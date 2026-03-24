import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

BASE_DIR = Path(__file__).parent.resolve()
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)

DB_FILES = {
    "psychologist": "psychology.db",
    "programmer": "programmer.db",
    "adult": "adult.db",
    "general": "default.db",
    "writer": "writer.db",
    "assistant": "assistant.db",
    "madina": "madina.db"
}

DB_PATHS = {}
for role, filename in DB_FILES.items():
    DB_PATHS[role] = DB_DIR / filename

AVAILABLE_ROLES = [
    {"id": "psychologist", "name": "🧠 Психолог"},
    {"id": "programmer", "name": "💻 Программист"},
    {"id": "adult", "name": "🔞 18+ Контент"},
    {"id": "writer", "name": "✍️ Писатель"},
    {"id": "assistant", "name": "🤖 Ассистент"},
    {"id": "general", "name": "💬 Общий чат"},
]

ROLE_MODELS = {
    "psychologist": "google/gemma-2-9b-it:free",
    "programmer": "deepseek/deepseek-chat:free",
    "adult": "undi95/toppy-m-7b:free",
    "writer": "google/gemma-2-9b-it:free",
    "assistant": "meta-llama/llama-3-8b-instruct:free",
    "general": "mistralai/mistral-7b-instruct:free"
}

CONTEXT_WINDOW = 6
MAX_CACHE_SIZE = 100

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("⚠️ TELEGRAM_BOT_TOKEN или OPENROUTER_API_KEY не найдены в окружении!")
