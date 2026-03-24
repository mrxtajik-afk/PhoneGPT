from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import AVAILABLE_ROLES

def get_main_menu_keyboard():
    keyboard = []
    for i in range(0, len(AVAILABLE_ROLES), 2):
        row = []
        for role in AVAILABLE_ROLES[i:i+2]:
            btn = InlineKeyboardButton(text=role["name"], callback_data=f"role:{role['id']}")
            row.append(btn)
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_rating_keyboard(message_id, role):
    btn1 = InlineKeyboardButton(text="👍", callback_data=f"rate:like:{message_id}:{role}")
    btn2 = InlineKeyboardButton(text="📋 Меню", callback_data=f"rate:menu:{message_id}:{role}")
    btn3 = InlineKeyboardButton(text="👎", callback_data=f"rate:dislike:{message_id}:{role}")
    return InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2, btn3]])

def get_admin_keyboard():
    btn1 = InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")
    btn2 = InlineKeyboardButton(text="🧪 Тест Мадины", callback_data="admin:madina_test")
    return InlineKeyboardMarkup(inline_keyboard=[[btn1], [btn2]])
