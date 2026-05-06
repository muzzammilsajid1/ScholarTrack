# storage/file_manager.py — ScholarTrack LMS
# 
# Drop-in JSON replacement for database/db_manager.py.
# Every public method signature is identical to DatabaseManager so the
# rest of the codebase needs no changes beyond swapping the import.
# 
# Data is stored in six JSON files inside the  data/  folder:
#     data/users.json
#     data/students.json
#     data/subjects.json
#     data/grades.json
#     data/enrollments.json
#     data/attendance.json
#     data/activity_log.json
#     data/teacher_subjects.json
# 
# Each file holds a list of dicts.  Auto-incrementing IDs are tracked by
# a separate  data/meta.json  file that stores the next available ID for
# every collection.

import os
import json
import hashlib
from datetime import datetime


# ── Path helpers ──────────────────────────────────────────────────────────────

_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

_FILES = {
    "users":           "users.json",
    "students":        "students.json",
    "subjects":        "subjects.json",
    "grades":          "grades.json",
    "enrollments":     "enrollments.json",
    "attendance":      "attendance.json",
    "activity_log":    "activity_log.json",
    "teacher_subjects": "teacher_subjects.json",
    "meta":            "meta.json",
}


def _path(key):
    return os.path.join(_BASE_DIR, _FILES[key])


# ── Low-level JSON I/O ────────────────────────────────────────────────────────

def _read(key):
    p = _path(key)
    if not os.path.exists(p):
        return []
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _write(key, data):
    with open(_path(key), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _read_meta():
    p = _path("meta")
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_meta(meta):
    with open(_path("meta"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def _next_id(collection):
    # Return the next auto-increment ID for a collection and advance the counter.
    meta = _read_meta()
    nid = meta.get(collection, 1)
    meta[collection] = nid + 1
    _write_meta(meta)
    return nid


# ── FileManager ───────────────────────────────────────────────────────────────


class FileManager:
    # JSON-file storage backend with the same public API as DatabaseManager.

    # ── Lifecycle ─────────────────────────────────────────────────

    def __init__(self, data_dir=None):
        # Ensure data directory and JSON files exist, then seed if empty.
        global _BASE_DIR
        if data_dir:
            _BASE_DIR = data_dir
        os.makedirs(_BASE_DIR, exist_ok=True)
        # Touch every file so reads always succeed.
        for key in _FILES:
            p = _path(key)
            if not os.path.exists(p):
                if key == "meta":
                    _write_meta({})
                else:
                    _write(key, [])
        self.seed_dummy_data()

    def close(self):
        # No-op — JSON files are opened and closed per operation.
        pass

    def connect(self):
        # No-op — included for API compatibility with DatabaseManager.
        pass

    def initialize_tables(self):
        # No-op — JSON files are already created in __init__.
        pass

    # ── Internal helpers ──────────────────────────────────────────

    def _hash_password(self, password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # Provided so GradeService (which calls self.db._fetch_all) still works.
    def _fetch_all(self, query, params=()):
        # Not used internally — kept for compatibility with GradeService calls.
        return []

    def _fetch_one(self, query, params=()):
        # Not used internally — kept for compatibility with login_screen calls.
        return None

    # ── Debug ─────────────────────────────────────────────────────

    def debug_print_all(self):
        # Print every record in all collections.
        for key in ("users", "students", "subjects", "enrollments", "teacher_subjects"):
            print(f"\n=== {key.upper()} ===")
            for row in _read(key):
                print(row)
        print()

    # ── Seeding ───────────────────────────────────────────────────

    def seed_dummy_data(self):
        # Insert demo data on first launch (skipped if users.json is non-empty).
        if _read("users"):
            return  # Already seeded.

        hashed_pass = self._hash_password("pass123")
        admin_pass  = self._hash_password("admin123")

        # Users
        users_seed = [
            {"name": "Taha Amjad",     "username": "taha_a",    "password": hashed_pass, "role": "student"},
            {"name": "Ibrahim Hafeez", "username": "ibrahim_h", "password": hashed_pass, "role": "student"},
            {"name": "Huzaifa Khan",   "username": "huzaifa_k", "password": hashed_pass, "role": "student"},
            {"name": "Mohsin Shah",    "username": "mohsin_s",  "password": hashed_pass, "role": "teacher"},
            {"name": "Anwar Abbas",    "username": "anwar_a",   "password": hashed_pass, "role": "teacher"},
            {"name": "Admin User",     "username": "admin",     "password": admin_pass,  "role": "admin"},
        ]
        users = []
        for u in users_seed:
            u["id"] = _next_id("users")
            users.append(u)
        _write("users", users)

        # Subjects
        subjects_seed = [
            {"name": "Calculus",       "code": "MT101", "credit_hours": 3},
            {"name": "Stats",          "code": "ES111", "credit_hours": 3},
            {"name": "Materials",      "code": "MM101", "credit_hours": 2},
            {"name": "Communications", "code": "HM101", "credit_hours": 1},
        ]
        subjects = []
        for s in subjects_seed:
            s["id"] = _next_id("subjects")
            subjects.append(s)
        _write("subjects", subjects)

        # Students (user_id matches insertion order above: 1=taha, 2=ibrahim, 3=huzaifa)
        students_seed = [
            {"user_id": 1, "semester": 1, "department": "Software Engineering"},
            {"user_id": 2, "semester": 1, "department": "Mechanical Engineering"},
            {"user_id": 3, "semester": 1, "department": "Computer Science"},
        ]
        students = []
        for st in students_seed:
            st["id"] = _next_id("students")
            students.append(st)
        _write("students", students)

        # Enrollments and blank grades
        enrollments_seed = [
            (1, 1), (2, 1), (2, 2), (3, 2), (1, 3), (3, 4),
        ]
        enrollments = []
        grades = []
        for student_id, subject_id in enrollments_seed:
            eid = _next_id("enrollments")
            enrollments.append({"id": eid, "student_id": student_id, "subject_id": subject_id})
            gid = _next_id("grades")
            grades.append({"id": gid, "student_id": student_id, "subject_id": subject_id,
                           "score": None, "grade_letter": None, "semester": 1})
        _write("enrollments", enrollments)
        _write("grades", grades)

        # Teacher–subject assignments (teacher user_id: mohsin=4, anwar=5)
        ts_seed = [(4, 1), (4, 2), (5, 3), (5, 4)]
        teacher_subjects = [{"teacher_id": t, "subject_id": s} for t, s in ts_seed]
        _write("teacher_subjects", teacher_subjects)

        print("[Seed] Enrolled students in MT101 (subject 1):",
              self.get_students_in_subject(1))

    # ── Authentication ────────────────────────────────────────────

    def authenticate_user(self, username, password):
        # Return the matching user tuple (id, name, username, password, role) or None.
        hashed = self._hash_password(password)
        for u in _read("users"):
            if u["username"] == username and u["password"] == hashed:
                return (u["id"], u["name"], u["username"], u["password"], u["role"])
        return None

    # ── User queries ──────────────────────────────────────────────

    def get_all_users(self):
        # Returns tuples: (user_id, name, username, role, student_id, semester, dept).
        users    = _read("users")
        students = _read("students")
        s_by_uid = {s["user_id"]: s for s in students}
        result = []
        for u in sorted(users, key=lambda x: x["id"]):
            s = s_by_uid.get(u["id"])
            result.append((
                u["id"], u["name"], u["username"], u["role"],
                s["id"] if s else None,
                s["semester"] if s else None,
                s["department"] if s else None,
            ))
        return result

    def delete_user(self, user_id):
        # Delete a user and all cascading records (student, grades, enrollments, etc.).
        users = [u for u in _read("users") if u["id"] != user_id]
        _write("users", users)

        # Find student record for cascade.
        students = _read("students")
        student_ids = [s["id"] for s in students if s["user_id"] == user_id]
        students = [s for s in students if s["user_id"] != user_id]
        _write("students", students)

        for sid in student_ids:
            enrollments = [e for e in _read("enrollments") if e["student_id"] != sid]
            _write("enrollments", enrollments)
            grades = [g for g in _read("grades") if g["student_id"] != sid]
            _write("grades", grades)
            attendance = [a for a in _read("attendance") if a["student_id"] != sid]
            _write("attendance", attendance)

        # If teacher, remove teacher_subjects.
        ts = [t for t in _read("teacher_subjects") if t["teacher_id"] != user_id]
        _write("teacher_subjects", ts)

    # ── Student queries ───────────────────────────────────────────

    def get_all_students(self):
        # Returns tuples: (student_id, name, username, semester, dept).
        students = _read("students")
        users    = {u["id"]: u for u in _read("users")}
        result = []
        for s in students:
            u = users.get(s["user_id"])
            if u:
                result.append((s["id"], u["name"], u["username"], s["semester"], s["department"]))
        return result

    def add_student(self, name, username, password, semester, department):
        # Insert a new student; returns the new user_id or None on failure.
        try:
            users = _read("users")
            if any(u["username"] == username for u in users):
                return None
            hashed  = self._hash_password(password)
            user_id = _next_id("users")
            users.append({"id": user_id, "name": name, "username": username,
                          "password": hashed, "role": "student"})
            _write("users", users)

            students = _read("students")
            s_id = _next_id("students")
            students.append({"id": s_id, "user_id": user_id,
                             "semester": semester, "department": department})
            _write("students", students)
            return user_id
        except Exception as e:
            print(f"[FM Error] add_student failed: {e}")
            return None

    def get_student_gpa(self, student_id):
        # Compute cumulative GPA for a student from their grade_letter values.
        grades  = [g for g in _read("grades") if g["student_id"] == student_id]
        letters = [g["grade_letter"] for g in grades if g.get("grade_letter")]
        if not letters:
            return 0.0
        gpa_map = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
        total = sum(gpa_map.get(l.upper(), 0.0) for l in letters)
        return round(total / len(letters), 2)

    # ── Teacher queries ───────────────────────────────────────────

    def add_teacher(self, name, username, password):
        # Insert a new teacher user; returns the new user_id or None.
        try:
            users = _read("users")
            if any(u["username"] == username for u in users):
                return None
            hashed  = self._hash_password(password)
            user_id = _next_id("users")
            users.append({"id": user_id, "name": name, "username": username,
                          "password": hashed, "role": "teacher"})
            _write("users", users)
            return user_id
        except Exception as e:
            print(f"[FM Error] add_teacher failed: {e}")
            return None

    # ── Subject queries ───────────────────────────────────────────

    def get_all_subjects(self):
        # Returns tuples: (subject_id, name, code, credit_hours).
        return [(s["id"], s["name"], s["code"], s["credit_hours"])
                for s in _read("subjects")]

    def add_subject(self, name, code, credit_hours):
        # Insert a new subject; returns the new subject_id or None on duplicate code.
        subjects = _read("subjects")
        code = code.strip().upper()
        if any(s["code"] == code for s in subjects):
            return None
        sid = _next_id("subjects")
        subjects.append({"id": sid, "name": name.strip(),
                         "code": code, "credit_hours": credit_hours})
        _write("subjects", subjects)
        return sid

    def delete_subject(self, subject_id):
        # Delete a subject and cascade to grades, enrollments, teacher_subjects, attendance.
        subjects = [s for s in _read("subjects") if s["id"] != subject_id]
        _write("subjects", subjects)
        _write("grades",       [g for g in _read("grades")       if g["subject_id"] != subject_id])
        _write("enrollments",  [e for e in _read("enrollments")  if e["subject_id"] != subject_id])
        _write("teacher_subjects", [t for t in _read("teacher_subjects") if t["subject_id"] != subject_id])
        _write("attendance",   [a for a in _read("attendance")   if a["subject_id"] != subject_id])

    # ── Enrollment queries ────────────────────────────────────────

    def enroll_student(self, student_id, subject_id):
        # Enroll a student; also creates a blank grade row. Returns True on success.
        enrollments = _read("enrollments")
        if any(e["student_id"] == student_id and e["subject_id"] == subject_id
               for e in enrollments):
            return False
        eid = _next_id("enrollments")
        enrollments.append({"id": eid, "student_id": student_id, "subject_id": subject_id})
        _write("enrollments", enrollments)

        students = _read("students")
        sem = next((s["semester"] for s in students if s["id"] == student_id), 1)
        grades = _read("grades")
        gid = _next_id("grades")
        grades.append({"id": gid, "student_id": student_id, "subject_id": subject_id,
                       "score": None, "grade_letter": None, "semester": sem})
        _write("grades", grades)
        return True

    def unenroll_student(self, student_id, subject_id):
        # Remove an enrollment row.
        enrollments = [e for e in _read("enrollments")
                       if not (e["student_id"] == student_id and e["subject_id"] == subject_id)]
        _write("enrollments", enrollments)

    def get_students_in_subject(self, subject_id):
        # Returns tuples (student_id, name, username, semester, dept) sorted by name.
        enrolled_ids = {e["student_id"] for e in _read("enrollments")
                        if e["subject_id"] == subject_id}
        students = {s["id"]: s for s in _read("students")}
        users    = {u["id"]: u for u in _read("users")}
        result = []
        for sid in enrolled_ids:
            s = students.get(sid)
            if not s:
                continue
            u = users.get(s["user_id"])
            if u:
                result.append((s["id"], u["name"], u["username"],
                               s["semester"], s["department"]))
        return sorted(result, key=lambda x: x[1])

    def get_subjects_for_student(self, student_id):
        # Returns tuples (subject_id, name, code) sorted by name.
        enrolled_ids = {e["subject_id"] for e in _read("enrollments")
                        if e["student_id"] == student_id}
        subjects = {s["id"]: s for s in _read("subjects")}
        result = [(subjects[sid]["id"], subjects[sid]["name"], subjects[sid]["code"])
                  for sid in enrolled_ids if sid in subjects]
        return sorted(result, key=lambda x: x[1])

    # ── Teacher–subject assignments ───────────────────────────────

    def assign_subject_to_teacher(self, teacher_id, subject_id):
        # Assign a subject to a teacher (idempotent — replaces any existing row).
        ts = [t for t in _read("teacher_subjects")
              if not (t["teacher_id"] == teacher_id and t["subject_id"] == subject_id)]
        ts.append({"teacher_id": teacher_id, "subject_id": subject_id})
        _write("teacher_subjects", ts)

    def unassign_subject_from_teacher(self, teacher_id, subject_id):
        # Remove a teacher–subject assignment.
        ts = [t for t in _read("teacher_subjects")
              if not (t["teacher_id"] == teacher_id and t["subject_id"] == subject_id)]
        _write("teacher_subjects", ts)

    def get_all_assignments(self):
        # Returns tuples (teacher_name, subject_name, code, teacher_id, subject_id).
        users    = {u["id"]: u for u in _read("users")}
        subjects = {s["id"]: s for s in _read("subjects")}
        result = []
        for t in _read("teacher_subjects"):
            u = users.get(t["teacher_id"])
            s = subjects.get(t["subject_id"])
            if u and s:
                result.append((u["name"], s["name"], s["code"],
                               t["teacher_id"], t["subject_id"]))
        return sorted(result, key=lambda x: (x[0], x[1]))

    def get_teacher_subjects(self, teacher_id):
        # Returns tuples (subject_id, name, code) for subjects assigned to a teacher.
        subjects = {s["id"]: s for s in _read("subjects")}
        result = []
        for t in _read("teacher_subjects"):
            if t["teacher_id"] == teacher_id:
                s = subjects.get(t["subject_id"])
                if s:
                    result.append((s["id"], s["name"], s["code"]))
        return sorted(result, key=lambda x: x[1])

    def get_subject_teacher(self, subject_id):
        # Returns (user_id, name) of the teacher assigned to a subject, or None.
        users = {u["id"]: u for u in _read("users")}
        for t in _read("teacher_subjects"):
            if t["subject_id"] == subject_id:
                u = users.get(t["teacher_id"])
                if u:
                    return (u["id"], u["name"])
        return None

    def get_students_for_teacher(self, teacher_id):
        # Returns distinct (student_id, name, username, semester, dept) for students
        # enrolled in any subject taught by this teacher.
        my_subjects = {t["subject_id"] for t in _read("teacher_subjects")
                       if t["teacher_id"] == teacher_id}
        if not my_subjects:
            return []
        my_student_ids = {e["student_id"] for e in _read("enrollments")
                          if e["subject_id"] in my_subjects}
        students = {s["id"]: s for s in _read("students")}
        users    = {u["id"]: u for u in _read("users")}
        result = []
        for sid in my_student_ids:
            s = students.get(sid)
            if not s:
                continue
            u = users.get(s["user_id"])
            if u:
                result.append((s["id"], u["name"], u["username"],
                               s["semester"], s["department"]))
        return sorted(result, key=lambda x: x[1])

    # ── Grade queries ─────────────────────────────────────────────

    def get_student_grades(self, student_id, teacher_id=None):
        # Returns tuples (grade_id, subj_name, code, score, letter, semester).
        # If teacher_id is given, only subjects assigned to that teacher are included.
        grades   = [g for g in _read("grades") if g["student_id"] == student_id]
        subjects = {s["id"]: s for s in _read("subjects")}

        if teacher_id is not None:
            my_subjects = {t["subject_id"] for t in _read("teacher_subjects")
                           if t["teacher_id"] == teacher_id}
            grades = [g for g in grades if g["subject_id"] in my_subjects]

        result = []
        for g in grades:
            s = subjects.get(g["subject_id"])
            if s:
                result.append((g["id"], s["name"], s["code"],
                               g["score"], g["grade_letter"], g["semester"]))
        return result

    def update_grade(self, grade_id, score, grade_letter):
        # Update score and grade_letter for an existing grade record.
        grades = _read("grades")
        for g in grades:
            if g["id"] == grade_id:
                g["score"]        = score
                g["grade_letter"] = grade_letter
                break
        _write("grades", grades)

    # ── Activity log ──────────────────────────────────────────────

    def log_action(self, user_id, action, target=None):
        # Append one entry to activity_log.json.
        log = _read("activity_log")
        lid = _next_id("activity_log")
        log.append({
            "id":        lid,
            "user_id":   user_id,
            "action":    action,
            "target":    target,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        _write("activity_log", log)

    def get_recent_activity(self, limit=8):
        # Returns tuples (action, target, timestamp) for the most recent entries.
        log = sorted(_read("activity_log"),
                     key=lambda x: x["timestamp"], reverse=True)
        return [(e["action"], e["target"], e["timestamp"]) for e in log[:limit]]

    # ── Attendance ────────────────────────────────────────────────

    def mark_attendance(self, student_id, subject_id, date, status):
        # Insert or replace an attendance record for student/subject/date.
        if status not in ("Present", "Absent", "Late"):
            print(f"[FM Error] Invalid attendance status: {status}")
            return
        attendance = _read("attendance")
        for rec in attendance:
            if (rec["student_id"] == student_id
                    and rec["subject_id"] == subject_id
                    and rec["date"] == date):
                rec["status"] = status
                _write("attendance", attendance)
                return
        aid = _next_id("attendance")
        attendance.append({"id": aid, "student_id": student_id,
                           "subject_id": subject_id, "date": date, "status": status})
        _write("attendance", attendance)

    def get_student_attendance(self, student_id):
        # Returns tuples (id, subj_name, code, date, status) sorted newest-first.
        records  = [a for a in _read("attendance") if a["student_id"] == student_id]
        subjects = {s["id"]: s for s in _read("subjects")}
        result = []
        for a in records:
            s = subjects.get(a["subject_id"])
            if s:
                result.append((a["id"], s["name"], s["code"], a["date"], a["status"]))
        return sorted(result, key=lambda x: x[3], reverse=True)

    def get_attendance_summary(self, student_id):
        # Returns {total, present, absent, late, percentage}.
        records = [a for a in _read("attendance") if a["student_id"] == student_id]
        total   = len(records)
        present = sum(1 for a in records if a["status"] == "Present")
        absent  = sum(1 for a in records if a["status"] == "Absent")
        late    = sum(1 for a in records if a["status"] == "Late")
        pct     = round((present / total) * 100, 1) if total else 0.0
        return {"total": total, "present": present,
                "absent": absent, "late": late, "percentage": pct}

    def delete_attendance(self, attendance_id):
        # Delete a single attendance record by its ID.
        attendance = [a for a in _read("attendance") if a["id"] != attendance_id]
        _write("attendance", attendance)
