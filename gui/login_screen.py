# Displays the authentication form and routes users to their specific dashboards
# Encapsulation: isolates UI layout and authentication logic within the LoginScreen class
# Polymorphism: creates different view objects (AdminView, TeacherView, StudentView) based on user role
import tkinter as tk

from gui.theme import THEME

from models.student import Student
from models.teacher import Teacher
from models.admin import Admin
from gui.teacher_view import TeacherView
from gui.student_view import StudentView
from gui.admin_view import AdminView
from gui.dialogs import show_error

BG_DARK = THEME["COLOR_BG_DARK"]
BG_CARD = THEME["COLOR_BG_CARD"]
FG      = "white"
ACCENT  = "#4a9eff"


class LoginScreen:
    def __init__(self, db):
        self.db = db

        self.window = tk.Tk()
        self.window.title("ScholarTrack - Login")

        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth()  // 2) - (420 // 2)
        y = (self.window.winfo_screenheight() // 2) - (580 // 2)
        self.window.geometry(f"420x580+{x}+{y}")
        self.window.resizable(False, False)
        self.window.configure(bg=BG_DARK)

        try:
            self.window.iconbitmap("icon.ico")
        except Exception:
            pass

        self.window.bind("<Return>", lambda e: self.attempt_login())

        self.build_ui()

    def build_ui(self):
        # ── Outer card frame ──────────────────────────────────────
        main_frame = tk.Frame(self.window, bg=BG_CARD)
        main_frame.pack(
            pady=THEME["PADDING_LARGE"],
            padx=THEME["PADDING_LARGE"],
            fill="both",
            expand=True,
        )

        # Center wrapper to keep everything perfectly centered vertically inside the card
        center_frame = tk.Frame(main_frame, bg=BG_CARD)
        center_frame.pack(expand=True)

        tk.Label(center_frame, text="🎓", font=("Segoe UI", 48), bg=BG_CARD, fg=FG).pack(pady=(0, 20))

        tk.Label(center_frame, text="ScholarTrack", font=THEME["FONT_TITLE"], bg=BG_CARD, fg=FG).pack()

        tk.Label(
            center_frame,
            text="Academic Performance System",
            font=THEME["FONT_SMALL"],
            bg=BG_CARD,
            fg=THEME["COLOR_TEXT_MUTED"],
        ).pack(pady=(0, 20))

        tk.Frame(center_frame, height=1, bg="#3A3A4E").pack(fill="x", padx=20, pady=(0, 20))

        self.entry_username = tk.Entry(
            center_frame,
            font=THEME["FONT_BODY"],
            width=28,
            bg="#3A3A5E",
            fg=FG,
            insertbackground="white",
            relief="flat",
        )
        self._add_placeholder(self.entry_username, "Username")
        self.entry_username.pack(pady=(0, 12), ipady=8)

        self.entry_password = tk.Entry(
            center_frame,
            font=THEME["FONT_BODY"],
            width=28,
            show="*",
            bg="#3A3A5E",
            fg=FG,
            insertbackground="white",
            relief="flat",
        )
        self._add_placeholder(self.entry_password, "Password", is_password=True)
        self.entry_password.pack(pady=(0, 8), ipady=8)

        self.err_label = tk.Label(
            center_frame,
            text="",
            font=THEME["FONT_SMALL"],
            bg=BG_CARD,
            fg=THEME["COLOR_DANGER"],
        )
        self.err_label.pack(pady=(0, 16))

        btn_login = tk.Button(
            center_frame,
            text="Login",
            command=self.attempt_login,
            width=28,
            height=2,
            bg=ACCENT,
            fg=FG,
            activebackground="#2563EB",
            activeforeground=FG,
            font=THEME["FONT_BUTTON"],
            relief="flat",
            cursor="hand2",
        )
        btn_login.pack(pady=(0, 20))

        tk.Label(
            center_frame,
            text="GIKI - CS112 Project",
            font=THEME["FONT_SMALL"],
            bg=BG_CARD,
            fg=THEME["COLOR_TEXT_MUTED"],
        ).pack()

    def _add_placeholder(self, entry, placeholder, is_password=False):
        # Provide inline field hints without requiring separate label widgets
        # Insert the hint text and dim it so it reads as a placeholder.
        entry.insert(0, placeholder)
        entry.configure(fg=THEME["COLOR_TEXT_MUTED"])

        # Clear the hint and restore normal colour/show when the user clicks in.
        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.configure(fg=FG)
                if is_password:
                    entry.configure(show="*")

        # Re-insert the hint if the user leaves the field empty.
        def on_focus_out(e):
            if entry.get() == "":
                entry.configure(fg=THEME["COLOR_TEXT_MUTED"], show="")
                entry.insert(0, placeholder)

        entry.bind("<FocusIn>",  on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def attempt_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        # Prevent placeholder text from being submitted as actual credentials
        if username == "Username":
            username = ""
        if password == "Password":
            password = ""

        if not username or not password:
            self.err_label.configure(text="Please enter your username and password.")
            return

        user_row = self.db.authenticate_user(username, password)

        if user_row:
            self.err_label.configure(text="")
            role = user_row[4].lower()
            self.launch_dashboard(user_row, role)
        else:
            self.err_label.configure(text="Invalid username or password")

    def launch_dashboard(self, user_row, role):
        user_id  = user_row[0]
        name     = user_row[1]
        username = user_row[2]

        # ── Build the domain model for this role ──────────────
        model = None
        if role == "student":
            # Map the authenticated username to a specific student record to build their complete model
            for s in self.db.get_all_students():
                # s = (student_id, name, username, semester, department)
                if s[2] == username:
                    model = Student(user_id, s[0], name, username, s[3], s[4])
                    break
        elif role == "teacher":
            model = Teacher(user_id, name, username, "General")
            # Populate teacher.subjects in the single canonical dict format
            for subj_id, subj_name, subj_code in self.db.get_teacher_subjects(user_id):
                enrolled = self.db.get_students_in_subject(subj_id)
                scores = []
                for s_id, *_ in enrolled:
                    for g in self.db.get_student_grades(s_id):
                        # g = (grade_id, subj_name, code, score, letter, semester)
                        if g[2] == subj_code and g[3] is not None:
                            scores.append(g[3])
                average = round(sum(scores) / len(scores), 2) if scores else 0.0
                model.subjects.append({
                    "subject_id": subj_id,
                    "name": subj_name,
                    "code": subj_code,
                    "students_count": len(enrolled),
                    "average": average
                })
        elif role == "admin":
            model = Admin(user_id, name, username, 3)

        if not model:
            return

        role_permission_map = {
            "student": "view_own_grades",
            "teacher": "edit_grades",
            "admin":   "manage_users",
        }
        required = role_permission_map.get(role)
        if not required or not model.has_permission(required):
            show_error(self.window, "Access Denied", "Your account lacks the necessary system permissions to proceed.")
            return


        self.window.destroy()

        view = None
        if role == "student":
            view = StudentView(model, self.db)
        elif role == "teacher":
            view = TeacherView(model, self.db)
        elif role == "admin":
            view = AdminView(model, self.db)

        if view:
            view.render()

    def render(self):
        self.window.mainloop()
