# -----------------------------------------------
# student_view.py - ScholarTrack LMS
# Role:     Displays a student's grades, attendance
#           summary, and AI-generated feedback.
# Key classes used: StudentView, Student,
#                   DatabaseManager, GradeService
# OOP concepts demonstrated: Encapsulation (all DB
#   calls wrapped in methods), Inheritance (Student
#   extends User), Abstraction (GradeService hides
#   GPA calculation logic)
# -----------------------------------------------
# Student view — standard Tkinter only.
# Layout:
#   Header (create_header)
#   Info bar — dept, semester, GPA badge
#   ttk.Notebook with two tabs:
#     • Grades      — Treeview: Subject | Code | Score | Grade
#     • Attendance  — summary label + Treeview: Subject | Date | Status
#   AI Feedback panel — button + read-only Text widget
import os
import threading
import tkinter as tk
from tkinter import ttk

from gui.theme import THEME
from gui.components import create_header
from gui.dialogs import show_success, show_error
from models.student import Student
from storage.file_manager import FileManager
from services.grade_service import GradeService

BG   = THEME["COLOR_BG_DARK"]
CARD = THEME["COLOR_BG_CARD"]
FG   = "white"
ACC  = "#4a9eff"


class StudentView:
    def __init__(self, student, db):
        self.student       = student
        self.db            = db
        self.grade_service = GradeService(self.db)

        self.window = tk.Tk()
        self.window.title("ScholarTrack - Student Portal")
        self.window.configure(bg=BG)
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth()  // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (680 // 2)
        self.window.geometry(f"900x680+{x}+{y}")
        self.window.resizable(False, False)

        self._load_data()
        self._apply_styles()
        self._build_ui()

    # ── Data ──────────────────────────────────────────────────────

    def _load_data(self):
        # Fetch enrolled subjects, grades, GPA, and attendance from the database.
        # Load only subjects this student is enrolled in.
        self.enrolled_subjects = self.db.get_subjects_for_student(self.student.id)
        # Keep a set of enrolled subject codes for fast filtering (code = g[2] in grade rows).
        self._enrolled_codes   = {s[2] for s in self.enrolled_subjects}

        # All grade rows: (grade_id, subj_name, code, score, letter, sem)
        all_grades = self.db.get_student_grades(self.student.id)
        # Only keep rows whose subject code is in the enrolled set.
        self.student.grades = [g for g in all_grades if len(g) >= 3 and g[2] in self._enrolled_codes]

        scores = [g[3] for g in self.student.grades if g[3] is not None]
        self.student.gpa = self.grade_service.calculate_gpa(scores)

        # Attendance rows and summary are already student-scoped; no extra filter needed.
        self.attendance_rows    = self.db.get_student_attendance(self.student.id)
        self.attendance_summary = self.db.get_attendance_summary(self.student.id)

    # ── Shared style ──────────────────────────────────────────────

    def _apply_styles(self):
        # Configure a single dark ttk.Treeview style used in all tabs.
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("S.Treeview",
                    background=CARD, foreground=FG,
                    fieldbackground=CARD, rowheight=30,
                    font=THEME["FONT_BODY"])
        s.configure("S.Treeview.Heading",
                    background="#16213E", foreground=FG,
                    font=THEME["FONT_BUTTON"])
        s.map("S.Treeview.Heading", foreground=[("active", "#1e1e2e")])
        s.map("S.Treeview", background=[("selected", ACC)])
        s.configure("TNotebook",     background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=CARD, foreground=FG,
                    padding=[12, 5], font=THEME["FONT_BUTTON"])
        s.map("TNotebook.Tab", background=[("selected", ACC)],
              foreground=[("selected", FG)])

    # ── UI construction ───────────────────────────────────────────

    def _build_ui(self):
        # Assemble: header → info bar → notebook tabs → AI panel.
        create_header(self.window, self.student.name, "Student", self._logout)
        self._build_info_bar()
        self._build_notebook()

    def _build_info_bar(self):
        # Thin strip showing department, semester, and colour-coded GPA.
        bar = tk.Frame(self.window, bg=CARD, height=48)
        bar.pack(fill="x", padx=15, pady=(10, 0))
        bar.pack_propagate(False)

        tk.Label(bar,
                 text=f"{self.student.department}  |  Semester {self.student.semester}",
                 font=THEME["FONT_BODY"], bg=CARD, fg=THEME["COLOR_TEXT_MUTED"]
                 ).pack(side="left", padx=15, pady=12)

        gpa = self.student.gpa
        gpa_color = (THEME["COLOR_SUCCESS"] if gpa >= 3.0 else
                     THEME["COLOR_WARNING"]  if gpa >= 2.0 else
                     THEME["COLOR_DANGER"])

        if self.grade_service.is_at_risk(gpa):
            tk.Label(bar, text="⚠ At Risk",
                     font=THEME["FONT_SMALL"], bg=CARD,
                     fg=THEME["COLOR_DANGER"]).pack(side="right", padx=5)

        self.btn_ai = tk.Button(bar, text="Get AI Feedback",
                                command=self._get_ai_feedback,
                                font=THEME["FONT_BUTTON"],
                                bg=ACC, fg=FG, activebackground="#2563EB",
                                relief="flat", cursor="hand2", padx=10, pady=2)
        self.btn_ai.pack(side="right", padx=(10, 15), pady=8)

        tk.Label(bar, text=f"GPA: {gpa:.2f}",
                 font=("Segoe UI", 13, "bold"), bg=CARD,
                 fg=gpa_color).pack(side="right", padx=(5, 10))

    def _build_notebook(self):
        # Create the ttk.Notebook containing Grades and Attendance tabs.
        nb = ttk.Notebook(self.window)
        nb.pack(fill="both", expand=True, padx=15, pady=10)

        tab_grades     = tk.Frame(nb, bg=BG)
        tab_attendance = tk.Frame(nb, bg=BG)
        nb.add(tab_grades,     text="  My Grades  ")
        nb.add(tab_attendance, text="  Attendance  ")

        self._build_grades_tab(tab_grades)
        self._build_attendance_tab(tab_attendance)

    # ── Grades tab ────────────────────────────────────────────────

    def _build_grades_tab(self, parent):
        # Treeview listing Subject | Code | Score | Grade.
        cols = ("Subject", "Code", "Score", "Grade")
        self.grade_tree = ttk.Treeview(parent, columns=cols,
                                       show="headings", style="S.Treeview", height=12)
        for col, w in zip(cols, [300, 110, 90, 90]):
            self.grade_tree.heading(col, text=col)
            self.grade_tree.column(col, width=w,
                                   anchor="w" if col == "Subject" else "center")

        sb = ttk.Scrollbar(parent, orient="vertical", command=self.grade_tree.yview)
        self.grade_tree.configure(yscrollcommand=sb.set)
        self.grade_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._populate_grades()

    def _populate_grades(self):
        # Insert one row per enrolled-subject grade record into the grades Treeview.
        self.grade_tree.delete(*self.grade_tree.get_children())
        if not self.student.grades:
            self.grade_tree.insert("", "end", values=("No grades on record.", "", "", ""))
            return
        for g in self.student.grades:
            if g and len(g) >= 5:
                score_str = f"{g[3]:.1f}" if g[3] is not None else "N/A"
                self.grade_tree.insert("", "end", values=(g[1], g[2], score_str, g[4] or "-"))

    # ── Attendance tab ────────────────────────────────────────────

    def _build_attendance_tab(self, parent):
        # Summary label + Treeview listing Subject | Date | Status.
        # Summary bar
        s = self.attendance_summary
        summary_text = (f"Attendance: {s['present']}/{s['total']} classes  "
                        f"({s['percentage']}%)   "
                        f"  Present: {s['present']}   Absent: {s['absent']}   Late: {s['late']}")
        summary_color = (THEME["COLOR_SUCCESS"] if s["percentage"] >= 75 else
                         THEME["COLOR_WARNING"]  if s["percentage"] >= 50 else
                         THEME["COLOR_DANGER"])

        tk.Label(parent, text=summary_text,
                 font=("Segoe UI", 11, "bold"), bg=BG,
                 fg=summary_color).pack(anchor="w", padx=5, pady=(8, 5))

        # Attendance Treeview
        cols = ("Subject", "Date", "Status")
        tree = ttk.Treeview(parent, columns=cols,
                            show="headings", style="S.Treeview", height=14)
        for col, w in zip(cols, [320, 140, 120]):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w" if col == "Subject" else "center")

        sb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Populate rows
        if not self.attendance_rows:
            tree.insert("", "end", values=("No attendance records yet.", "", ""))
        else:
            for row in self.attendance_rows:
                # row: (id, subject_name, subject_code, date, status)
                tree.insert("", "end", iid=str(row[0]),
                            values=(row[1], row[3], row[4]))

    # ── AI Feedback panel ─────────────────────────────────────────

    def _get_ai_feedback(self):
        # Open a popup window and fetch AI feedback.
        self.btn_ai.configure(state="disabled")

        popup = tk.Toplevel(self.window)
        popup.title("AI Academic Advisor")
        popup.geometry("600x450")
        popup.configure(bg=BG)
        popup.transient(self.window)
        popup.grab_set()

        # Handle window close
        def on_close():
            self.btn_ai.configure(state="normal")
            popup.destroy()
        popup.protocol("WM_DELETE_WINDOW", on_close)

        lbl = tk.Label(popup, text="Connecting to Gemini AI… please wait.",
                       font=THEME["FONT_BODY"], bg=BG, fg=FG)
        lbl.pack(pady=10)

        txt_frame = tk.Frame(popup, bg=CARD)
        txt_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        ai_text = tk.Text(txt_frame, wrap="word",
                          font=("Segoe UI", 11),
                          bg="#1A1A2E", fg=FG,
                          insertbackground="white", relief="flat")
        sb = ttk.Scrollbar(txt_frame, orient="vertical", command=ai_text.yview)
        ai_text.configure(yscrollcommand=sb.set)
        ai_text.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        ai_text.insert("1.0", "Fetching...")
        ai_text.configure(state="disabled")

        def _set_text(content, is_err=False):
            lbl.configure(text="AI Feedback Complete" if not is_err else "Error")
            ai_text.configure(state="normal", fg=THEME["COLOR_DANGER"] if is_err else FG)
            ai_text.delete("1.0", "end")
            ai_text.insert("1.0", content)
            ai_text.configure(state="disabled")

        def worker():
            try:
                from google import genai
                api_key = os.environ.get("GEMINI_API_KEY", "")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not set in .env file.")

                client = genai.Client(api_key=api_key)
                grade_lines = "\n".join(
                    f"- {g[1]} ({g[2]}): {g[3]}/100 — {g[4]}"
                    for g in self.student.grades
                )
                gpa = self.student.gpa
                if   gpa >= 3.5: ctx = "excellent standing"
                elif gpa >= 3.0: ctx = "good standing, room for improvement"
                elif gpa >= 2.0: ctx = "needs improvement, at risk of probation"
                else:            ctx = "critical — immediate intervention needed"

                prompt = (
                    f"You are an academic advisor. Give structured plain-text (no markdown) "
                    f"feedback for this student.\n\n"
                    f"Name: {self.student.name} | Dept: {self.student.department} | "
                    f"Semester: {self.student.semester} | GPA: {gpa:.2f} ({ctx})\n\n"
                    f"Grades:\n{grade_lines}\n\n"
                    f"Sections to include:\n"
                    f"PERFORMANCE SUMMARY\n"
                    f"SUBJECT-BY-SUBJECT BREAKDOWN\n"
                    f"RECOMMENDED WEEKLY STUDY PLAN\n"
                    f"KEY TAKEAWAY"
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt)
                self.window.after(0, lambda t=response.text: _set_text(t))

            except Exception as e:
                msg = f"Error: {type(e).__name__}: {e}\n\nCheck GEMINI_API_KEY in .env"
                self.window.after(0, lambda m=msg: _set_text(m, is_err=True))

        threading.Thread(target=worker, daemon=True).start()

    # ── Navigation ────────────────────────────────────────────────

    def _logout(self):
        # Destroy window and return to login screen.
        self.window.destroy()
        from gui.login_screen import LoginScreen
        LoginScreen(self.db).render()

    def render(self):
        # Start the Tkinter event loop.
        self.window.mainloop()
