from datetime import datetime
import sqlite3
from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text
from app.handlers.common import AdressList


async def save_history(user_chat_id: int, url: str):
    current_date = datetime.now()
    with sqlite3.connect('app/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO historyurl (user_chat_id, url, date) '
            'VALUES (?, ?, ?)',
            (user_chat_id, url, current_date))
        conn.commit()


async def get_history(message: types.Message):
    user_id = message.chat.id
    keyboard = types.InlineKeyboardMarkup()
    with sqlite3.connect('app/users.db') as conn:
        cursor = conn.cursor()
        select_stmt = f"select url, date from historyurl where user_chat_id={user_id} order by key DESC LIMIT 0,3"
        cursor.execute(select_stmt)
        result = cursor.fetchall()
        for i in result:
            date_format = i[1][8:10] + '.' + i[1][5:7] + '.' + i[1][0:4] + ' ' + i[1][11:16]
            button = types.InlineKeyboardButton(text=date_format, url=i[0])
            keyboard.add(button)
    await message.answer('Последние три маршрута, построенных Вами. Для построения нового маршрута отправьте команду '
                         '/adress', reply_markup=keyboard)


def register_handlers_history(dp: Dispatcher):
    dp.register_message_handler(get_history, Text(contains='История'), state=AdressList.waiting_for_start_adress)
