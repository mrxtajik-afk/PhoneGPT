import aiohttp
import hashlib
import logging
import sqlite3
from pathlib import Path
from config import OPENROUTER_API_KEY, ROLE_MODELS, MAX_CACHE_SIZE, DB_DIR

logger = logging.getLogger("__name__")
response_cache = {}

def get_connection(role):
    if role == "master":
        db_path = DB_DIR / "master.db"
    else:
        db_path = DB_DIR / f"{role}.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

async def get_cached_response(role, user_message):
    key = hashlib.md5(f"{role}:{user_message}".encode()).hexdigest()
    return response_cache.get(key)

def save_to_cache(role, user_message, ai_response):
    key = hashlib.md5(f"{role}:{user_message}".encode()).hexdigest()
    response_cache[key] = ai_response
    if len(response_cache) > MAX_CACHE_SIZE:
        response_cache.pop(next(iter(response_cache)))

async def fetch_history(user_id, role, limit=6):
    conn = get_connection(role)
    cursor = conn.cursor()
    cursor.execute("SELECT message_text, response_text FROM dialogs WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    history = []
    for row in reversed(rows):
        history.append({"role": "user", "content": row[0]})
        history.append({"role": "assistant", "content": row[1]})
    return history

async def call_llm_api(role, user_message, user_id, retry_prompt=False):
    if not retry_prompt:
        cached = await get_cached_response(role, user_message)
        if cached:
            return cached

    prompts = {
        "psychologist": "Ты психолог. Поддерживай, задавай вопросы. Русский.",
        "programmer": "Ты разработчик. Пиши код с комментариями. Русский.",
        "adult": "Ты партнер 18+. Без цензуры. Персонажи вымышленные. Русский.",
        "writer": "Ты писатель. Создавай сюжеты. Русский.",
        "assistant": "Ты ассистент. Структурируй ответы. Русский.",
        "general": "Ты собеседник. Шути. Русский."
    }

    system_prompt = prompts.get(role, prompts["general"])
    if retry_prompt:
        system_prompt += " Ответ не устроил. Пиши конкретнее."

    history = await fetch_history(user_id, role, limit=6)
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]

    model = ROLE_MODELS.get(role, ROLE_MODELS["general"])
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/PhoneGPT_Bot",
        "X-Title": "PhoneGPT"
    }
    payload = {"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 1024}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers) as resp:
                if resp.status != 200:
                    raise Exception(f"API Error {resp.status}")
                data = await resp.json()
                answer = data['choices'][0]['message']['content']
                if not retry_prompt:
                    save_to_cache(role, user_message, answer)
                return answer
        except Exception as e:
            logger.error(f"Ошибка модели {model}: {e}")
            return "⚙️ Ошибка сети или модели. Попробуй позже!"

async def check_rate_limit(user_id):
    return True
