# System administrator panel for managing users, subjects, enrollments, and attendance
# Encapsulation: isolates admin-specific GUI layouts and CRUD events
# Polymorphism: reuses shared GUI components like dialogs and headers across different views
import tkinter as tk
from tkinter import ttk

from gui.theme import THEME
from gui.components import create_header
from gui.dialogs import show_success, show_error, show_confirm
from models.admin import Admin


BG   = THEME["COLOR_BG_DARK"]
CARD = THEME["COLOR_BG_CARD"]
FG   = "white"
ACC  = "#4a9eff"


class AdminView:
    def __init__(self, admin, db):
        self.admin = admin
        self.db    = db

        self.window = tk.Tk()
        self.window.title("ScholarTrack - Admin Dashboard")
        self.window.configure(bg=BG)
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth()  // 2) - (1100 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700  // 2)
        self.window.geometry(f"1100x700+{x}+{y}")
        self.window.resizable(False, False)

        self._build_ui()

    # ── Shared Treeview style ─────────────────────────────────────

    def _apply_tree_style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Admin.Treeview",
                    background=CARD, foreground=FG,
                    fieldbackground=CARD, rowheight=30,
                    font=THEME["FONT_BODY"])
        s.configure("Admin.Treeview.Heading",
                    background="#16213E", foreground=FG,
                    font=THEME["FONT_BUTTON"])
        s.map("Admin.Treeview.Heading", foreground=[("active", "#1e1e2e")])
        s.map("Admin.Treeview", background=[("selected", ACC)])

    def _make_treeview(self, parent, columns, widths):
        # Create a styled Treeview with a vertical scrollbar.
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True, pady=(5, 0))

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                            style="Admin.Treeview")
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree

    # ── UI construction ───────────────────────────────────────────

    def _build_ui(self):
        # Assemble header + Notebook.
        self._apply_tree_style()
        create_header(self.window, self.admin.name, "Administrator", self._logout)
        self._build_stats_bar()
        self._build_notebook()

    def _build_stats_bar(self):
        # Quick summary strip across the top.
        n_stu = len(self.db.get_all_students())
        n_tch = len([u for u in self.db.get_all_users() if u[3] == "teacher"])
        n_sub = len(self.db.get_all_subjects())
        risk  = sum(1 for s in self.db.get_all_students()
                    if self.db.get_student_gpa(s[0]) < 2.0)

        bar = tk.Frame(self.window, bg=CARD, height=75)
        bar.pack(fill="x"); bar.pack_propagate(False)

        for label, val, color in [
            ("Students", n_stu,  FG),
            ("Teachers", n_tch,  FG),
            ("Subjects", n_sub,  FG),
            ("At Risk",  risk,   THEME["COLOR_DANGER"] if risk else FG),
        ]:
            cell = tk.Frame(bar, bg=CARD)
            cell.pack(side="left", expand=True, fill="both")
            tk.Label(cell, text=str(val), font=THEME["FONT_TITLE"],
                     bg=CARD, fg=color).pack()
            tk.Label(cell, text=label, font=THEME["FONT_SMALL"],
                     bg=CARD, fg=THEME["COLOR_TEXT_MUTED"]).pack()

    def _build_notebook(self):
        # Create the ttk.Notebook with Students/Teachers/Subjects/Assignments/Enrollments/Attendance/Activity tabs.
        style = ttk.Style()
        style.configure("TNotebook",        background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",    background=CARD, foreground=FG,
                        padding=[14, 6], font=THEME["FONT_BUTTON"])
        style.map("TNotebook.Tab",          background=[("selected", ACC)],
                  foreground=[("selected", FG)])

        nb = ttk.Notebook(self.window)
        nb.pack(fill="both", expand=True, padx=15, pady=10)

        tab_students    = tk.Frame(nb, bg=BG)
        tab_teachers    = tk.Frame(nb, bg=BG)
        tab_subjects    = tk.Frame(nb, bg=BG)
        tab_assignments = tk.Frame(nb, bg=BG)
        tab_enrollments = tk.Frame(nb, bg=BG)
        tab_attendance  = tk.Frame(nb, bg=BG)

        nb.add(tab_students,    text="  Students  ")
        nb.add(tab_teachers,    text="  Teachers  ")
        nb.add(tab_subjects,    text="  Subjects  ")
        nb.add(tab_assignments, text="  Assignments  ")
        nb.add(tab_enrollments, text="  Enrollments  ")
        nb.add(tab_attendance,  text="  Attendance  ")

        self._build_students_tab(tab_students)
        self._build_teachers_tab(tab_teachers)
        self._build_subjects_tab(tab_subjects)
        self._build_assignments_tab(tab_assignments)
        self._build_enrollments_tab(tab_enrollments)
        self._build_attendance_tab(tab_attendance)

    # ── Students tab ─────────────────────────────────────────────

    def _build_students_tab(self, parent):
        # Students Treeview + Add / Delete buttons.
        tk.Label(parent, text="All Students",
                 font=THEME["FONT_HEADING"], bg=BG, fg=FG
                 ).pack(anchor="w", pady=(8, 2))

        cols    = ("ID", "Name", "Username", "Department", "Sem", "GPA", "Status")
        widths  = [45, 180, 130, 160, 50, 70, 100]
        self.student_tree = self._make_treeview(parent, cols, widths)
        self._load_students()

        btn_bar = tk.Frame(parent, bg=BG)
        btn_bar.pack(fill="x", pady=8)
        tk.Button(btn_bar, text="Add Student",
                  command=self._open_add_student,
                  font=THEME["FONT_BUTTON"], bg=ACC, fg=FG,
                  activebackground="#2563EB", relief="flat",
                  cursor="hand2", padx=12, pady=4
                  ).pack(side="left", padx=(0, 8))
        tk.Button(btn_bar, text="Delete Selected",
                  command=lambda: self._delete_selected(self.student_tree, "student"),
                  font=THEME["FONT_BUTTON"], bg=THEME["COLOR_DANGER"], fg=FG,
                  activebackground="#DC2626", relief="flat",
                  cursor="hand2", padx=12, pady=4
                  ).pack(side="left")

    def _load_students(self):
        # Fetch all students from DB and populate the Treeview.
        self.student_tree.delete(*self.student_tree.get_children())
        for u in self.db.get_all_users():
            user_id, name, username, role, s_id, sem, dept = u
            if role != "student":
                continue
            gpa    = self.db.get_student_gpa(s_id) if s_id else 0.0
            status = "At Risk" if gpa < 2.0 else "Good"
            self.student_tree.insert("", "end", iid=str(user_id),
                                     values=(user_id, name, username,
                                             dept or "", sem or "", f"{gpa:.2f}", status))

    def _open_add_student(self):
        # Popup form to register a new student.
        popup = self._make_popup("Add New Student", 420, 480)
        main  = tk.Frame(popup, bg=BG)
        main.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(main, text="Register Student",
                 font=THEME["FONT_TITLE"], bg=BG, fg=FG).pack(pady=(0, 15))

        fields = {}
        for label, key, kw in [
            ("Full Name",   "name",  {}),
            ("Username",    "user",  {}),
            ("Password",    "pass",  {"show": "•"}),
            ("Department",  "dept",  {}),
            ("Semester",    "sem",   {}),
        ]:
            tk.Label(main, text=label, font=THEME["FONT_SMALL"],
                     bg=BG, fg=THEME["COLOR_TEXT_MUTED"]).pack(anchor="w")
            e = tk.Entry(main, font=THEME["FONT_BODY"], width=32,
                         bg="#3A3A5E", fg=FG, insertbackground="white",
                         relief="flat", **kw)
            e.pack(pady=(0, 8), ipady=5)
            fields[key] = e

        err = tk.Label(main, text="", font=THEME["FONT_SMALL"],
                       bg=BG, fg=THEME["COLOR_DANGER"])
        err.pack()

        def _commit():
            n, u, p = fields["name"].get().strip(), fields["user"].get().strip(), fields["pass"].get().strip()
            d, s    = fields["dept"].get().strip(), fields["sem"].get().strip()
            if not all([n, u, p, d, s]):
                err.configure(text="All fields are required."); return
            if not s.isdigit():
                err.configure(text="Semester must be a number."); return
            if not Admin.validate_username(u):
                err.configure(text="Username must be 3–20 alphanumeric chars."); return
            try:
                self.db.add_student(n, u, p, int(s), d)
                
                popup.destroy()
                self._load_students()
                show_success(self.window, "Success", f"{n} added successfully.")
            except Exception as exc:
                err.configure(text=str(exc))

        tk.Button(main, text="Register", command=_commit,
                  font=THEME["FONT_BUTTON"], bg=ACC, fg=FG,
                  relief="flat", cursor="hand2", pady=6
                  ).pack(fill="x", pady=(8, 0))

    # ── Teachers tab ─────────────────────────────────────────────

    def _build_teachers_tab(self, parent):
        # Teachers Treeview + Add / Delete buttons.
        tk.Label(parent, text="All Teachers",
                 font=THEME["FONT_HEADING"], bg=BG, fg=FG
                 ).pack(anchor="w", pady=(8, 2))

        cols   = ("ID", "Name", "Username")
        widths = [60, 280, 200]
        self.teacher_tree = self._make_treeview(parent, cols, widths)
        self._load_teachers()

        btn_bar = tk.Frame(parent, bg=BG)
        btn_bar.pack(fill="x", pady=8)
        tk.Button(btn_bar, text="Add Teacher",
                  command=self._open_add_teacher,
                  font=THEME["FONT_BUTTON"], bg=ACC, fg=FG,
                  activebackground="#2563EB", relief="flat",
                  cursor="hand2", padx=12, pady=4
                  ).pack(side="left", padx=(0, 8))
        tk.Button(btn_bar, text="Delete Selected",
                  command=lambda: self._delete_selected(self.teacher_tree, "teacher"),
                  font=THEME["FONT_BUTTON"], bg=THEME["COLOR_DANGER"], fg=FG,
                  activebackground="#DC2626", relief="flat",
                  cursor="hand2", padx=12, pady=4
                  ).pack(side="left")

    def _load_teachers(self):
        # Fetch all teachers and populate the Treeview.
        self.teacher_tree.delete(*self.teacher_tree.get_children())
        for u in self.db.get_all_users():
            user_id, name, username, role, *_ = u
            if role == "teacher":
                self.teacher_tree.insert("", "end", iid=str(user_id),
                                         values=(user_id, name, username))

    def _open_add_teacher(self):
        # Popup form to register a new teacher.
        popup = self._make_popup("Add New Teacher", 420, 360)
        main  = tk.Frame(popup, bg=BG)
        main.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(main, text="Register Teacher",
                 font=THEME["FONT_TITLE"], bg=BG, fg=FG).pack(pady=(0, 15))

        fields = {}
        for label, key, kw in [
            ("Full Name", "name", {}),
            ("Username",  "user", {}),
            ("Password",  "pass", {"show": "•"}),
        ]:
            tk.Label(main, text=label, font=THEME["FONT_SMALL"],
                     bg=BG, fg=THEME["COLOR_TEXT_MUTED"]).pack(anchor="w")
            e = tk.Entry(main, font=THEME["FONT_BODY"], width=32,
                         bg="#3A3A5E", fg=FG, insertbackground="white",
                         relief="flat", **kw)
            e.pack(pady=(0, 8), ipady=5)
            fields[key] = e

        err = tk.Label(main, text="", font=THEME["FONT_SMALL"],
                       bg=BG, fg=THEME["COLOR_DANGER"])
        err.pack()

        def _commit():
            n, u, p = fields["name"].get().strip(), fields["user"].get().strip(), fields["pass"].get().strip()
            if not all([n, u, p]):
                err.configure(text="All fields are required."); return
            if not Admin.validate_username(u):
                err.configure(text="Username must be 3–20 alphanumeric chars."); return
            try:
                result = self.db.add_teacher(n, u, p)
                if result is None:
                    err.configure(text="Username already exists."); return
                
                popup.destroy()
                self._load_teachers()
                show_success(self.window, "Success", f"Teacher '{n}' registered.")
            except Exception as exc:
                err.configure(text=str(exc))

        tk.Button(main, text="Register", command=_commit,
                  font=THEME["FONT_BUTTON"], bg=ACC, fg=FG,
                  relief="flat", cursor="hand2", pady=6
                  ).pack(fill="x", pady=(8, 0))



    # ── Attendance tab ─────────────────────────────────────────

    def _build_attendance_tab(self, parent):
        # Read-only Treeview of all attendance records + Delete Selected button.
        tk.Label(parent, text="All Attendance Records",
                 font=THEME["FONT_HEADING"], bg=BG, fg=FG
                 ).pack(anchor="w", pady=(8, 2))

        cols   = ("ID", "Student", "Subject", "Date", "Status")
        widths = [50, 220, 200, 120, 100]
        self.att_tree = self._make_treeview(parent, cols, widths)
        self._load_attendance()

        btn_bar = tk.Frame(parent, bg=BG)
        btn_bar.pack(fill="x", pady=8)
        tk.Button(btn_bar, text="Delete Selected Record",
                  command=self._delete_att_record,
                  font=THEME["FONT_BUTTON"], bg=THEME["COLOR_DANGER"], fg=FG,
                  activebackground="#DC2626", relief="flat",
                  cursor="hand2", padx=12, pady=4
                  ).pack(side="left", padx=(0, 8))
        tk.Button(btn_bar, text="Refresh",
                  command=self._load_attendance,
                  font=THEME["FONT_BUTTON"], bg=CARD, fg=FG,
                  activebackground="#3A3A5E", relief="solid", bd=1,
                  cursor="hand2", padx=12, pady=4
                  ).pack(side="left")

    def _load_attendance(self):
        # Fetch all attendance records via the public API.
        self.att_tree.delete(*self.att_tree.get_children())
        try:
            for student in self.db.get_all_students():
                # student = (student_id, name, username, semester, dept)
                student_id, student_name = student[0], student[1]
                for rec in self.db.get_student_attendance(student_id):
                    # rec = (att_id, subj_name, code, date, status)
                    att_id, subj_name, code, date, status = rec
                    self.att_tree.insert("", "end", iid=str(att_id),
                                         values=(att_id, student_name, subj_name, date, status))
        except Exception as e:
            print(f"[AdminView] _load_attendance error: {e}")

    def _delete_att_record(self):
        # Delete the selected attendance row after confirmation.
        sel = self.att_tree.selection()
        if not sel:
            show_error(self.window, "No Selection",
                       "Select an attendance row to delete."); return
        att_id   = int(sel[0])
        row_vals = self.att_tree.item(sel[0])["values"]
        label    = f"{row_vals[1]} — {row_vals[2]} on {row_vals[3]}"
        if show_confirm(self.window, "Delete Attendance Record",
                        f"Delete this record?\n\n{label}"):
            try:
                self.db.delete_attendance(att_id)
                
                self.att_tree.delete(sel[0])
                show_success(self.window, "Deleted", "Attendance record removed.")
            except Exception as exc:
                show_error(self.window, "Error", str(exc))

    # ── Assignments tab ───────────────────────────────────────────

    def _build_assignments_tab(self, parent):
        # Teacher–Subject assignment manager: Treeview + Assign / Remove controls.
        tk.Label(parent, text="Teacher–Subject Assignments",
                 font=THEME["FONT_HEADING"], bg=BG, fg=FG
                 ).pack(anchor="w", pady=(8, 2), padx=5)

        # ── Treeview ──
        cols   = ("Teacher", "Subject", "Code")
        widths = [260, 280, 120]
        self.assign_tree = self._make_treeview(parent, cols, widths)
        self._load_assignments()

        # ── Controls row ──
        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=5, pady=(8, 4))

        # Teacher dropdown
        tk.Label(ctrl, text="Teacher:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(10, 4), pady=10)
        self.asgn_teacher_var = tk.StringVar()
        self.asgn_teacher_cb  = ttk.Combobox(ctrl, textvariable=self.asgn_teacher_var,
                                              state="readonly",
                                              font=THEME["FONT_BODY"], width=22)
        self.asgn_teacher_cb.pack(side="left", padx=(0, 10))

        # Subject dropdown
        tk.Label(ctrl, text="Subject:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(0, 4))
        self.asgn_subject_var = tk.StringVar()
        self.asgn_subject_cb  = ttk.Combobox(ctrl, textvariable=self.asgn_subject_var,
                                              state="readonly",
                                              font=THEME["FONT_BODY"], width=22)
        self.asgn_subject_cb.pack(side="left", padx=(0, 10))

        # Assign button
        tk.Button(ctrl, text="Assign",
                  command=self._do_assign,
                  font=THEME["FONT_BUTTON"],
                  bg=ACC, fg=FG, activebackground="#2563EB",
                  relief="flat", cursor="hand2", padx=12, pady=4
                  ).pack(side="left", padx=(0, 6))

        # Remove button
        tk.Button(ctrl, text="Remove Selected",
                  command=self._do_unassign,
                  font=THEME["FONT_BUTTON"],
                  bg=THEME["COLOR_DANGER"], fg=FG, activebackground="#DC2626",
                  relief="flat", cursor="hand2", padx=12, pady=4
                  ).pack(side="left")

        self.asgn_status_lbl = tk.Label(ctrl, text="",
                                        font=THEME["FONT_SMALL"], bg=CARD, fg=FG)
        self.asgn_status_lbl.pack(side="left", padx=10)

        self._refresh_asgn_dropdowns()

    def _load_assignments(self):
        # Fetch all teacher-subject assignments and populate the Treeview.
        self.assign_tree.delete(*self.assign_tree.get_children())
        for row in self.db.get_all_assignments():
            # row: (teacher_name, subject_name, code, teacher_id, subject_id)
            iid = f"{row[3]}:{row[4]}"   # unique key for removal
            self.assign_tree.insert("", "end", iid=iid,
                                    values=(row[0], row[1], row[2]))

    def _refresh_asgn_dropdowns(self):
        # Rebuild teacher and subject Comboboxes from live DB data.
        teachers = [(u[0], u[1]) for u in self.db.get_all_users() if u[3] == "teacher"]
        self._asgn_teachers = teachers
        self.asgn_teacher_cb["values"] = [t[1] for t in teachers]
        if teachers:
            self.asgn_teacher_cb.current(0)

        subjects = self.db.get_all_subjects()
        self._asgn_subjects = subjects
        self.asgn_subject_cb["values"] = [f"{s[1]} ({s[2]})" for s in subjects]
        if subjects:
            self.asgn_subject_cb.current(0)

    def _do_assign(self):
        # Validate dropdowns, check for existing assignment, then persist.
        if not self._asgn_teachers or not self._asgn_subjects:
            self._show_asgn_status("No teachers or subjects available.", err=True)
            return

        t_idx = self.asgn_teacher_cb.current()
        s_idx = self.asgn_subject_cb.current()
        if t_idx < 0 or s_idx < 0:
            self._show_asgn_status("Select both a teacher and a subject.", err=True)
            return

        teacher_id, teacher_name = self._asgn_teachers[t_idx]
        subject_id, subj_name, subj_code = self._asgn_subjects[s_idx]

        # Check if this subject already has a teacher assigned — warn before overwriting.
        existing = self.db.get_subject_teacher(subject_id)
        if existing and existing[0] != teacher_id:
            if not show_confirm(
                    self.window, "Reassign Subject",
                    f"'{subj_name}' is already assigned to {existing[1]}.\n"
                    f"Reassign to {teacher_name}?"):
                return

        try:
            self.db.assign_subject_to_teacher(teacher_id, subject_id)
            
            self._load_assignments()
            self._refresh_asgn_dropdowns()
            self._show_asgn_status(f"✔ {subj_name} assigned to {teacher_name}", err=False)
        except Exception as exc:
            self._show_asgn_status(f"Error: {exc}", err=True)

    def _do_unassign(self):
        # Remove the selected assignment row after confirmation.
        sel = self.assign_tree.selection()
        if not sel:
            show_error(self.window, "No Selection", "Select a row to remove.")
            return
        iid = sel[0]   # "teacher_id:subject_id"
        try:
            teacher_id, subject_id = map(int, iid.split(":"))
        except ValueError:
            show_error(self.window, "Error", "Could not parse assignment row."); return

        row_vals = self.assign_tree.item(iid)["values"]
        label = f"{row_vals[0]} → {row_vals[1]}"
        if show_confirm(self.window, "Remove Assignment", f"Remove assignment:\n{label}?"):
            try:
                self.db.unassign_subject_from_teacher(teacher_id, subject_id)
                
                self._load_assignments()
                self._refresh_asgn_dropdowns()
                self._show_asgn_status(f"Removed: {label}", err=False)
            except Exception as exc:
                show_error(self.window, "Error", str(exc))

    def _show_asgn_status(self, msg, err: bool = False):
        # Temporary inline feedback next to the assignment buttons.
        self.asgn_status_lbl.configure(
            text=msg, fg=THEME["COLOR_DANGER"] if err else THEME["COLOR_SUCCESS"])
        self.window.after(4000, lambda: self.asgn_status_lbl.configure(text=""))

    # ── Enrollments tab ───────────────────────────────────────────

    def _build_enrollments_tab(self, parent):
        # Enrollment manager: Treeview of all enrollments + Enroll / Remove controls.
        tk.Label(parent, text="All Enrollments",
                 font=THEME["FONT_HEADING"], bg=BG, fg=FG
                 ).pack(anchor="w", pady=(8, 2), padx=5)

        # ── Treeview ──
        cols   = ("Student", "Subject", "Code")
        widths = [280, 280, 120]
        self.enroll_tree = self._make_treeview(parent, cols, widths)
        self._load_enrollments()

        # ── Controls row ──
        ctrl = tk.Frame(parent, bg=CARD)
        ctrl.pack(fill="x", padx=5, pady=(8, 4))

        # Student dropdown
        tk.Label(ctrl, text="Student:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(10, 4), pady=10)
        self.enroll_student_var = tk.StringVar()
        self.enroll_student_cb  = ttk.Combobox(ctrl, textvariable=self.enroll_student_var,
                                               state="readonly",
                                               font=THEME["FONT_BODY"], width=22)
        self.enroll_student_cb.pack(side="left", padx=(0, 12))

        # Subject dropdown
        tk.Label(ctrl, text="Subject:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(0, 4))
        self.enroll_subject_var = tk.StringVar()
        self.enroll_subject_cb  = ttk.Combobox(ctrl, textvariable=self.enroll_subject_var,
                                               state="readonly",
                                               font=THEME["FONT_BODY"], width=22)
        self.enroll_subject_cb.pack(side="left", padx=(0, 12))

        # Enroll button
        tk.Button(ctrl, text="Enroll",
                  command=self._enroll_student,
                  font=THEME["FONT_BUTTON"],
                  bg=ACC, fg=FG, activebackground="#2563EB",
                  relief="flat", cursor="hand2", padx=12, pady=4
                  ).pack(side="left", padx=(0, 6))

        # Remove button
        tk.Button(ctrl, text="Remove Selected",
                  command=self._unenroll_student,
                  font=THEME["FONT_BUTTON"],
                  bg=THEME["COLOR_DANGER"], fg=FG, activebackground="#DC2626",
                  relief="flat", cursor="hand2", padx=12, pady=4
                  ).pack(side="left")

        self.enroll_status_lbl = tk.Label(ctrl, text="",
                                          font=THEME["FONT_SMALL"], bg=CARD, fg=FG)
        self.enroll_status_lbl.pack(side="left", padx=10)

        # Populate dropdowns on first build.
        self._refresh_enroll_dropdowns()

    def _load_enrollments(self):
        # Fetch all enrollment rows via the public API.
        self.enroll_tree.delete(*self.enroll_tree.get_children())
        for student in self.db.get_all_students():
            # student = (student_id, name, username, semester, dept)
            student_id, student_name = student[0], student[1]
            for subj in self.db.get_subjects_for_student(student_id):
                # subj = (subject_id, name, code)
                subject_id, subj_name, subj_code = subj
                iid = f"{student_id}-{subject_id}"
                self.enroll_tree.insert("", "end", iid=iid,
                                        values=(student_name, subj_name, subj_code))

    def _refresh_enroll_dropdowns(self):
        # Rebuild the student and subject Combobox lists from live DB data.
        students = self.db.get_all_students()   # (student_id, name, ...)
        self._enroll_students = students
        self.enroll_student_cb["values"] = [s[1] for s in students]
        if students:
            self.enroll_student_cb.current(0)

        subjects = self.db.get_all_subjects()   # (subject_id, name, code)
        self._enroll_subjects = subjects
        self.enroll_subject_cb["values"] = [f"{s[1]} ({s[2]})" for s in subjects]
        if subjects:
            self.enroll_subject_cb.current(0)

    def _enroll_student(self):
        # Read the dropdowns and insert the enrollment row.
        s_idx = self.enroll_student_cb.current()
        j_idx = self.enroll_subject_cb.current()
        if s_idx < 0 or j_idx < 0:
            self._show_enroll_status("Select a student and a subject.", err=True)
            return

        student_id,   student_name = self._enroll_students[s_idx][0], self._enroll_students[s_idx][1]
        subject_id,   subj_name    = self._enroll_subjects[j_idx][0], self._enroll_subjects[j_idx][1]
        subj_code                  = self._enroll_subjects[j_idx][2]

        enrolled = self.db.enroll_student(student_id, subject_id)
        if not enrolled:
            self._show_enroll_status(f"{student_name} is already enrolled in {subj_name}.", err=True)
            return

        
        # Reload Treeview AND dropdowns so fresh data is reflected everywhere.
        self._load_enrollments()
        self._refresh_enroll_dropdowns()
        self._show_enroll_status(f"Enrolled {student_name} in {subj_name}.", err=False)

    def _unenroll_student(self):
        # Remove the selected enrollment row after confirmation.
        sel = self.enroll_tree.selection()
        if not sel:
            show_error(self.window, "No Selection", "Select an enrollment row to remove.")
            return

        row_vals    = self.enroll_tree.item(sel[0])["values"]
        student_name, subj_name = row_vals[0], row_vals[1]
        label = f"{student_name} from {subj_name}"

        if show_confirm(self.window, "Remove Enrollment",
                        f"Remove enrollment: {label}?"):
            try:
                # Parse student_id and subject_id directly from the iid (format: "student_id-subject_id").
                student_id, subject_id = map(int, sel[0].split("-"))
                self.db.unenroll_student(student_id, subject_id)
                
                self._load_enrollments()
                self._refresh_enroll_dropdowns()
                self._show_enroll_status(f"Removed: {label}", err=False)
            except Exception as exc:
                show_error(self.window, "Error", str(exc))

    def _show_enroll_status(self, msg, err: bool = False):
        # Display a temporary inline status message next to the enrollment buttons.
        self.enroll_status_lbl.configure(
            text=msg, fg=THEME["COLOR_DANGER"] if err else THEME["COLOR_SUCCESS"])
        self.window.after(4000, lambda: self.enroll_status_lbl.configure(text=""))

    # ── Subjects tab ──────────────────────────────────────────────

    def _build_subjects_tab(self, parent):
        # Subjects Treeview + Add-Subject form + Delete button.
        # ── Treeview ──
        cols   = ("ID", "Subject Name", "Code", "Credit Hours")
        widths = [60, 320, 140, 100]
        self.subj_tree = self._make_treeview(parent, cols, widths)
        self._load_subjects()

        # ── Add-subject form ──
        form = tk.Frame(parent, bg=CARD)
        form.pack(fill="x", padx=5, pady=(8, 4))

        tk.Label(form, text="Subject Name:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(10, 4), pady=10)
        self.subj_name_var = tk.StringVar()
        tk.Entry(form, textvariable=self.subj_name_var, width=28,
                 font=THEME["FONT_BODY"],
                 bg="#3A3A5E", fg=FG, insertbackground="white", relief="flat"
                 ).pack(side="left", ipady=4, padx=(0, 16))

        tk.Label(form, text="Code:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(0, 4))
        self.subj_code_var = tk.StringVar()
        tk.Entry(form, textvariable=self.subj_code_var, width=10,
                 font=THEME["FONT_BODY"],
                 bg="#3A3A5E", fg=FG, insertbackground="white", relief="flat"
                 ).pack(side="left", ipady=4, padx=(0, 10))

        tk.Label(form, text="CH:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(0, 4))
        self.subj_ch_var = tk.StringVar(value="3")
        tk.Entry(form, textvariable=self.subj_ch_var, width=4,
                 font=THEME["FONT_BODY"],
                 bg="#3A3A5E", fg=FG, insertbackground="white", relief="flat"
                 ).pack(side="left", ipady=4, padx=(0, 16))

        tk.Button(form, text="Add Subject",
                  command=self._add_subject,
                  font=THEME["FONT_BUTTON"],
                  bg=ACC, fg=FG, activebackground="#2563EB",
                  relief="flat", cursor="hand2", padx=12, pady=4
                  ).pack(side="left", padx=(0, 8))

        tk.Button(form, text="Delete Selected",
                  command=self._delete_subject,
                  font=THEME["FONT_BUTTON"],
                  bg=THEME["COLOR_DANGER"], fg=FG, activebackground="#DC2626",
                  relief="flat", cursor="hand2", padx=12, pady=4
                  ).pack(side="left")

        self.subj_status_lbl = tk.Label(form, text="",
                                        font=THEME["FONT_SMALL"], bg=CARD, fg=FG)
        self.subj_status_lbl.pack(side="left", padx=10)

        # ── Assign Teacher row ──
        assign_row = tk.Frame(parent, bg=CARD)
        assign_row.pack(fill="x", padx=5, pady=(0, 8))

        tk.Label(assign_row, text="Assign:", font=THEME["FONT_BODY"],
                 bg=CARD, fg=FG).pack(side="left", padx=(10, 6), pady=10)

        # Teacher combobox
        tk.Label(assign_row, text="Teacher", font=THEME["FONT_SMALL"],
                 bg=CARD, fg=THEME["COLOR_TEXT_MUTED"]).pack(side="left", padx=(0, 2))
        self.assign_teacher_var = tk.StringVar()
        self.assign_teacher_cb  = ttk.Combobox(assign_row,
                                               textvariable=self.assign_teacher_var,
                                               state="readonly",
                                               font=THEME["FONT_BODY"], width=22)
        self.assign_teacher_cb.pack(side="left", padx=(0, 10))

        tk.Label(assign_row, text="→  Subject", font=THEME["FONT_SMALL"],
                 bg=CARD, fg=THEME["COLOR_TEXT_MUTED"]).pack(side="left", padx=(0, 2))
        self.assign_subject_var = tk.StringVar()
        self.assign_subject_cb  = ttk.Combobox(assign_row,
                                               textvariable=self.assign_subject_var,
                                               state="readonly",
                                               font=THEME["FONT_BODY"], width=22)
        self.assign_subject_cb.pack(side="left", padx=(0, 10))

        tk.Button(assign_row, text="Assign",
                  command=self._assign_teacher_to_subject,
                  font=THEME["FONT_BUTTON"],
                  bg=THEME["COLOR_SUCCESS"], fg=FG, activebackground="#16A34A",
                  relief="flat", cursor="hand2", padx=12, pady=4
                  ).pack(side="left")

        self.assign_status_lbl = tk.Label(assign_row, text="",
                                          font=THEME["FONT_SMALL"], bg=CARD, fg=FG)
        self.assign_status_lbl.pack(side="left", padx=10)

        # Populate both assign dropdowns on first build.
        self._refresh_assign_dropdowns()

    def _load_subjects(self):
        # Fetch all subjects from the DB and populate the Treeview.
        self.subj_tree.delete(*self.subj_tree.get_children())
        for row in self.db.get_all_subjects():
            # row: (id, name, code, credit_hours)
            self.subj_tree.insert("", "end", iid=str(row[0]), values=row)

    def _add_subject(self):
        # Validate the form fields and insert a new subject row.
        name = self.subj_name_var.get().strip()
        code = self.subj_code_var.get().strip()
        ch_str = getattr(self, "subj_ch_var", tk.StringVar(value="3")).get().strip()

        if not name or not code or not ch_str:
            self._show_subj_status("Name, Code, and CH are required.", err=True)
            return
            
        try:
            ch = int(ch_str)
        except ValueError:
            self._show_subj_status("Credit hours must be a number.", err=True)
            return

        new_id = self.db.add_subject(name, code, ch)
        if new_id is None:
            self._show_subj_status("Failed — code may already exist.", err=True)
            return

        
        self.subj_name_var.set("")
        self.subj_code_var.set("")
        if hasattr(self, "subj_ch_var"):
            self.subj_ch_var.set("3")
        self._show_subj_status(f"Added: {name} ({code.upper()})", err=False)
        # Reload Treeview and all subject-dependent dropdowns across every tab.
        self._load_subjects()
        self._refresh_assign_dropdowns()
        self._refresh_asgn_dropdowns()
        self._refresh_enroll_dropdowns()

    def _delete_subject(self):
        # Confirm and delete the selected subject row.
        sel = self.subj_tree.selection()
        if not sel:
            show_error(self.window, "No Selection", "Select a subject to delete.")
            return
        subj_id  = int(sel[0])
        row_vals = self.subj_tree.item(sel[0])["values"]
        label    = f"{row_vals[1]} ({row_vals[2]})"
        if show_confirm(self.window, "Delete Subject",
                        f"Permanently delete '{label}'?\n"
                        f"All grades linked to this subject will also be removed."):
            try:
                self.db.delete_subject(subj_id)
                
                show_success(self.window, "Deleted", f"'{label}' removed.")
                # Refresh Treeview and all subject-dependent dropdowns across every tab.
                self._load_subjects()
                self._refresh_assign_dropdowns()
                self._refresh_asgn_dropdowns()
                self._refresh_enroll_dropdowns()
                self._load_enrollments()
                self._load_assignments()
            except Exception as exc:
                show_error(self.window, "Error", str(exc))

    def _show_subj_status(self, msg, err: bool = False):
        # Display a temporary feedback message next to the Add Subject button.
        self.subj_status_lbl.configure(
            text=msg, fg=THEME["COLOR_DANGER"] if err else THEME["COLOR_SUCCESS"])
        self.window.after(3500, lambda: self.subj_status_lbl.configure(text=""))

    def _refresh_assign_dropdowns(self):
        # Repopulate both Comboboxes in the Assign Teacher row from live DB data.
        # Teacher dropdown — all users with role='teacher'
        teachers = [(u[0], u[1]) for u in self.db.get_all_users() if u[3] == "teacher"]
        self._assign_teachers = teachers   # [(user_id, name), ...]
        self.assign_teacher_cb["values"] = [t[1] for t in teachers]
        if teachers:
            self.assign_teacher_cb.current(0)

        # Subject dropdown — all subjects
        subjects = self.db.get_all_subjects()
        self._assign_subjects = subjects   # [(id, name, code), ...]
        self.assign_subject_cb["values"] = [f"{s[1]} ({s[2]})" for s in subjects]
        if subjects:
            self.assign_subject_cb.current(0)

    def _assign_teacher_to_subject(self):
        # Read the two dropdowns and persist the assignment via the DB.
        if not self._assign_teachers or not self._assign_subjects:
            self._show_assign_status("No teachers or subjects available.", err=True)
            return

        # Resolve the selected teacher
        t_idx = self.assign_teacher_cb.current()
        if t_idx < 0:
            self._show_assign_status("Select a teacher.", err=True); return
        teacher_id, teacher_name = self._assign_teachers[t_idx]

        # Resolve the selected subject
        s_idx = self.assign_subject_cb.current()
        if s_idx < 0:
            self._show_assign_status("Select a subject.", err=True); return
        subject_id, subj_name, subj_code = self._assign_subjects[s_idx]

        try:
            self.db.assign_subject_to_teacher(teacher_id, subject_id)
            
            # Keep the Assignments tab Treeview in sync.
            self._load_assignments()
            self._refresh_asgn_dropdowns()
            self._show_assign_status(
                f"✔ {subj_name} assigned to {teacher_name}", err=False)
        except Exception as exc:
            self._show_assign_status(f"Error: {exc}", err=True)

    def _show_assign_status(self, msg, err: bool = False):
        # Temporary feedback label next to the Assign button.
        self.assign_status_lbl.configure(
            text=msg, fg=THEME["COLOR_DANGER"] if err else THEME["COLOR_SUCCESS"])
        self.window.after(4000, lambda: self.assign_status_lbl.configure(text=""))

    # ── Shared helpers ────────────────────────────────────────────

    def _delete_selected(self, tree: ttk.Treeview, kind):
        # Confirm and delete the currently selected row from the DB.
        sel = tree.selection()
        if not sel:
            show_error(self.window, "No Selection", f"Select a {kind} row to delete.")
            return
        user_id = int(sel[0])
        if user_id == self.admin.id:
            show_error(self.window, "Denied", "You cannot delete your own account.")
            return
        name_col = tree.item(sel[0])["values"][1]
        if show_confirm(self.window, f"Delete {kind.title()}",
                        f"Permanently delete '{name_col}' and all their data?"):
            try:
                self.db.delete_user(user_id)
                
                show_success(self.window, "Deleted", f"'{name_col}' removed.")
                # Reload whichever list changed and resync every dependent dropdown.
                if kind == "student":
                    self._load_students()
                    self._refresh_enroll_dropdowns()
                    self._load_enrollments()
                elif kind == "teacher":
                    self._load_teachers()
                    self._refresh_asgn_dropdowns()
                    self._refresh_assign_dropdowns()
                    self._load_assignments()
            except Exception as exc:
                show_error(self.window, "Error", str(exc))

    def _make_popup(self, title, width, height):
        # Create a centred, modal Toplevel window.
        popup = tk.Toplevel(self.window)
        popup.title(title)
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.grab_set()
        popup.focus()
        popup.update_idletasks()
        x = (popup.winfo_screenwidth()  // 2) - (width  // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        return popup

    # ── Navigation ────────────────────────────────────────────────

    def _logout(self):
        # Destroy window and return to login screen.
        self.window.destroy()
        from gui.login_screen import LoginScreen
        LoginScreen(self.db).render()

    def render(self):
        # Start the Tkinter event loop.
        self.window.mainloop()
