import asyncio
import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_ID, DB_DIR
from database.db_core import init_all_databases
from mycode.handlers import register_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

async def main():
    print("🔄 Инициализация баз данных...")
    init_all_databases()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    register_handlers(dp)
    
    print("✅ Бот запущен! Ожидаю сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
