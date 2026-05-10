# Provides reusable modal popup windows for alerts and confirmations
# Abstraction: exposes simple methods like show_success() without requiring clients to build Tkinter windows
# Polymorphism: reuses a common base dialog factory to generate different visual outcomes
import tkinter as tk
from gui.theme import THEME

BG = THEME["COLOR_BG_CARD"]
FG = "white"


def _style_btn(btn, bg_color):
    btn.configure(bg=bg_color, fg="white", activebackground=bg_color, activeforeground="white", relief="flat", cursor="hand2", font=THEME["FONT_BUTTON"])


def _create_base_dialog(parent, title, message, icon):
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.geometry("380x260")
    dlg.resizable(False, False)
    dlg.focus()
    dlg.configure(bg=BG)

    tk.Label(dlg, text=icon, font=("Segoe UI", 40), bg=BG, fg=FG).pack(pady=(15, 5))
    tk.Label(dlg, text=title, font=THEME["FONT_HEADING"], bg=BG, fg=THEME["COLOR_TEXT_MUTED"]).pack()
    tk.Label(dlg, text=message, font=THEME["FONT_BODY"], bg=BG, fg=FG, wraplength=320, justify="center").pack(pady=(5, 10))

    return dlg


def show_success(parent, title, message):
    dlg = _create_base_dialog(parent, title, message, "✅")

    btn = tk.Button(dlg, text="OK", command=dlg.destroy, width=12, height=2)
    _style_btn(btn, THEME["COLOR_SUCCESS"])
    btn.pack(pady=(0, 15))


def show_error(parent, title, message):
    dlg = _create_base_dialog(parent, title, message, "❌")

    btn = tk.Button(dlg, text="OK", command=dlg.destroy, width=12, height=2)
    _style_btn(btn, THEME["COLOR_DANGER"])
    btn.pack(pady=(0, 15))


def show_confirm(parent, title, message):
    dlg = _create_base_dialog(parent, title, message, "⚠️")

    result = {"value": False}

    def on_confirm():
        result["value"] = True
        dlg.destroy()

    def on_cancel():
        result["value"] = False
        dlg.destroy()

    btn_frame = tk.Frame(dlg, bg=BG)
    btn_frame.pack(pady=(10, 20))

    btn_conf = tk.Button(btn_frame, text="Confirm", command=on_confirm, width=12, height=2)
    _style_btn(btn_conf, THEME["COLOR_DANGER"])
    btn_conf.pack(side="left", padx=10)

    btn_canc = tk.Button(btn_frame, text="Cancel", command=on_cancel, width=12, height=2, relief="solid", bd=1)
    btn_canc.configure(bg=BG, fg=THEME["COLOR_TEXT_MUTED"], activebackground="#3A3A4E", activeforeground="white", font=THEME["FONT_BUTTON"], cursor="hand2")
    btn_canc.pack(side="left", padx=10)

    dlg.protocol("WM_DELETE_WINDOW", on_cancel)
    parent.wait_window(dlg)
    return result["value"]
