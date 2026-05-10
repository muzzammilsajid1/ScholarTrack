# Provides an interface for teachers to manage grades and submit class attendance
# Encapsulation: isolates UI layout and teacher-specific event handlers
# Abstraction: uses GradeService to handle grade validations without writing custom checks
import tkinter as tk
from tkinter import ttk
from datetime import date as dt_date

from gui.theme import THEME
from gui.components import create_header
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
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth()  // 2) - (1050 // 2)
        y = (self.window.winfo_screenheight() // 2) - (680  // 2)
        self.window.geometry(f"1050x680+{x}+{y}")
        self.window.resizable(False, False)

        self._apply_styles()
        self._build_ui()

    # ── Shared style ──────────────────────────────────────────────

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("T.Treeview",
                    background=CARD, foreground=FG,
                    fieldbackground=CARD, rowheight=30,
                    font=THEME["FONT_BODY"])
        s.configure("T.Treeview.Heading",
                    background="#16213E", foreground=FG,
                    font=THEME["FONT_BUTTON"])
        s.map("T.Treeview.Heading", foreground=[("active", "#1e1e2e")])
        s.map("T.Treeview", background=[("selected", ACC)])
        s.configure("TNotebook",     background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=CARD, foreground=FG,
                    padding=[12, 5], font=THEME["FONT_BUTTON"])
        s.map("TNotebook.Tab", background=[("selected", ACC)],
              foreground=[("selected", FG)])

    # ── UI construction ───────────────────────────────────────────

    def _build_ui(self):
        create_header(self.window, self.teacher.name, "Teacher", self._logout)

        # If the admin hasn't assigned any subjects yet, show a helpful message
        # instead of empty, confusing tabs.
        if not self.all_subjects:
            notice = tk.Frame(self.window, bg=BG)
            notice.pack(expand=True)
            tk.Label(notice, text="⚠",
                     font=("Segoe UI", 48), bg=BG,
                     fg=THEME["COLOR_WARNING"]).pack(pady=(0, 10))
            tk.Label(notice,
                     text="No subjects assigned.",
                     font=THEME["FONT_TITLE"], bg=BG, fg=FG).pack()
            tk.Label(notice,
                     text="Contact your administrator to be assigned to a subject.",
                     font=THEME["FONT_BODY"], bg=BG,
                     fg=THEME["COLOR_TEXT_MUTED"]).pack(pady=(6, 0))
            return

        nb = ttk.Notebook(self.window)
        nb.pack(fill="both", expand=True, padx=15, pady=10)

        tab_grades     = tk.Frame(nb, bg=BG)
        tab_attendance = tk.Frame(nb, bg=BG)
        nb.add(tab_grades,     text="  Grades  ")
        nb.add(tab_attendance, text="  Mark Attendance  ")

        self._build_grades_tab(tab_grades)
        self._build_attendance_tab(tab_attendance)

    # ── Grades tab ────────────────────────────────────────────────

    def _build_grades_tab(self, parent):
        self._build_student_panel(parent)
        self._build_grade_panel(parent)

    def _build_student_panel(self, parent):
        left = tk.Frame(parent, bg=CARD, width=340)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(left, text="Students",
                 font=THEME["FONT_HEADING"], bg=CARD, fg=FG
                 ).pack(anchor="w", padx=10, pady=(10, 4))

        # Search box
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_students)
        tk.Entry(left, textvariable=self.search_var,
                 font=THEME["FONT_BODY"],
                 bg="#3A3A5E", fg=FG, insertbackground="white", relief="flat"
                 ).pack(fill="x", padx=10, pady=(0, 8), ipady=6)

        # Student Treeview
        self.student_tree = ttk.Treeview(left, columns=("Name", "Dept"),
                                         show="headings", style="T.Treeview")
        self.student_tree.heading("Name", text="Name")
        self.student_tree.heading("Dept", text="Department")
        self.student_tree.column("Name", width=140)
        self.student_tree.column("Dept", width=170)

        sb = ttk.Scrollbar(left, orient="vertical", command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=sb.set)
        self.student_tree.pack(side="left", fill="both", expand=True,
                               padx=(10, 0), pady=(0, 10))
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
        self.placeholder = tk.Label(self.right,
                                    text="← Select a student to edit grades",
                                    font=THEME["FONT_BODY"],
                                    bg=BG, fg=THEME["COLOR_TEXT_MUTED"])
        self.placeholder.pack(expand=True)

        # Grade Treeview (packed when student selected)
        cols = ("Subject", "Code", "Score", "Grade")
        self.grade_tree = ttk.Treeview(self.right, columns=cols,
                                       show="headings", style="T.Treeview", height=12)
        for col, w in zip(cols, [260, 90, 80, 80]):
            self.grade_tree.heading(col, text=col)
            self.grade_tree.column(col, width=w,
                                   anchor="w" if col == "Subject" else "center")

        self._grade_sb = ttk.Scrollbar(self.right, orient="vertical",
                                       command=self.grade_tree.yview)
        self.grade_tree.configure(yscrollcommand=self._grade_sb.set)

        # Edit form
        self._edit_frame = tk.Frame(self.right, bg=CARD)
        tk.Label(self._edit_frame, text="New Score (0–100):",
                 font=THEME["FONT_BODY"], bg=CARD, fg=FG
                 ).pack(side="left", padx=(10, 5), pady=8)
        self.score_var = tk.StringVar()
        tk.Entry(self._edit_frame, textvariable=self.score_var, width=8,
                 font=THEME["FONT_BODY"],
                 bg="#3A3A5E", fg=FG, insertbackground="white", relief="flat"
                 ).pack(side="left", ipady=4)
        tk.Button(self._edit_frame, text="Save Grade",
                  command=self._save_selected_grade,
                  font=THEME["FONT_BUTTON"],
                  bg=THEME["COLOR_SUCCESS"], fg=FG,
                  activebackground="#16A34A", relief="flat", cursor="hand2", padx=12
                  ).pack(side="left", padx=10, pady=8)
        self.status_lbl = tk.Label(self._edit_frame, text="",
                                   font=THEME["FONT_SMALL"], bg=CARD, fg=FG)
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
                self.grade_tree.insert("", "end", iid=str(g[0]),
                                       values=(g[1], g[2], score_str, g[4] or "-"))
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

    # ── Attendance tab ────────────────────────────────────────────

    def _build_attendance_tab(self, parent):
        # ── Controls row ──
        ctrl = tk.Frame(parent, bg=CARD, height=54)
        ctrl.pack(fill="x", pady=(0, 8))
        ctrl.pack_propagate(False)

        tk.Label(ctrl, text="Subject:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(12, 4), pady=15)

        # Build a mapping: display string → subject_id for reliable lookup.
        # This avoids fragile string parsing when the combobox fires.
        self.subject_map = {
            f"{s[1]} ({s[2]})": s[0] for s in self.all_subjects
        }

        subject_names = list(self.subject_map.keys())
        self.att_subject_var = tk.StringVar()
        self.att_subject_cb  = ttk.Combobox(ctrl, textvariable=self.att_subject_var,
                                             values=subject_names, state="readonly",
                                             font=THEME["FONT_BODY"], width=28)
        if subject_names:
            self.att_subject_cb.current(0)
        self.att_subject_cb.pack(side="left", padx=(0, 16), pady=15)
        # Reload student list every time the teacher picks a different subject.
        self.att_subject_cb.bind("<<ComboboxSelected>>",
                                 self._on_subject_selected)

        tk.Label(ctrl, text="Date:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(0, 4))
        self.att_date_var = tk.StringVar(value=str(dt_date.today()))
        tk.Entry(ctrl, textvariable=self.att_date_var, width=12,
                 font=THEME["FONT_BODY"],
                 bg="#3A3A5E", fg=FG, insertbackground="white", relief="flat"
                 ).pack(side="left", ipady=4, padx=(0, 16))

        tk.Button(ctrl, text="Submit Attendance",
                  command=self._submit_attendance,
                  font=THEME["FONT_BUTTON"],
                  bg=THEME["COLOR_SUCCESS"], fg=FG,
                  activebackground="#16A34A", relief="flat",
                  cursor="hand2", padx=12
                  ).pack(side="left", padx=4)

        self.att_status_lbl = tk.Label(ctrl, text="",
                                       font=THEME["FONT_SMALL"], bg=CARD, fg=FG)
        self.att_status_lbl.pack(side="left", padx=8)

        # ── Scrollable student list ──
        list_frame = tk.Frame(parent, bg=BG)
        list_frame.pack(fill="both", expand=True)

        self._att_canvas = tk.Canvas(list_frame, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self._att_canvas.yview)
        self._att_scroll_frame = tk.Frame(self._att_canvas, bg=BG)
        self._att_scroll_frame.bind(
            "<Configure>",
            lambda e: self._att_canvas.configure(
                scrollregion=self._att_canvas.bbox("all")))
        self._att_canvas_window = self._att_canvas.create_window(
            (0, 0), window=self._att_scroll_frame, anchor="nw")
        # Keep inner frame width in sync with canvas so rows fill the full width.
        self._att_canvas.bind(
            "<Configure>",
            lambda e: self._att_canvas.itemconfig(
                self._att_canvas_window, width=e.width))
        self._att_canvas.configure(yscrollcommand=sb.set)
        self._att_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        # Enable mouse-wheel scrolling over the canvas.
        self._att_canvas.bind(
            "<MouseWheel>",
            lambda e: self._att_canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units"))

        # Column headers
        hdr = tk.Frame(self._att_scroll_frame, bg="#16213E", height=36)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        for txt, w in [("Student Name", 300), ("Present?", 120)]:
            tk.Label(hdr, text=txt, font=THEME["FONT_BUTTON"],
                     bg="#16213E", fg=FG, width=w // 10
                     ).pack(side="left", padx=10)

        # Rows frame — rebuilt by load_attendance_students().
        self._att_rows_frame = tk.Frame(self._att_scroll_frame, bg=BG)
        self._att_rows_frame.pack(fill="both", expand=True)

        # Dict of student_id → BooleanVar (True = Present, False = Absent).
        self.attendance_vars = {}

        # Trigger initial load so students appear immediately on tab open.
        if subject_names:
            self.load_attendance_students()

    def _on_subject_selected(self, event=None):
        # Handler for <<ComboboxSelected>> — delegates to load_attendance_students.
        self.load_attendance_students()

    def load_attendance_students(self):
        # Fetch enrolled students for the selected subject and render Checkbutton rows.
        # Called on <<ComboboxSelected>> and once on tab build so the list
        # appears immediately. Each student gets a BooleanVar defaulting to
        # True (Present). Teacher unchecks absent students before submitting.
        # Clear previous rows and stored vars.
        for widget in self._att_rows_frame.winfo_children():
            widget.destroy()
        self.attendance_vars = {}

        # Look up subject_id from the pre-built subject_map (avoids string parsing).
        selected = self.att_subject_var.get()
        subject_id = self.subject_map.get(selected)

        if subject_id is None:
            tk.Label(self._att_rows_frame,
                     text="Select a subject above to load students.",
                     font=THEME["FONT_BODY"], bg=BG,
                     fg=THEME["COLOR_TEXT_MUTED"]).pack(pady=20)
            return

        enrolled = self.db.get_students_in_subject(subject_id)

        if not enrolled:
            tk.Label(self._att_rows_frame,
                     text="No students enrolled in this subject.",
                     font=THEME["FONT_BODY"], bg=BG,
                     fg=THEME["COLOR_TEXT_MUTED"]).pack(pady=20)
            return

        # Render one row per enrolled student.
        for idx, student in enumerate(enrolled):
            s_id, name = student[0], student[1]
            row_bg = CARD if idx % 2 == 0 else "#252535"

            row = tk.Frame(self._att_rows_frame, bg=row_bg, height=44)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            tk.Label(row, text=name, font=THEME["FONT_BODY"],
                     bg=row_bg, fg=FG, anchor="w", width=34
                     ).pack(side="left", padx=14, pady=10)

            # BooleanVar: True = Present (default), False = Absent.
            var = tk.BooleanVar(value=True)
            self.attendance_vars[s_id] = var

            tk.Checkbutton(row, text="Present", variable=var,
                           font=THEME["FONT_BODY"],
                           bg=row_bg, fg=FG,
                           activebackground=row_bg, activeforeground=FG,
                           selectcolor=CARD,
                           cursor="hand2"
                           ).pack(side="left", padx=14)

    def _get_selected_subject_id(self):
        # Return the subject_id for the currently selected combobox item via subject_map.
        return self.subject_map.get(self.att_subject_var.get())

    def _submit_attendance(self):
        # Save attendance for every rendered student (Present if checked, Absent if not).
        # Uses mark_attendance (INSERT OR REPLACE) so re-submitting the same
        # student/subject/date updates the existing record instead of duplicating it.
        subject_id = self._get_selected_subject_id()
        if subject_id is None:
            self._show_att_status("Select a subject first.", err=True); return

        date_str = self.att_date_var.get().strip()
        if not date_str:
            self._show_att_status("Enter a date (YYYY-MM-DD).", err=True); return

        from datetime import datetime as _dt
        try:
            _dt.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self._show_att_status("Date must be YYYY-MM-DD format.", err=True); return

        if not self.attendance_vars:
            self._show_att_status("No students loaded — select a subject first.", err=True)
            return

        # Loop every student: checked checkbox → Present, unchecked → Absent.
        for student_id, var in self.attendance_vars.items():
            status = "Present" if var.get() else "Absent"
            self.db.mark_attendance(student_id, subject_id, date_str, status)

        count = len(self.attendance_vars)


        from tkinter import messagebox
        messagebox.showinfo("Done", f"Attendance saved for {count} students.\nDate: {date_str}")
        self._show_att_status(f"Saved for {count} student(s).", err=False)

    def _show_att_status(self, msg, err=False):
        try:
            if not self.att_status_lbl.winfo_exists():
                return
            self.att_status_lbl.configure(
                text=msg, fg=THEME["COLOR_DANGER"] if err else THEME["COLOR_SUCCESS"])
            # Guard the after-callback with winfo_exists so it won't crash on logout.
            def _clear():
                try:
                    if self.att_status_lbl.winfo_exists():
                        self.att_status_lbl.configure(text="")
                except Exception:
                    pass
            self.window.after(3500, _clear)
        except Exception:
            pass

    # ── Navigation ────────────────────────────────────────────────

    def _logout(self):
        self.window.destroy()
        from gui.login_screen import LoginScreen
        LoginScreen(self.db).render()

    def render(self):
        self.window.mainloop()
