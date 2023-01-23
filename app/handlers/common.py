import sqlite3
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext


class AdressList(StatesGroup):
    waiting_for_auth = State()
    waiting_for_start_adress = State()
    waiting_for_add_adress = State()
    waiting_for_number = State()
    admin_state = State()
    waiting_for_message = State()


def get_access(user_chat_id):
    with sqlite3.connect('app/users.db') as conn:
        cursor = conn.cursor()
        id = user_chat_id
        select_stmt = f"select role from users_table where user_chat_id={id}"
        cursor.execute(select_stmt)
        result = cursor.fetchone()
        print(result)
        return result


def db_table_val(user_chat_id: int, username: str, user_id: int, telephone_number: int, access_to_bot):
    with sqlite3.connect('app/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users_table (user_chat_id, username, user_id, telephone_number, role) '
            'VALUES (?, ?, ?, ?, ?)',
            (user_chat_id, username, user_id, telephone_number, access_to_bot))
        conn.commit()


async def cmd_start(message: types.Message, state: FSMContext):
    access = get_access(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn2 = types.KeyboardButton("Зарегистрироваться", request_contact=True)
    us_name = message.chat.first_name
    markup.add(btn2)
    if access:
        if access[0] == 'admin':
            await message.answer(
                f'Привет {us_name}!'
                f'\nСписок комманд:'
                f'\n/moderate - изменение ролей пользователям'
                f'\n/mail - осуществить рассылку сообщений пользователям'
                f'\n/adress - осуществить рассылку сообщений пользователям'
            )
            await state.set_state(AdressList.waiting_for_start_adress.state)
        else:
            await message.answer(
                f'Привет {us_name}! Введите команду /adress')
            await state.set_state(AdressList.waiting_for_start_adress.state)
    else:
        await message.answer(
            "Вы не зарегистрированы, пройти регистрацию?", reply_markup=markup)
        await state.set_state(AdressList.waiting_for_auth.state)


async def registration(message: types.Message, state: FSMContext):
    if message.contact is not None:
        ud_id = message.contact.user_id
        us_name = message.contact.first_name
        us_id1 = 1
        telephone = message.contact.phone_number
        role = 'user'
        db_table_val(ud_id, us_name, us_id1, telephone, role)
        await message.answer(
            f'Поздравляем {us_name}, Вы зарегистрированы. Введите команду /adress')
        await state.set_state(AdressList.waiting_for_start_adress.state)


async def cmd_cancel(message: types.Message):
    await message.answer("Действие отменено", reply_markup=types.ReplyKeyboardRemove())


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(registration, content_types=['contact'], state=AdressList.waiting_for_auth)
    dp.register_message_handler(cmd_cancel, Text(equals="отмена", ignore_case=True), state="*")
