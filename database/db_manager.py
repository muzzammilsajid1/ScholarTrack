"""
Database manager for ScholarTrack — wraps all SQLite operations.

Usage:
    db = DatabaseManager("tracker.db")
    user = db.authenticate_user("alice_s", "pass123")
"""
import sqlite3
import hashlib
from models.exceptions import DatabaseError


class DatabaseManager:
    """Handles all SQLite database connections and queries for ScholarTrack.

    Encapsulates every SQL statement behind named methods so the GUI layer
    never has to write raw SQL (except for the two direct cursor calls in
    login_screen and admin_view which are noted below).
    """

    # ── Internal helpers ──────────────────────────────────────────

    # Hashes a plain-text password with SHA-256 before storing or comparing it.
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # Runs a SELECT and returns all matching rows as a list of tuples.
    def _fetch_all(self, query: str, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    # Runs a SELECT and returns the first matching row (or None).
    def _fetch_one(self, query: str, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    # Runs an INSERT / UPDATE / DELETE, commits, and returns the new row ID.
    def _execute(self, query: str, params=()):
        self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.lastrowid

    # Runs the same INSERT / UPDATE / DELETE for a list of param tuples in one shot.
    def _executemany(self, query: str, params_list):
        self.cursor.executemany(query, params_list)
        self.connection.commit()

    # ── Lifecycle ─────────────────────────────────────────────────

    def __init__(self, db_path: str = "tracker.db"):
        """Opens the database file, creates all tables, and seeds demo data."""
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.connect()
        self.initialize_tables()
        self.seed_dummy_data()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # Shows the database file path when the object is printed or inspected.
    def __str__(self) -> str:
        return f"DatabaseManager connected to {self.db_path}"

    def __repr__(self) -> str:
        state = "Open" if self.connection else "Closed"
        return f"<DatabaseManager db_path='{self.db_path}', state='{state}'>"

    # Prints every row in the five key tables — used for debugging enrollment issues.
    def debug_print_all(self):
        """Dump all rows from users, students, subjects, enrollments, teacher_subjects."""
        print("\n=== USERS ===")
        for row in self._fetch_all("SELECT * FROM users"):
            print(row)
        print("\n=== STUDENTS ===")
        for row in self._fetch_all("SELECT * FROM students"):
            print(row)
        print("\n=== SUBJECTS ===")
        for row in self._fetch_all("SELECT * FROM subjects"):
            print(row)
        print("\n=== ENROLLMENTS ===")
        for row in self._fetch_all("SELECT * FROM enrollments"):
            print(row)
        print("\n=== TEACHER_SUBJECTS ===")
        for row in self._fetch_all("SELECT * FROM teacher_subjects"):
            print(row)
        print()

    # Opens the SQLite connection and enables foreign-key enforcement.
    def connect(self):
        """Establishes the SQLite connection and enables foreign-key support."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print(f"[DB Error] Connection failed: {e}")
            from models.exceptions import DatabaseError
            raise DatabaseError(f"Could not connect to {self.db_path}: {e}")

    # Safely closes the connection when the application shuts down.
    def close(self):
        """Closes the SQLite connection if one is open."""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
            except sqlite3.Error as e:
                print(f"[DB Error] Error closing DB: {e}")

    # ── Schema setup ──────────────────────────────────────────────

    # Creates all six tables if they don't already exist (safe to call on every startup).
    def initialize_tables(self):
        """Creates the users, subjects, students, grades, activity_log, and
        attendance tables if they do not already exist."""
        try:
            self._execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            ''')
            self._execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    code TEXT UNIQUE NOT NULL,
                    credit_hours INTEGER DEFAULT 3
                )
            ''')
            self._execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    semester INTEGER,
                    department TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            self._execute('''
                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    score REAL,
                    grade_letter TEXT,
                    semester INTEGER,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY(subject_id) REFERENCES subjects(id)
                )
            ''')
            self._execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    target TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            self._execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late')),
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY(subject_id) REFERENCES subjects(id)
                )
            ''')
            self._execute('''
                CREATE TABLE IF NOT EXISTS teacher_subjects (
                    teacher_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    PRIMARY KEY (teacher_id, subject_id),
                    FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                )
            ''')
            self._execute('''
                CREATE TABLE IF NOT EXISTS enrollments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    UNIQUE(student_id, subject_id),
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                )
            ''')
        except sqlite3.Error as e:
            print(f"[DB Error] Error initializing tables: {e}")

    # Populates the database with demo users, subjects, students, and grades
    # the first time the app is run (skipped if the users table is already populated).
    def seed_dummy_data(self):
        """Inserts demo data on first launch so the app is immediately usable."""
        try:
            row = self._fetch_one("SELECT COUNT(*) FROM users")
            if row and row[0] == 0:
                hashed_pass = self._hash_password("pass123")
                admin_pass  = self._hash_password("admin123")

                users_data = [
                    ("Taha Amjad",     "taha_a",    hashed_pass, "student"),
                    ("Ibrahim Hafeez", "ibrahim_h", hashed_pass, "student"),
                    ("Huzaifa Khan",   "huzaifa_k", hashed_pass, "student"),
                    ("Mohsin Shah",    "mohsin_s",  hashed_pass, "teacher"),
                    ("Anwar Abbas",    "anwar_a",   hashed_pass, "teacher"),
                    ("Admin User",     "admin",     admin_pass,  "admin"),
                ]
                self._executemany(
                    "INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)",
                    users_data)

                subjects_data = [
                    ("Calculus",       "MT101", 3),
                    ("Stats",          "ES111", 3),
                    ("Materials",      "MM101", 2),
                    ("Communications", "HM101", 1),
                ]
                self._executemany(
                    "INSERT INTO subjects (name, code, credit_hours) VALUES (?, ?, ?)",
                    subjects_data)

                students_data = [
                    (1, 1, "Software Engineering"),
                    (2, 1, "Mechanical Engineering"),
                    (3, 1, "Computer Science"),
                ]
                self._executemany(
                    "INSERT INTO students (user_id, semester, department) VALUES (?, ?, ?)",
                    students_data)

                grades_data = [
                    (1, 1, 1),
                    (2, 1, 1),
                    (2, 2, 1),
                    (3, 2, 1),
                    (1, 3, 1),
                    (3, 4, 1),
                ]
                self._executemany(
                    "INSERT INTO grades (student_id, subject_id, semester) VALUES (?, ?, ?)",
                    grades_data)
                
                enrollments_data = [
                    (1, 1),  # taha -> MT101
                    (2, 1),  # ibrahim -> MT101
                    (2, 2),  # ibrahim -> ES111
                    (3, 2),  # huzaifa -> ES111
                    (1, 3),  # taha -> MM101
                    (3, 4),  # huzaifa -> HM101
                ]
                self._executemany(
                    "INSERT OR IGNORE INTO enrollments (student_id, subject_id) VALUES (?, ?)",
                    enrollments_data)

                teacher_subjects_data = [
                    (4, 1),  # mohsin -> MT101
                    (4, 2),  # mohsin -> ES111
                    (5, 3),  # anwar -> MM101
                    (5, 4),  # anwar -> HM101
                ]
                self._executemany(
                    "INSERT OR IGNORE INTO teacher_subjects (teacher_id, subject_id) VALUES (?, ?)",
                    teacher_subjects_data)

                # Confirm seeded data is queryable on first launch.
                print("[Seed] Enrolled students in MT101 (subject 1):",
                      self.get_students_in_subject(1))
        except sqlite3.Error as e:
            print(f"[DB Error] Error seeding dummy data: {e}")

    # ── Authentication ────────────────────────────────────────────

    # Checks the username and hashed password; returns the matching user row or None.
    def authenticate_user(self, username: str, password: str):
        """Looks up a user by username and password; returns the DB row or None."""
        try:
            hashed = self._hash_password(password)
            return self._fetch_one(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, hashed))
        except sqlite3.Error as e:
            print(f"[DB Error] authenticate_user failed: {e}")
            return None

    # ── User queries ──────────────────────────────────────────────

    # Returns every user row joined with their student details (used by admin tab).
    def get_all_users(self) -> list:
        """Returns all users with optional student-specific fields (semester, dept)."""
        try:
            return self._fetch_all('''
                SELECT u.id, u.name, u.username, u.role,
                       s.id AS student_id, s.semester, s.department
                FROM users u
                LEFT JOIN students s ON u.id = s.user_id
                ORDER BY u.id
            ''')
        except sqlite3.Error as e:
            print(f"[DB Error] get_all_users failed: {e}")
            return []

    # Removes a user by their user ID — CASCADE deletes their student/grade records too.
    def delete_user(self, user_id: int):
        """Deletes a user and all their related records via CASCADE."""
        try:
            self._execute("DELETE FROM users WHERE id = ?", (user_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] delete_user failed: {e}")
            raise e

    # ── Student queries ───────────────────────────────────────────

    # Returns every student row joined with their user name and username.
    def get_all_students(self) -> list:
        """Returns all students as tuples: (student_id, name, username, semester, dept)."""
        try:
            return self._fetch_all('''
                SELECT s.id, u.name, u.username, s.semester, s.department
                FROM students s
                JOIN users u ON s.user_id = u.id
            ''')
        except sqlite3.Error as e:
            print(f"[DB Error] get_all_students failed: {e}")
            return []

    # Creates a new user row with role='student' and a matching students row.
    def add_student(self, name: str, username: str, password: str,
                    semester: int, department: str) -> int | None:
        """Inserts a new student into users and students tables; returns the new user ID."""
        try:
            hashed = self._hash_password(password)
            user_id = self._execute(
                "INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)",
                (name, username, hashed, "student"))
            self._execute(
                "INSERT INTO students (user_id, semester, department) VALUES (?, ?, ?)",
                (user_id, semester, department))
            return user_id
        except sqlite3.Error as e:
            print(f"[DB Error] add_student failed: {e}")
            return None

    # Calculates the GPA for a student from their grade_letter values (A=4, B=3 …).
    def get_student_gpa(self, student_id: int) -> float:
        """Computes and returns the cumulative GPA for a student (0.0–4.0 scale)."""
        try:
            rows = self._fetch_all(
                "SELECT grade_letter FROM grades WHERE student_id = ?",
                (student_id,))
            letters = [r[0] for r in rows if r[0]]
            if not letters:
                return 0.0
            gpa_map = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
            total = sum(gpa_map.get(g.upper(), 0.0) for g in letters)
            return round(total / len(letters), 2)
        except sqlite3.Error as e:
            print(f"[DB Error] get_student_gpa failed: {e}")
            return 0.0

    # ── Teacher queries ───────────────────────────────────────────

    # Creates a new user row with role='teacher'; returns the new user ID or None on failure.
    def add_teacher(self, name: str, username: str, password: str) -> int | None:
        """Inserts a new teacher into the users table; returns the new user ID."""
        try:
            hashed = self._hash_password(password)
            return self._execute(
                "INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)",
                (name, username, hashed, "teacher"))
        except sqlite3.Error as e:
            print(f"[DB Error] add_teacher failed: {e}")
            return None

    # ── Subject queries ───────────────────────────────────────────

    # Returns every row in the subjects table as (id, name, code) tuples.
    def get_all_subjects(self) -> list:
        """Returns all subjects as tuples: (subject_id, name, code, credit_hours)."""
        try:
            return self._fetch_all("SELECT id, name, code, credit_hours FROM subjects")
        except sqlite3.Error as e:
            print(f"[DB Error] get_all_subjects failed: {e}")
            return []

    # ── Enrollment queries ────────────────────────────────────────

    # Enrolls a student in a subject; silently ignores if they are already enrolled.
    def enroll_student(self, student_id: int, subject_id: int) -> bool:
        """Inserts an enrollment row and a blank grade row; returns True on success."""
        try:
            self._execute(
                "INSERT OR IGNORE INTO enrollments (student_id, subject_id) VALUES (?, ?)",
                (student_id, subject_id))
            if self.cursor.rowcount > 0:
                row = self._fetch_one("SELECT semester FROM students WHERE id = ?", (student_id,))
                sem = row[0] if row else 1
                self._execute(
                    "INSERT INTO grades (student_id, subject_id, semester) VALUES (?, ?, ?)",
                    (student_id, subject_id, sem))
                return True
            return False
        except sqlite3.Error as e:
            print(f"[DB Error] enroll_student failed: {e}")
            return False

    # Removes a student's enrollment in a subject.
    def unenroll_student(self, student_id: int, subject_id: int):
        """Deletes the enrollment row for the given student and subject."""
        try:
            self._execute(
                "DELETE FROM enrollments WHERE student_id = ? AND subject_id = ?",
                (student_id, subject_id))
        except sqlite3.Error as e:
            print(f"[DB Error] unenroll_student failed: {e}")
            raise e

    # Returns all students enrolled in a given subject, joined to their user names.
    def get_students_in_subject(self, subject_id: int) -> list:
        """Returns enrolled students as tuples: (student_id, name, username, semester, dept)."""
        try:
            return self._fetch_all('''
                SELECT s.id, u.name, u.username, s.semester, s.department
                FROM enrollments e
                JOIN students s ON e.student_id = s.id
                JOIN users u ON s.user_id = u.id
                WHERE e.subject_id = ?
                ORDER BY u.name
            ''', (subject_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] get_students_in_subject failed: {e}")
            return []

    # Returns all subjects a given student is enrolled in.
    def get_subjects_for_student(self, student_id: int) -> list:
        """Returns enrolled subjects as tuples: (subject_id, name, code)."""
        try:
            return self._fetch_all('''
                SELECT s.id, s.name, s.code
                FROM enrollments e
                JOIN subjects s ON e.subject_id = s.id
                WHERE e.student_id = ?
                ORDER BY s.name
            ''', (student_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] get_subjects_for_student failed: {e}")
            return []

    # Links one teacher to one subject in the junction table.
    def assign_subject_to_teacher(self, teacher_id: int, subject_id: int):
        """Assigns a subject to a teacher using INSERT OR REPLACE (handles reassignment)."""
        try:
            self._execute(
                "INSERT OR REPLACE INTO teacher_subjects (teacher_id, subject_id) VALUES (?, ?)",
                (teacher_id, subject_id))
        except sqlite3.Error as e:
            print(f"[DB Error] assign_subject_to_teacher failed: {e}")
            raise e

    # Removes a teacher–subject assignment from the junction table.
    def unassign_subject_from_teacher(self, teacher_id: int, subject_id: int):
        """Deletes the assignment row so the teacher can no longer manage that subject."""
        try:
            self._execute(
                "DELETE FROM teacher_subjects WHERE teacher_id = ? AND subject_id = ?",
                (teacher_id, subject_id))
        except sqlite3.Error as e:
            print(f"[DB Error] unassign_subject_from_teacher failed: {e}")
            raise e

    # Returns all current teacher–subject assignments joined with names (for admin Treeview).
    def get_all_assignments(self) -> list:
        """Returns all assignments as tuples: (teacher_name, subject_name, subject_code)."""
        try:
            return self._fetch_all('''
                SELECT u.name AS teacher_name, s.name AS subject_name, s.code,
                       ts.teacher_id, ts.subject_id
                FROM teacher_subjects ts
                JOIN users u ON ts.teacher_id = u.id
                JOIN subjects s ON ts.subject_id = s.id
                ORDER BY u.name, s.name
            ''')
        except sqlite3.Error as e:
            print(f"[DB Error] get_all_assignments failed: {e}")
            return []

    # Returns only the subjects that have been assigned to a specific teacher.
    def get_teacher_subjects(self, teacher_id: int) -> list:
        """Returns subjects assigned to a teacher as tuples: (subject_id, name, code)."""
        try:
            return self._fetch_all('''
                SELECT s.id, s.name, s.code
                FROM subjects s
                JOIN teacher_subjects ts ON s.id = ts.subject_id
                WHERE ts.teacher_id = ?
                ORDER BY s.name
            ''', (teacher_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] get_teacher_subjects failed: {e}")
            return []

    # Returns the teacher user row assigned to a subject, or None if unassigned.
    def get_subject_teacher(self, subject_id: int):
        """Returns (user_id, name) of the teacher assigned to a subject, or None."""
        try:
            return self._fetch_one('''
                SELECT u.id, u.name
                FROM users u
                JOIN teacher_subjects ts ON u.id = ts.teacher_id
                WHERE ts.subject_id = ?
            ''', (subject_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] get_subject_teacher failed: {e}")
            return None

    # Returns students enrolled in subjects that are assigned to this teacher.
    # Returns an empty list (not a fallback) when the teacher has no assignments.
    def get_students_for_teacher(self, teacher_id: int) -> list:
        """Returns students enrolled in the teacher's assigned subjects.

        Returns an empty list when the teacher has no subject assignments —
        the caller (teacher_view) shows a 'no subjects' message in that case.
        """
        try:
            return self._fetch_all('''
                SELECT DISTINCT s.id, u.name, u.username, s.semester, s.department
                FROM students s
                JOIN users u ON s.user_id = u.id
                JOIN enrollments e ON e.student_id = s.id
                JOIN teacher_subjects ts ON e.subject_id = ts.subject_id
                WHERE ts.teacher_id = ?
                ORDER BY u.name
            ''', (teacher_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] get_students_for_teacher failed: {e}")
            return []

    # Inserts a new row into subjects and returns the new primary key.
    def add_subject(self, name: str, code: str, credit_hours: int) -> int | None:
        """Inserts a new subject with the given name, code, and CH; returns the new subject ID."""
        try:
            return self._execute(
                "INSERT INTO subjects (name, code, credit_hours) VALUES (?, ?, ?)",
                (name.strip(), code.strip().upper(), credit_hours))
        except sqlite3.Error as e:
            print(f"[DB Error] add_subject failed: {e}")
            return None

    # Permanently removes a subject row — grades referencing it are also removed via CASCADE.
    def delete_subject(self, subject_id: int):
        """Deletes a subject by its ID (grades referencing it are removed by CASCADE)."""
        try:
            self._execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] delete_subject failed: {e}")
            raise e

    # ── Grade queries ─────────────────────────────────────────────

    # Returns all grade rows for a student, joined to the matching subject name and code.
    def get_student_grades(self, student_id: int, teacher_id: int = None) -> list:
        """Returns grade rows for a student. If teacher_id is provided, filters by subjects they teach."""
        try:
            if teacher_id is not None:
                return self._fetch_all('''
                    SELECT g.id, su.name, su.code, g.score, g.grade_letter, g.semester
                    FROM grades g
                    JOIN subjects su ON g.subject_id = su.id
                    JOIN teacher_subjects ts ON su.id = ts.subject_id
                    WHERE g.student_id = ? AND ts.teacher_id = ?
                ''', (student_id, teacher_id))
            return self._fetch_all('''
                SELECT g.id, su.name, su.code, g.score, g.grade_letter, g.semester
                FROM grades g
                JOIN subjects su ON g.subject_id = su.id
                WHERE g.student_id = ?
            ''', (student_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] get_student_grades failed: {e}")
            return []

    # Saves a new numeric score and letter grade for an existing grade row.
    def update_grade(self, grade_id: int, score: float, grade_letter: str):
        """Updates the score and letter grade for an existing grade record."""
        try:
            self._execute(
                "UPDATE grades SET score = ?, grade_letter = ? WHERE id = ?",
                (score, grade_letter, grade_id))
        except sqlite3.Error as e:
            print(f"[DB Error] update_grade failed: {e}")

    # ── Activity log ──────────────────────────────────────────────

    # Writes one line to the activity_log table recording who did what to whom.
    def log_action(self, user_id: int, action: str, target: str = None):
        """Inserts an entry into the activity_log (user_id, action string, optional target)."""
        try:
            self._execute(
                "INSERT INTO activity_log (user_id, action, target) VALUES (?, ?, ?)",
                (user_id, action, target))
        except sqlite3.Error as e:
            print(f"[DB Error] log_action failed: {e}")

    # Returns the N most recent activity log entries, newest first.
    def get_recent_activity(self, limit: int = 8) -> list:
        """Returns up to `limit` recent log entries as (action, target, timestamp) tuples."""
        try:
            return self._fetch_all('''
                SELECT action, target, timestamp
                FROM activity_log
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        except sqlite3.Error as e:
            print(f"[DB Error] get_recent_activity failed: {e}")
            return []

    # ── Attendance ────────────────────────────────────────────────

    # Inserts or replaces an attendance record for one student for a given subject and date.
    def mark_attendance(self, student_id: int, subject_id: int,
                        date: str, status: str):
        """Saves attendance for one student (INSERT OR REPLACE so re-submitting the same
        day updates instead of duplicating).  status must be 'Present', 'Absent', or 'Late'."""
        try:
            self._execute('''
                INSERT OR REPLACE INTO attendance (student_id, subject_id, date, status)
                VALUES (?, ?, ?, ?)
            ''', (student_id, subject_id, date, status))
        except sqlite3.Error as e:
            print(f"[DB Error] mark_attendance failed: {e}")

    # Returns all attendance rows for a single student, newest date first.
    def get_student_attendance(self, student_id: int) -> list:
        """Returns attendance history for a student: (id, subj_name, code, date, status)."""
        try:
            return self._fetch_all('''
                SELECT a.id, su.name, su.code, a.date, a.status
                FROM attendance a
                JOIN subjects su ON a.subject_id = su.id
                WHERE a.student_id = ?
                ORDER BY a.date DESC
            ''', (student_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] get_student_attendance failed: {e}")
            return []

    # Counts how many classes a student attended, was absent from, and was late to.
    def get_attendance_summary(self, student_id: int) -> dict:
        """Returns a summary dict: {total, present, absent, late, percentage}."""
        try:
            rows = self._fetch_all(
                "SELECT status FROM attendance WHERE student_id = ?",
                (student_id,))
            total   = len(rows)
            present = sum(1 for r in rows if r[0] == "Present")
            absent  = sum(1 for r in rows if r[0] == "Absent")
            late    = sum(1 for r in rows if r[0] == "Late")
            pct     = round((present / total) * 100, 1) if total else 0.0
            return {"total": total, "present": present,
                    "absent": absent, "late": late, "percentage": pct}
        except sqlite3.Error as e:
            print(f"[DB Error] get_attendance_summary failed: {e}")
            return {"total": 0, "present": 0, "absent": 0, "late": 0, "percentage": 0.0}

    # Permanently removes one attendance record by its primary key.
    def delete_attendance(self, attendance_id: int):
        """Deletes a single attendance record by its ID."""
        try:
            self._execute("DELETE FROM attendance WHERE id = ?", (attendance_id,))
        except sqlite3.Error as e:
            print(f"[DB Error] delete_attendance failed: {e}")
            raise e
