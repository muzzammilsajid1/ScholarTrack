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

        self.window.geometry("420x580")
        self.window.resizable(False, False)
        self.window.configure(bg=BG_DARK)

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

        tk.Label(center_frame, text="Username", font=THEME["FONT_SMALL"], bg=BG_CARD, fg=THEME["COLOR_TEXT_MUTED"]).pack(anchor="w")
        self.entry_username = tk.Entry(
            center_frame,
            font=THEME["FONT_BODY"],
            width=28,
            bg="#3A3A5E",
            fg=FG,
            insertbackground="white",
            relief="flat",
        )
        self.entry_username.pack(pady=(0, 12), ipady=8)

        tk.Label(center_frame, text="Password", font=THEME["FONT_SMALL"], bg=BG_CARD, fg=THEME["COLOR_TEXT_MUTED"]).pack(anchor="w")
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
            relief="flat"
        )
        btn_login.pack(pady=(0, 20))

        tk.Label(
            center_frame,
            text="GIKI - CS112 Project",
            font=THEME["FONT_SMALL"],
            bg=BG_CARD,
            fg=THEME["COLOR_TEXT_MUTED"],
        ).pack()


    def attempt_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

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
            
        elif role == "admin":
            model = Admin(user_id, name, username, 3)

        if not model:
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
