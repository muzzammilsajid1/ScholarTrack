# ScholarTrack

A robust, object-oriented Python application designed to track, manage, and analyze student academic performance. The system features secure role-based access controls for Administrators, Teachers, and Students, complete with integrated mathematical charting, dynamic PDF reporting, and AI-driven performance feedback.

## Tech Stack
- **Python 3**: Core language.
- **CustomTkinter**: Modern dark-themed graphical user interface (GUI).
- **SQLite3**: Lightweight, native relational database mapping.
- **Matplotlib**: Embedded graphical rendering for analytical curves.
- **Google Gemini API**: AI-powered study feedback and insights.
- **ReportLab**: Native PDF document generation.

## OOP Concepts Demonstrated

This project strictly adheres to native Object-Oriented Programming principles:

- **Abstraction**: 
  - `models/user.py`: The `User` class inherits from python's `ABC` module, establishing required abstract methods (`get_dashboard_data`, `generate_report`) that all human actors must implement securely.
- **Inheritance**: 
  - `models/student.py`, `models/teacher.py`, `models/admin.py`: All naturally subclass the root `User` object, inheriting primary traits like `id`, `name`, and `role`.
  - `models/exceptions.py`: System exceptions subclassing the base `Exception` runtime class.
- **Encapsulation**: 
  - `models/student.py`: Raw mathematical variables like `__gpa` are strictly protected behind private double-underscore attributes, guarded by rigorous `@property` setters ensuring grades never breach 4.0 manually.
  - `database/db_manager.py`: Raw SQL dialect strings and recursive database cursors are fully hidden from the frontend GUI.
- **Polymorphism**: 
  - `models/student.py`, `models/teacher.py`, `models/admin.py`: Each explicitly overrides the `generate_report()` method, producing entirely unique structures depending dynamically upon the object currently active in the UI loop.
- **Composition**: 
  - `gui/admin_view.py` and `gui/dashboard.py`: Higher-order window schemas are constructed by nesting robust smaller components (like `GradeService`, `DatabaseManager`, and `Admin` models) directly inside their constructors to separate algorithmic workloads elegantly.

## Folder Structure

```text
/
├── main.py                     # Initial execution point bootstrapping the database and login loop.
├── requirements.txt            # Package dependencies mapped identically for environments.
├── database/
│   └── db_manager.py           # Core SQLite controller handling tables, hooks, and testing seeds.
├── models/
│   ├── user.py                 # Abstract Base Class schema.
│   ├── student.py              # Student data structure inheriting User.
│   ├── teacher.py              # Teacher data structure inheriting User.
│   ├── admin.py                # Superuser structural logic.
│   └── exceptions.py           # Explicit custom errors (InvalidGradeError, etc).
├── services/
│   ├── grade_service.py        # Independent calculation module separating GPA math from GUIs.
│   └── report_service.py       # Isolated chart bridging.
└── gui/
    ├── login_screen.py         # Authentication entry layer.
    ├── dashboard.py            # Primary navigation router.
    ├── student_view.py         # Target Student UI natively running Gemini APIs and Matplotlib.
    ├── teacher_view.py         # Dedicated faculty grade editor mapping inline.
    └── admin_view.py           # System-wide searchable table and PDF report module.
```

## Setup Instructions

1. **Clone the Repository**
2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # (On Windows)
   # source venv/bin/activate    # (On macOS/Linux)
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure AI Environment Variables** *(Optional, but required for the AI Feedback feature)*:
   Rename `.env.example` to `.env` in the root directory and insert your own Gemini API key:
   ```env
   GEMINI_API_KEY="your_gemini_api_key_here"
   ```
5. **Run the Application**:
   ```bash
   python main.py
   ```
   *Note: Running `main.py` for the first time will automatically generate `tracker.db` and securely seed dummy data constraints for immediate testing. If you are upgrading to the new hashed password system, delete the existing `tracker.db` file so it gets regenerated cleanly with properly hashed passwords on the next run.*

## Running Without a Gemini API Key

This application is designed to function fully even if you do not have a Google Gemini API key. All core features (dashboards, SQLite databases, PDF exports, custom charts, grading, user generation) run 100% locally and perfectly without requiring internet access or the `google-genai` service. 

If no key is found inside `.env` or if you left the default placeholder, the login screen will launch successfully, but the student "AI Feedback" button panel will cleanly fall back to showing a gracefully disabled warning explicitly stating the AI feedback generation is bypassed.

## Default Dummy Credentials

The database automatically seeds these accounts if run completely from scratch or using `create_users.py`:

**Student (Seeded by DatabaseManager)**
- Username: `alice_s`
- Password: `pass123`

**Teacher (Seeded via create_users.py)**
- Username: `teacher`
- Password: `teacher123`

**Administrator (Seeded via create_users.py)**
- Username: `admin`
- Password: `admin123`

## Screenshots

- Screenshot coming soon
- Screenshot coming soon
- Screenshot coming soon
- Screenshot coming soon

## Known Limitations

- Passwords are encrypted using basic native SHA-256 hashing (no robust salting or bcrypt hashing currently deployed).
- This is entirely a local Desktop GUI architecture built with CustomTkinter and Matplotlib. 
- The database is locked natively to SQLite locally stored in the same directory, meaning it currently lacks multi-user client/server networking configurations.
