# -----------------------------------------------
# dashboard.py - ScholarTrack LMS
# STATUS: LEGACY / UNUSED
#   This module is NOT instantiated anywhere in the
#   current application flow.  main.py routes users
#   via LoginScreen directly to the role-specific
#   views (StudentView, TeacherView, AdminView).
#   It is retained to demonstrate the OOP concepts
#   of encapsulation and abstraction via a sidebar-
#   navigation pattern.
# Key classes used: Dashboard, User, DatabaseManager
# OOP concepts demonstrated: Encapsulation (view
#   switching hidden behind clear_main_container),
#   Abstraction (User base class used for display)
# -----------------------------------------------
"""
Legacy dashboard shell — NOT used in the current application flow.
Retained for reference to demonstrate OOP sidebar-navigation patterns.
"""
import tkinter as tk
from tkinter import ttk

from gui.theme import THEME
from database.db_manager import DatabaseManager
from models.user import User

BG_DARK = THEME["COLOR_BG_DARK"]
BG_CARD = THEME["COLOR_BG_CARD"]
FG      = "white"
ACCENT  = "#4a9eff"


class Dashboard:
    """Handles the main application dashboard layout and routing.

    This class demonstrates encapsulation by managing its UI elements and dynamically
    swapping view contexts within a central container.
    """
    def __init__(self, user: User, db: DatabaseManager):
        """Initializes the dashboard interface for the logged-in user.

        Args:
            user (User): The authenticated user instance.
            db (DatabaseManager): The active database connection manager.
        """
        self.user = user
        self.db   = db

        self.window = tk.Tk()
        self.window.title("ScholarTrack - Dashboard")
        self.window.geometry("1000x700")
        self.window.minsize(800, 600)
        self.window.configure(bg=BG_DARK)

        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=1)

        self.build_sidebar()
        self.build_main_container()

        self.show_home_view()

        # Consistent Top-Right Logout Overlay
        btn_logout = tk.Button(
            self.window,
            text="Logout",
            command=self.logout,
            width=8,
            bg=THEME["COLOR_DANGER"],
            fg=FG,
            activebackground=THEME["COLOR_DANGER"],
            activeforeground=FG,
            font=THEME["FONT_BUTTON"],
            relief="flat",
            cursor="hand2",
        )
        btn_logout.place(relx=0.98, rely=0.02, anchor="ne")

    def build_sidebar(self):
        """Constructs the sidebar navigation menu."""
        self.sidebar_frame = tk.Frame(self.window, width=220, bg=BG_CARD)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        tk.Label(
            self.sidebar_frame,
            text="Smart Tracker",
            font=THEME["FONT_TITLE"],
            bg=BG_CARD,
            fg=FG,
        ).grid(row=0, column=0, padx=THEME["PADDING_MEDIUM"], pady=(THEME["PADDING_MEDIUM"], THEME["PADDING_SMALL"]))

        tk.Label(
            self.sidebar_frame,
            text=f"{self.user.name}",
            font=THEME["FONT_HEADING"],
            bg=BG_CARD,
            fg=FG,
        ).grid(row=1, column=0, padx=THEME["PADDING_MEDIUM"], pady=(THEME["PADDING_SMALL"], 0))

        tk.Label(
            self.sidebar_frame,
            text=f"{self.user.role.upper()} ACCOUNT",
            font=THEME["FONT_SMALL"],
            bg=BG_CARD,
            fg=THEME["COLOR_TEXT_MUTED"],
        ).grid(row=2, column=0, padx=THEME["PADDING_MEDIUM"], pady=(0, THEME["PADDING_MEDIUM"]))

        def _nav_btn(row, label, cmd):
            b = tk.Button(
                self.sidebar_frame,
                text=label,
                command=cmd,
                font=THEME["FONT_BUTTON"],
                bg=ACCENT,
                fg=FG,
                activebackground="#2563EB",
                activeforeground=FG,
                relief="flat",
                cursor="hand2",
                width=16,
            )
            b.grid(row=row, column=0, padx=THEME["PADDING_MEDIUM"], pady=THEME["PADDING_SMALL"])

        _nav_btn(3, "Home",     self.show_home_view)
        _nav_btn(4, "Students", self.show_student_view)
        _nav_btn(5, "Grades",   self.show_grade_view)
        _nav_btn(6, "Reports",  self.show_report_view)
        _nav_btn(8, "Settings", self.show_settings_view)

        btn_logout = tk.Button(
            self.sidebar_frame,
            text="Logout",
            command=self.logout,
            font=THEME["FONT_BUTTON"],
            bg=BG_CARD,
            fg=THEME["COLOR_TEXT_MUTED"],
            activebackground="#3A3A4E",
            activeforeground=FG,
            relief="solid",
            bd=1,
            cursor="hand2",
            width=16,
        )
        btn_logout.grid(row=9, column=0, padx=THEME["PADDING_MEDIUM"], pady=THEME["PADDING_MEDIUM"])

    def build_main_container(self):
        """Creates the main container for rendering dynamic views."""
        self.main_container = tk.Frame(
            self.window,
            bg=BG_CARD,
        )
        self.main_container.grid(
            row=0, column=1, sticky="nsew",
            padx=THEME["PADDING_MEDIUM"],
            pady=THEME["PADDING_MEDIUM"],
        )
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

    def clear_main_container(self):
        """Purges all active child widgets in the main container."""
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_home_view(self):
        """Displays the home dashboard screen."""
        self.clear_main_container()
        frame = tk.Frame(self.main_container, bg=BG_CARD)
        frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(frame, text="Dashboard Home", font=THEME["FONT_TITLE"], bg=BG_CARD, fg=FG).pack(
            pady=(40, THEME["PADDING_MEDIUM"]), padx=40, anchor="w"
        )
        welcome_string = f"Welcome back, {self.user.name}! Use the sidebar configuration paths to administrate records."
        tk.Label(frame, text=welcome_string, font=THEME["FONT_BODY"], bg=BG_CARD, fg=FG).pack(
            pady=THEME["PADDING_SMALL"], padx=40, anchor="w"
        )

    def show_student_view(self):
        """Displays the student management view."""
        self.clear_main_container()
        frame = tk.Frame(self.main_container, bg=BG_CARD)
        frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(frame, text="Virtual Student Frame", font=THEME["FONT_TITLE"], bg=BG_CARD, fg=FG).pack(
            pady=(40, THEME["PADDING_MEDIUM"]), padx=40, anchor="w"
        )
        tk.Label(frame, text="Browse and modify class participation schemas here.", font=THEME["FONT_BODY"], bg=BG_CARD, fg=FG).pack(
            pady=THEME["PADDING_SMALL"], padx=40, anchor="w"
        )

    def show_grade_view(self):
        """Displays the grades management view."""
        self.clear_main_container()
        frame = tk.Frame(self.main_container, bg=BG_CARD)
        frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(frame, text="Digital Grades Book", font=THEME["FONT_TITLE"], bg=BG_CARD, fg=FG).pack(
            pady=(40, THEME["PADDING_MEDIUM"]), padx=40, anchor="w"
        )
        tk.Label(frame, text="Insert and calculate GPAs using GradeService metrics.", font=THEME["FONT_BODY"], bg=BG_CARD, fg=FG).pack(
            pady=THEME["PADDING_SMALL"], padx=40, anchor="w"
        )

    def show_report_view(self):
        """Displays the system analytics view."""
        self.clear_main_container()
        frame = tk.Frame(self.main_container, bg=BG_CARD)
        frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(frame, text="System Analytics", font=THEME["FONT_TITLE"], bg=BG_CARD, fg=FG).pack(
            pady=(40, THEME["PADDING_MEDIUM"]), padx=40, anchor="w"
        )
        tk.Label(frame, text="Generate system-wide metrics and performance reports mapping.", font=THEME["FONT_BODY"], bg=BG_CARD, fg=FG).pack(
            pady=THEME["PADDING_SMALL"], padx=40, anchor="w"
        )

    def show_settings_view(self):
        """Displays the account configuration view."""
        self.clear_main_container()
        frame = tk.Frame(self.main_container, bg=BG_CARD)
        frame.grid(row=0, column=0, sticky="nsew")

        tk.Label(frame, text="Account Configuration", font=THEME["FONT_TITLE"], bg=BG_CARD, fg=FG).pack(
            pady=(40, THEME["PADDING_MEDIUM"]), padx=40, anchor="w"
        )
        tk.Label(frame, text="Modify permissions and structural application variables.", font=THEME["FONT_BODY"], bg=BG_CARD, fg=FG).pack(
            pady=THEME["PADDING_SMALL"], padx=40, anchor="w"
        )

    def logout(self):
        """Terminates the current session and returns to login."""
        self.user = None
        self.window.destroy()

        from gui.login_screen import LoginScreen
        app = LoginScreen(self.db)
        app.render()

    def render(self):
        """Mounts and renders the dashboard UI loop."""
        self.window.mainloop()
