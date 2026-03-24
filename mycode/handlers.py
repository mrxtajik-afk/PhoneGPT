import asyncio
import logging
import sqlite3
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path
from config import ADMIN_ID, AVAILABLE_ROLES, DB_DIR
from mycode.ui import get_main_menu_keyboard, get_rating_keyboard, get_admin_keyboard
from mycode.models.llm_router import call_llm_api

logger = logging.getLogger("__name__")
user_roles = {}

class UserState(StatesGroup):
    in_dialog = State()

def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_secret, Command("secret"))
    dp.message.register(cmd_admin, Command("admin"))
    dp.message.register(handle_message, F.text)
    dp.callback_query.register(handle_role_cb, F.data.startswith("role:"))
    dp.callback_query.register(handle_rating, F.data.startswith("rate:"))
    dp.callback_query.register(handle_admin_cb, F.data.startswith("admin:"))
    logger.info("Обработчики зарегистрированы")

async def cmd_start(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    uname = message.from_user.username or "Пользователь"
    conn = sqlite3.connect(DB_DIR / "master.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users(user_id,username,first_name) VALUES(?,?,?)", (uid, uname, message.from_user.first_name))
    conn.commit()
    conn.close()
    await message.answer(f"👋 Привет, {uname}!\n\nЯ — Мадина.\nВыбери роль:", reply_markup=get_main_menu_keyboard())
    await state.clear()

async def cmd_secret(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Нет доступа")
        return
    conn = sqlite3.connect(DB_DIR / "madina.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM training_data")
    total = cur.fetchone()[0]
    conn.close()
    await message.answer(f"🔐 Статистика:\nЗаписей: {total}")
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ Админ:", reply_markup=get_admin_keyboard())

async def handle_role_cb(callback: types.CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    data = callback.data.split(":")
    if len(data) < 2:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    rid = data[1]
    rname = None
    for r in AVAILABLE_ROLES:
        if r["id"] == rid:
            rname = r["name"]
            break
    if not rname:
        await callback.answer("❌ Роль не найдена", show_alert=True)
        return
    user_roles[uid] = rid
    await callback.answer(f"✅ {rname}")
    await callback.message.edit_text(f"✅ Выбрана роль: {rname}\n\nЗадавайте вопросы!")
    await state.set_state(UserState.in_dialog)

async def handle_message(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    txt = message.text
    if uid not in user_roles:
        await message.answer("⚠️ Выберите роль!", reply_markup=get_main_menu_keyboard())
        return
    role = user_roles[uid]
    load = await message.answer("🤔 Думаю...")
    try:
        resp = await call_llm_api(role=role, user_message=txt, user_id=uid, retry_prompt=False)
        await load.delete()
        m = await message.answer(resp, reply_markup=get_rating_keyboard(message.message_id + 1, role))
        save_db(role, uid, message.from_user.username, txt, resp, m.message_id)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await load.delete()
        await message.answer("⚠️ Ошибка.")

async def handle_rating(callback: types.CallbackQuery):
    data = callback.data.split(":")
    action = data[1]
    role = data[3]
    uid = callback.from_user.id
    await callback.answer()
    if action == "like":
        upd_rate(role, uid, 1)
        original_text = callback.message.text
        thank_text = "\n\n_Спасибо за оценку💞_"
        if len(original_text) + len(thank_text) <= 4096:
            new_text = original_text + thank_text
        else:
            new_text = original_text[:4080] + thank_text
        try:
            await callback.message.edit_text(text=new_text, reply_markup=get_rating_keyboard(callback.message.message_id, role), parse_mode="Markdown")
        except:
            tmp = await callback.message.answer("_Спасибо за оценку💞_", parse_mode="Markdown")
            await asyncio.sleep(2)
            await tmp.delete()

    elif action == "dislike":
        upd_rate(role, uid, -1)
        conn = sqlite3.connect(DB_DIR / f"{role}.db", check_same_thread=False)
        cur = conn.cursor()
        cur.execute("SELECT message_text FROM dialogs WHERE user_id=? AND rating=-1 ORDER BY id DESC LIMIT 1", (uid,))
        row = cur.fetchone()
        conn.close()
        if row:
            q = row[0]
            await callback.message.delete()
            retry = await callback.message.answer("🔄 Переформулирую...")
            new_resp = await call_llm_api(role=role, user_message=q, user_id=uid, retry_prompt=True)
            await retry.delete()
            nm = await callback.message.answer(new_resp, reply_markup=get_rating_keyboard(callback.message.message_id, role))
            save_db(role, uid, callback.from_user.username, q, new_resp, nm.message_id, 1)

    elif action == "menu":
        await callback.message.answer("📋 Меню:", reply_markup=get_main_menu_keyboard())

async def handle_admin_cb(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    await callback.answer()
    if callback.data == "admin:stats":
        conn = sqlite3.connect(DB_DIR / "master.db", check_same_thread=False)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        conn.close()
        await callback.message.answer(f"📊 Пользователей: {total}")

def save_db(role, uid, uname, umsg, aresp, rmid, rc=0):
    conn = sqlite3.connect(DB_DIR / f"{role}.db", check_same_thread=False)    
    cur = conn.cursor()
    cur.execute("INSERT INTO dialogs(user_id,username,message_text,response_text,rating,retry_count) VALUES(?,?,?,?,NULL,?)", (uid, uname, umsg, aresp, rc))
    conn.commit()
    conn.close()

def upd_rate(role, uid, rating):
    conn = sqlite3.connect(DB_DIR / f"{role}.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("UPDATE dialogs SET rating=? WHERE user_id=? AND rating IS NULL ORDER BY id DESC LIMIT 1", (rating, uid))
    conn.commit()
    conn.close()
