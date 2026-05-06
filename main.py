import os
from dotenv import load_dotenv
from storage.file_manager import FileManager
from gui.login_screen import LoginScreen

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    print("\nWARNING: GEMINI_API_KEY is missing. AI features will be disabled.\n")

db = FileManager()
LoginScreen(db).render()
