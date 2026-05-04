# -----------------------------------------------
# login_screen.py - ScholarTrack LMS
# Role:     Displays the login form and routes each
#           authenticated user to their role-specific view.
# Key classes used: LoginScreen, DatabaseManager,
#                   Student, Teacher, Admin
# OOP concepts demonstrated: Encapsulation (UI logic
#   isolated in LoginScreen), Polymorphism (different
#   model objects and views created per role),
#   Inheritance (Student/Teacher/Admin all extend User)
# -----------------------------------------------
"""
Login screen — standard Tkinter, no third-party GUI library.
"""
import tkinter as tk
from tkinter import ttk

from gui.theme import THEME
from database.db_manager import DatabaseManager
from models.student import Student
from models.teacher import Teacher
from models.admin import Admin
from gui.teacher_view import TeacherView
from gui.student_view import StudentView
from gui.admin_view import AdminView
from models.exceptions import PermissionDeniedError
from gui.dialogs import show_error

BG_DARK = THEME["COLOR_BG_DARK"]
BG_CARD = THEME["COLOR_BG_CARD"]
FG      = "white"
ACCENT  = "#4a9eff"


class LoginScreen:
    """Handles GUI and logic for user authentication.

    This class demonstrates encapsulation by isolating UI layouts from core application logic.
    """
    def __init__(self, db: DatabaseManager):
        """Initializes the authentication GUI.

        Args:
            db (DatabaseManager): The initialized database connection manager.
        """
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
        """Constructs every widget on the login card: logo, entries, button, footer."""
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

        # Username entry
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

        # Password entry
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

    def _add_placeholder(self, entry: tk.Entry, placeholder: str, is_password=False):
        """Simulates placeholder text: shows muted hint text until the user types."""
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
        """Reads the entry fields, validates them, and either shows an error or
        calls launch_dashboard() with the authenticated user row."""
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        # Treat the placeholder strings as empty input.
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
        """Constructs the correct model object for the role and opens its view window.

        Args:
            user_row (tuple): The validated DB row for the matched user.
            role (str): The role string ('student', 'teacher', or 'admin').
        """
        user_id  = user_row[0]
        name     = user_row[1]
        username = user_row[2]

        try:
            # ── Build the domain model for this role ──────────────
            model = None
            if role == "student":
                student_row = self.db._fetch_one(
                    "SELECT * FROM students WHERE user_id = ?", (user_id,))
                if student_row:
                    s_id = student_row[0]
                    sem  = student_row[2]
                    dept = student_row[3]
                    model = Student(s_id, name, username, sem, dept)
            elif role == "teacher":
                model = Teacher(user_id, name, username, "General")
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
                raise PermissionDeniedError("Your account lacks the necessary system permissions to proceed.")

            self.db.log_action(user_id, "LOGIN", username)
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

        except PermissionDeniedError as e:
            show_error(self.window, "Access Denied", str(e))

    def render(self):
        """Renders the login screen window."""
        self.window.mainloop()
