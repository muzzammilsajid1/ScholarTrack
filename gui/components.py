import tkinter as tk
from tkinter import ttk
from gui.theme import THEME


def create_header(parent, user_name: str, user_role: str, on_logout) -> tk.Frame:
    """Creates a reusable, standardized header bar across dynamic windows."""
    BG = "#16213E"
    header = tk.Frame(parent, height=64, bg=BG)
    header.pack(fill="x")

    # Needs to prevent squeezing smaller than height=64
    header.pack_propagate(False)

    # --- LEFT SIDE --- #
    left_frame = tk.Frame(header, bg=BG)
    left_frame.pack(side="left", padx=(16, 0), fill="y")

    lbl_logo = tk.Label(left_frame, text="🎓", font=("Segoe UI", 20), bg=BG, fg="white")
    lbl_logo.pack(side="left")

    lbl_app_name = tk.Label(
        left_frame,
        text="ScholarTrack",
        font=THEME["FONT_HEADING"],
        bg=BG,
        fg=THEME["COLOR_PRIMARY"],
    )
    lbl_app_name.pack(side="left", padx=(8, 0))

    separator = tk.Frame(left_frame, width=1, height=30, bg="#3A3A4E")
    separator.pack(side="left", padx=16)

    # --- CENTER --- #
    # User wrapper expands and fills available space forcing the right frame to stay on the edge
    center_frame = tk.Frame(header, bg=BG)
    center_frame.pack(side="left", fill="x", expand=True)

    lbl_user = tk.Label(center_frame, text=user_name, font=THEME["FONT_BODY"], bg=BG, fg="white")
    lbl_user.pack(anchor="w", pady=(12, 0))

    lbl_role = tk.Label(
        center_frame,
        text=user_role.upper(),
        font=THEME["FONT_SMALL"],
        bg=BG,
        fg=THEME["COLOR_TEXT_MUTED"],
    )
    lbl_role.pack(anchor="w", pady=(0, 12))

    # --- RIGHT SIDE --- #
    right_frame = tk.Frame(header, bg=BG)
    right_frame.pack(side="right", padx=(0, 16), fill="y")

    btn_logout = tk.Button(
        right_frame,
        text="Logout",
        width=10,
        relief="solid",
        bd=1,
        font=THEME["FONT_SMALL"],
        bg=BG,
        fg=THEME["COLOR_DANGER"],
        activebackground="#3A1A1A",
        activeforeground=THEME["COLOR_DANGER"],
        cursor="hand2",
        command=on_logout,
    )
    btn_logout.pack(pady=16)

    return header
