# -----------------------------------------------
# main.py - ScholarTrack LMS
# Role:     Application entry point — bootstraps the
#           database connection and opens the login window.
# Key classes used: DatabaseManager, LoginScreen
# OOP concepts demonstrated: Encapsulation (DB hidden
#           behind DatabaseManager), Polymorphism (each
#           role opens a different view after login)
# -----------------------------------------------
#
# ScholarTrack — Academic Performance Management System
# CS112 Object-Oriented Programming Project
#
# HOW TO RUN:
#   python main.py
#
# REQUIREMENTS:
#   pip install -r requirements.txt
#   (Also create a .env file with GEMINI_API_KEY=<your_key>
#    for the AI feedback feature; the app runs fine without it.)
#
# DEFAULT LOGIN CREDENTIALS (seeded on first launch):
#   Student  →  alice_s   / pass123
#   Student  →  bob_j     / pass123
#   Student  →  charlie_b / pass123
#   Teacher  →  ahmed_k   / pass123
#   Admin    →  admin     / admin123
# -----------------------------------------------

import os
from dotenv import load_dotenv

from database.db_manager import DatabaseManager
from gui.login_screen import LoginScreen

# Load environment variables from .env (e.g. GEMINI_API_KEY)
load_dotenv()


def main():
    """Entry point: checks the API key, opens the database, and launches the login screen."""

    # Warn if the Gemini API key is missing — the app still runs without it.
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("\nWARNING: GEMINI_API_KEY is missing or set to the placeholder in .env.")
        print("Add your real Google Gemini API key to enable AI feedback.")
        print("The app will launch normally; AI features will be disabled.\n")

    # Initialise the database — creates tables and seeds demo data on first run.
    db = DatabaseManager()
    print(f"Database ready: {db}")
    db.debug_print_all()

    # Open the login window and start the Tkinter event loop.
    LoginScreen(db).render()


if __name__ == "__main__":
    main()
