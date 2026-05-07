# Provides reusable modal popup windows for alerts, confirmations, and input forms
# Abstraction: exposes simple methods like show_success() without requiring clients to build Tkinter windows
# Polymorphism: reuses a common base dialog factory to generate different visual outcomes
import tkinter as tk
from tkinter import ttk
from gui.theme import THEME

BG = THEME["COLOR_BG_CARD"]
FG = "white"


def center_window(window, width, height, parent=None):
    window.update_idletasks()
    if parent is None:
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
    else:
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw // 2) - (width // 2)
        y = py + (ph // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def _style_btn(btn, bg_color):
    btn.configure(bg=bg_color, fg="white", activebackground=bg_color,
                  activeforeground="white", relief="flat", cursor="hand2",
                  font=THEME["FONT_BUTTON"])


def _create_base_dialog(parent, title, message, icon):
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    center_window(dlg, 380, 260, parent)
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.focus()
    dlg.configure(bg=BG)

    tk.Label(dlg, text=icon, font=("Segoe UI", 40), bg=BG, fg=FG).pack(pady=(15, 5))
    tk.Label(dlg, text=title, font=THEME["FONT_HEADING"], bg=BG, fg=THEME["COLOR_TEXT_MUTED"]).pack()
    tk.Label(dlg, text=message, font=THEME["FONT_BODY"], bg=BG, fg=FG,
             wraplength=320, justify="center").pack(pady=(5, 10))

    return dlg


def show_success(parent, title, message):
    dlg = _create_base_dialog(parent, title, message, "✅")

    btn = tk.Button(dlg, text="OK", command=dlg.destroy, width=12, height=2)
    _style_btn(btn, THEME["COLOR_SUCCESS"])
    btn.pack(pady=(0, 15))

    dlg.after(3000, lambda: dlg.destroy() if dlg.winfo_exists() else None)


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

    btn_canc = tk.Button(btn_frame, text="Cancel", command=on_cancel, width=12, height=2,
                         relief="solid", bd=1)
    btn_canc.configure(bg=BG, fg=THEME["COLOR_TEXT_MUTED"],
                       activebackground="#3A3A4E", activeforeground="white",
                       font=THEME["FONT_BUTTON"], cursor="hand2")
    btn_canc.pack(side="left", padx=10)

    dlg.protocol("WM_DELETE_WINDOW", on_cancel)
    parent.wait_window(dlg)
    return result["value"]


def show_input_form(parent, title, fields):
    h = 100 + (50 * len(fields)) + 80
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    center_window(dlg, 400, h, parent)
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.focus()
    dlg.configure(bg=BG)

    tk.Label(dlg, text=title, font=THEME["FONT_TITLE"], bg=BG, fg=FG).pack(pady=20)

    entries = {}
    for f in fields:
        e = tk.Entry(dlg, font=THEME["FONT_BODY"], width=28,
                     bg="#3A3A5E", fg=FG, insertbackground="white",
                     relief="flat")
        e.insert(0, f)   # placeholder-style pre-fill (field name as hint)
        e.bind("<FocusIn>",  lambda ev, ew=e, fn=f: ew.delete(0, "end") if ew.get() == fn else None)
        e.bind("<FocusOut>", lambda ev, ew=e, fn=f: ew.insert(0, fn) if ew.get() == "" else None)
        e.pack(pady=5, ipady=6)
        entries[f] = e

    result = {"value": None}

    def on_submit():
        res = {}
        for f, e in entries.items():
            val = e.get()
            res[f] = "" if val == f else val  # strip placeholder
        result["value"] = res
        dlg.destroy()

    def on_cancel():
        dlg.destroy()

    btn_frame = tk.Frame(dlg, bg=BG)
    btn_frame.pack(pady=20)

    btn_sub = tk.Button(btn_frame, text="Submit", command=on_submit, width=12, height=2)
    _style_btn(btn_sub, THEME["COLOR_PRIMARY"])
    btn_sub.pack(side="left", padx=10)

    btn_can = tk.Button(btn_frame, text="Cancel", command=on_cancel, width=12, height=2,
                        relief="solid", bd=1)
    btn_can.configure(bg=BG, fg=THEME["COLOR_TEXT_MUTED"],
                      activebackground="#3A3A4E", activeforeground="white",
                      font=THEME["FONT_BUTTON"], cursor="hand2")
    btn_can.pack(side="left", padx=10)

    dlg.protocol("WM_DELETE_WINDOW", on_cancel)
    parent.wait_window(dlg)
    return result["value"]
