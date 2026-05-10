# Provides an interface for teachers to manage grades and submit class attendance
# Encapsulation: isolates UI layout and teacher-specific event handlers
# Abstraction: uses GradeService to handle grade validations without writing custom checks
import tkinter as tk
from tkinter import ttk

from gui.theme import THEME
from gui.components import create_header
from gui.dialogs import show_success
from services.grade_service import GradeService

BG   = THEME["COLOR_BG_DARK"]
CARD = THEME["COLOR_BG_CARD"]
FG   = "white"
ACC  = "#4a9eff"


class TeacherView:
    def __init__(self, teacher, db):
        self.teacher       = teacher
        self.db            = db
        self.grade_service = GradeService(self.db)

        # Shared data — scoped to this teacher's assigned subjects and enrolled students.
        # Falls back to all subjects/students if no assignments have been made yet.
        self.all_subjects        = self.db.get_teacher_subjects(self.teacher.id)
        self.all_students        = self.db.get_students_for_teacher(self.teacher.id)
        self.selected_student_id = None
        self.selected_grades     = []

        self.window = tk.Tk()
        self.window.title("ScholarTrack - Teacher Portal")
        self.window.configure(bg=BG)
        self.window.geometry("1050x680")
        self.window.resizable(False, False)

        self._apply_styles()
        self._build_ui()

    # ── Shared style ──────────────────────────────────────────────

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("T.Treeview", background=CARD, foreground=FG, fieldbackground=CARD, rowheight=30, font=THEME["FONT_BODY"])
        s.configure("T.Treeview.Heading", background="#16213E", foreground=FG, font=THEME["FONT_BUTTON"])
        s.map("T.Treeview.Heading", foreground=[("active", "#1e1e2e")])
        s.map("T.Treeview", background=[("selected", ACC)])
        s.configure("TNotebook",     background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=CARD, foreground=FG, padding=[12, 5], font=THEME["FONT_BUTTON"])
        s.map("TNotebook.Tab", background=[("selected", ACC)], foreground=[("selected", FG)])

    # ── UI construction ───────────────────────────────────────────

    def _build_ui(self):
        create_header(self.window, self.teacher.name, "Teacher", self._logout)

        # If the admin hasn't assigned any subjects yet, show a helpful message
        # instead of empty, confusing tabs.
        if not self.all_subjects:
            notice = tk.Frame(self.window, bg=BG)
            notice.pack(expand=True)
            tk.Label(notice, text="⚠", font=("Segoe UI", 48), bg=BG, fg=THEME["COLOR_WARNING"]).pack(pady=(0, 10))
            tk.Label(notice, text="No subjects assigned.", font=THEME["FONT_TITLE"], bg=BG, fg=FG).pack()
            tk.Label(notice, text="Contact your administrator to be assigned to a subject.", font=THEME["FONT_BODY"], bg=BG, fg=THEME["COLOR_TEXT_MUTED"]).pack(pady=(6, 0))
            return

        nb = ttk.Notebook(self.window)
        nb.pack(fill="both", expand=True, padx=15, pady=10)

        tab_grades     = tk.Frame(nb, bg=BG)
        nb.add(tab_grades,     text="  Grades  ")

        self._build_grades_tab(tab_grades)

    # ── Grades tab ────────────────────────────────────────────────

    def _build_grades_tab(self, parent):
        self._build_student_panel(parent)
        self._build_grade_panel(parent)

    def _build_student_panel(self, parent):
        left = tk.Frame(parent, bg=CARD, width=340)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(left, text="Students", font=THEME["FONT_HEADING"], bg=CARD, fg=FG).pack(anchor="w", padx=10, pady=(10, 4))

        # Search box
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_students)
        tk.Entry(left, textvariable=self.search_var, font=THEME["FONT_BODY"], bg="#3A3A5E", fg=FG, insertbackground="white", relief="flat").pack(fill="x", padx=10, pady=(0, 8), ipady=6)

        # Student Treeview
        self.student_tree = ttk.Treeview(left, columns=("Name", "Dept"), show="headings", style="T.Treeview")
        self.student_tree.heading("Name", text="Name")
        self.student_tree.heading("Dept", text="Department")
        self.student_tree.column("Name", width=140)
        self.student_tree.column("Dept", width=170)

        sb = ttk.Scrollbar(left, orient="vertical", command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=sb.set)
        self.student_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        sb.pack(side="right", fill="y", pady=(0, 10), padx=(0, 5))

        self.student_tree.bind("<<TreeviewSelect>>", self._on_student_select)
        self._populate_student_tree(self.all_students)

    def _populate_student_tree(self, students):
        self.student_tree.delete(*self.student_tree.get_children())
        for s in students:
            self.student_tree.insert("", "end", iid=str(s[0]), values=(s[1], s[4]))

    def _filter_students(self, *_):
        # Filter student list by the search entry text.
        q = self.search_var.get().lower()
        self._populate_student_tree(
            [s for s in self.all_students if q in s[1].lower()])

    def _on_student_select(self, _event):
        # Load the selected student's grades into the right panel.
        sel = self.student_tree.selection()
        if not sel:
            return
        self.selected_student_id = int(sel[0])
        self.selected_grades = self.db.get_student_grades(self.selected_student_id, self.teacher.id)
        self._refresh_grade_panel()

    def _build_grade_panel(self, parent):
        self.right = tk.Frame(parent, bg=BG)
        self.right.pack(side="left", fill="both", expand=True)

        # Placeholder text until a student is chosen
        self.placeholder = tk.Label(self.right, text="← Select a student to edit grades", font=THEME["FONT_BODY"], bg=BG, fg=THEME["COLOR_TEXT_MUTED"])
        self.placeholder.pack(expand=True)

        # Grade Treeview (packed when student selected)
        cols = ("Subject", "Code", "Score", "Grade")
        self.grade_tree = ttk.Treeview(self.right, columns=cols, show="headings", style="T.Treeview", height=12)
        for col, w in zip(cols, [260, 90, 80, 80]):
            self.grade_tree.heading(col, text=col)
            self.grade_tree.column(col, width=w, anchor="w" if col == "Subject" else "center")

        self._grade_sb = ttk.Scrollbar(self.right, orient="vertical", command=self.grade_tree.yview)
        self.grade_tree.configure(yscrollcommand=self._grade_sb.set)

        # Edit form
        self._edit_frame = tk.Frame(self.right, bg=CARD)
        tk.Label(self._edit_frame, text="New Score (0–100):", font=THEME["FONT_BODY"], bg=CARD, fg=FG).pack(side="left", padx=(10, 5), pady=8)
        self.score_var = tk.StringVar()
        tk.Entry(self._edit_frame, textvariable=self.score_var, width=8, font=THEME["FONT_BODY"], bg="#3A3A5E", fg=FG, insertbackground="white", relief="flat").pack(side="left", ipady=4)
        tk.Button(self._edit_frame, text="Save Grade", command=self._save_selected_grade, font=THEME["FONT_BUTTON"], bg=THEME["COLOR_SUCCESS"], fg=FG, activebackground="#16A34A", relief="flat", cursor="hand2", padx=12).pack(side="left", padx=10, pady=8)
        self.status_lbl = tk.Label(self._edit_frame, text="", font=THEME["FONT_SMALL"], bg=CARD, fg=FG)
        self.status_lbl.pack(side="left", padx=5)

    def _refresh_grade_panel(self):
        # Reveal and repopulate the grade Treeview for the chosen student.
        self.placeholder.pack_forget()
        self.grade_tree.pack(fill="both", expand=True, pady=(0, 5))
        self._grade_sb.pack(side="right", fill="y")
        self._edit_frame.pack(fill="x")

        self.grade_tree.delete(*self.grade_tree.get_children())
        for g in self.selected_grades:
            if g and len(g) >= 5:
                score_str = f"{g[3]:.1f}" if g[3] is not None else "N/A"
                self.grade_tree.insert("", "end", iid=str(g[0]), values=(g[1], g[2], score_str, g[4] or "-"))
        self.status_lbl.configure(text="")

    def _save_selected_grade(self):
        # Validate score entry and persist the update for the selected grade row.
        sel = self.grade_tree.selection()
        if not sel:
            self._show_status("Select a grade row first.", err=True); return
        raw = self.score_var.get().strip()
        try:
            score = float(raw)
            if not (0 <= score <= 100):
                raise ValueError
        except ValueError:
            self._show_status("Enter a number between 0 and 100.", err=True); return

        grade_id = int(sel[0])
        letter   = self.grade_service.letter_grade(score)
        self.db.update_grade(grade_id, score, letter)

        self.selected_grades = self.db.get_student_grades(self.selected_student_id, self.teacher.id)
        self._refresh_grade_panel()
        self._show_status("Saved successfully.", err=False)

    def _show_status(self, msg, err=False):
        self.status_lbl.configure(
            text=msg, fg=THEME["COLOR_DANGER"] if err else THEME["COLOR_SUCCESS"])
        self.window.after(3000, lambda: self.status_lbl.configure(text=""))



    # ── Navigation ────────────────────────────────────────────────

    def _logout(self):
        self.window.destroy()
        from gui.login_screen import LoginScreen
        LoginScreen(self.db).render()

    def render(self):
        self.window.mainloop()
