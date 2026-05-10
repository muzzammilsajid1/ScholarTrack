# Displays a student's personal grades, attendance summary, and AI-generated feedback
# Encapsulation: bundles UI construction and event handling for the student dashboard into one class
# Abstraction: utilizes GradeService to calculate GPA without exposing the underlying math
import os
import threading
import tkinter as tk
from tkinter import ttk

from gui.theme import THEME
from gui.components import create_header
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
        self.window.geometry("900x680")
        self.window.resizable(False, False)

        self._load_data()
        self._apply_styles()
        self._build_ui()

    # ── Data ──────────────────────────────────────────────────────

    def _load_data(self):
        self.enrolled_subjects = self.db.get_subjects_for_student(self.student.student_id)
        # Cache enrolled subject codes to quickly filter global grade records
        self._enrolled_codes   = {s[2] for s in self.enrolled_subjects}

        all_grades = self.db.get_student_grades(self.student.student_id)
        # Prevent display of grades for subjects the student is no longer enrolled in
        self.student.grades = [g for g in all_grades if len(g) >= 3 and g[2] in self._enrolled_codes]

        scores = [g[3] for g in self.student.grades if g[3] is not None]
        self.student.gpa = self.grade_service.calculate_gpa(scores)

    # ── Shared style ──────────────────────────────────────────────

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("S.Treeview", background=CARD, foreground=FG, fieldbackground=CARD, rowheight=30, font=THEME["FONT_BODY"])
        s.configure("S.Treeview.Heading", background="#16213E", foreground=FG, font=THEME["FONT_BUTTON"])
        s.map("S.Treeview.Heading", foreground=[("active", "#1e1e2e")])
        s.map("S.Treeview", background=[("selected", ACC)])
        s.configure("TNotebook",     background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=CARD, foreground=FG, padding=[12, 5], font=THEME["FONT_BUTTON"])
        s.map("TNotebook.Tab", background=[("selected", ACC)], foreground=[("selected", FG)])

    # ── UI construction ───────────────────────────────────────────

    def _build_ui(self):
        create_header(self.window, self.student.name, "Student", self._logout)
        self._build_info_bar()
        self._build_notebook()

    def _build_info_bar(self):
        bar = tk.Frame(self.window, bg=CARD, height=48)
        bar.pack(fill="x", padx=15, pady=(10, 0))
        bar.pack_propagate(False)

        tk.Label(bar, text=f"{self.student.department}  |  Semester {self.student.semester}", font=THEME["FONT_BODY"], bg=CARD, fg=THEME["COLOR_TEXT_MUTED"]).pack(side="left", padx=15, pady=12)

        gpa = self.student.gpa
        gpa_color = (THEME["COLOR_SUCCESS"] if gpa >= 3.0 else THEME["COLOR_WARNING"]  if gpa >= 2.0 else THEME["COLOR_DANGER"])

        if self.grade_service.is_at_risk(gpa):
            tk.Label(bar, text="⚠ At Risk", font=THEME["FONT_SMALL"], bg=CARD, fg=THEME["COLOR_DANGER"]).pack(side="right", padx=5)

        self.btn_ai = tk.Button(bar, text="Get AI Feedback", command=self._get_ai_feedback, font=THEME["FONT_BUTTON"], bg=ACC, fg=FG, activebackground="#2563EB", relief="flat", cursor="hand2", padx=10, pady=2)
        self.btn_ai.pack(side="right", padx=(10, 15), pady=8)

        tk.Label(bar, text=f"GPA: {gpa:.2f}", font=("Segoe UI", 13, "bold"), bg=CARD, fg=gpa_color).pack(side="right", padx=(5, 10))

    def _build_notebook(self):
        nb = ttk.Notebook(self.window)
        nb.pack(fill="both", expand=True, padx=15, pady=10)

        tab_grades     = tk.Frame(nb, bg=BG)
        nb.add(tab_grades,     text="  My Grades  ")

        self._build_grades_tab(tab_grades)

    # ── Grades tab ────────────────────────────────────────────────

    def _build_grades_tab(self, parent):
        cols = ("Subject", "Code", "Score", "Grade")
        self.grade_tree = ttk.Treeview(parent, columns=cols, show="headings", style="S.Treeview", height=12)
        for col, w in zip(cols, [300, 110, 90, 90]):
            self.grade_tree.heading(col, text=col)
            self.grade_tree.column(col, width=w, anchor="w" if col == "Subject" else "center")

        sb = ttk.Scrollbar(parent, orient="vertical", command=self.grade_tree.yview)
        self.grade_tree.configure(yscrollcommand=sb.set)
        self.grade_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._populate_grades()

    def _populate_grades(self):
        self.grade_tree.delete(*self.grade_tree.get_children())
        if not self.student.grades:
            self.grade_tree.insert("", "end", values=("No grades on record.", "", "", ""))
            return
        for g in self.student.grades:
            if g and len(g) >= 5:
                score_str = f"{g[3]:.1f}" if g[3] is not None else "N/A"
                self.grade_tree.insert("", "end", values=(g[1], g[2], score_str, g[4] or "-"))



    # ── AI Feedback panel ─────────────────────────────────────────

    def _get_ai_feedback(self):
        popup = tk.Toplevel(self.window)
        popup.title("AI Academic Advisor")
        popup.geometry("600x450")
        popup.configure(bg=BG)

        lbl = tk.Label(popup, text="Connecting to Gemini AI… please wait.", font=THEME["FONT_BODY"], bg=BG, fg=FG)
        lbl.pack(pady=10)

        txt_frame = tk.Frame(popup, bg=CARD)
        txt_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        ai_text = tk.Text(txt_frame, wrap="word", font=("Segoe UI", 11), bg="#1A1A2E", fg=FG, insertbackground="white", relief="flat")
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
                response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                self.window.after(0, lambda t=response.text: _set_text(t))

            except Exception as e:
                msg = f"Error: {type(e).__name__}: {e}\n\nCheck GEMINI_API_KEY in .env"
                self.window.after(0, lambda m=msg: _set_text(m, is_err=True))

        threading.Thread(target=worker).start()

    # ── Navigation ────────────────────────────────────────────────

    def _logout(self):
        self.window.destroy()
        from gui.login_screen import LoginScreen
        LoginScreen(self.db).render()

    def render(self):
        self.window.mainloop()
