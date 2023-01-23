from aiogram import Dispatcher, Bot
from app.config_reader import load_config
from aiogram.types import InputFile
from aiogram import types
from aiogram.dispatcher import FSMContext
from app.handlers.common import AdressList
from app.handlers.excel_parcer import format_file
import os
import sqlite3
from app.handlers.utilities import xlsx_reader, csv_reader
from app.handlers.excel_parcer import IsAdmin
from aiogram.dispatcher.filters import Text

config = load_config("config/bot.ini")
bot = Bot(token=config.tg_bot.token)


async def moderate(message: types.Message, state: FSMContext):
    doc_path = 'app/files/examples/example_users.xlsx'
    await message.answer(
        'Введите номер пользователя, которому Вы хотите сменить роль, либо отправьте файл '
        'формата xlsx, xls, csv со список пользователей. Важно! Ячейка A1 <u><b>обязательно</b></u> должна называться '
        '"Номера телефонов". Пример файла:', parse_mode=types.ParseMode.HTML)
    await message.answer_document(InputFile(doc_path))
    await state.set_state(AdressList.admin_state)


async def change_role_user(message: types.Message):
    with sqlite3.connect('app/users.db') as conn:
        cursor = conn.cursor()
        select_stmt = f"select username, user_chat_id from users_table " \
                      f"where telephone_number like '%{message.text[1:]}%'"
        cursor.execute(select_stmt)
        result = cursor.fetchone()
    keyboard = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='Admin', callback_data=f'change, admin, {result[1]}')
    btn2 = types.InlineKeyboardButton(text='User', callback_data=f'change, user, {result[1]}')
    keyboard.add(btn1, btn2)
    await message.answer(f'Выберите роль, которую Вы хотите назначить пользователю {result[0]}', reply_markup=keyboard)


async def change_role(call: types.CallbackQuery):
    data_list = call.data.split(', ')
    with sqlite3.connect('app/users.db') as conn:
        cursor = conn.cursor()
        sql = f"Update users_table set role='{data_list[1]}' where user_chat_id='{data_list[2]}'"
        cursor.execute(sql)
    try:
        await bot.send_message(chat_id=data_list[2], text=f'Ваша роль изменилась, теперь Вы {data_list[1]}')
    except:
        await call.message.answer(f'Пользователь заблокировал бота')
    await call.message.answer('Роль пользователя изменена'
                              f'\nСписок команд:'
                              f'\n/moderate - изменение ролей пользователям'
                              f'\n/mail - осуществить рассылку сообщений пользователям'
                              )


async def mail(message: types.Message, state: FSMContext):
    await message.answer(
        'Введите сообщение, с которым необходимо осуществить рассылку')
    await state.set_state(AdressList.waiting_for_message.state)


async def change_role_all(message: types.Message, state: FSMContext):
    file_typer = message.document.mime_type
    if format_file(file_typer):
        await message.answer(f'Файл не является файлом формата xlsx или csv.')
        return
    direc = os.getcwd()
    last_file = await message.document.download(destination_dir=f'{direc}/app/files/admin')

    if file_typer == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        text = await xlsx_reader(last_file)
    else:
        text = await csv_reader(last_file.name)

    await message.answer(
        f'\n{text}'
        f'\n'
        f'\nСписок команд: '
        f'\n/moderate - изменение ролей пользователям'
        f'\n/mail - осуществить рассылку сообщений пользователям'
        f'\n/adress - осуществить рассылку сообщений пользователям', parse_mode=types.ParseMode.HTML)
    await state.finish()
    await state.set_state(AdressList.waiting_for_start_adress.state)


async def send_message_all(message: types.Message, state: FSMContext):
    with sqlite3.connect('app/users.db') as conn:
        cursor = conn.cursor()
        sql = f"select user_chat_id, username from users_table"
        cursor.execute(sql)
        result = cursor.fetchall()
        for i in result:
            try:
                await bot.send_message(chat_id=i[0], text=message.text)
            except:
                await message.answer(f'Пользователь {i[1]} заблокировал бота')
    await message.answer('Рассылка выполнена')
    await state.finish()
    await state.set_state(AdressList.waiting_for_start_adress.state)


def register_handlers_administrate(dp: Dispatcher):
    dp.register_message_handler(moderate, IsAdmin(), commands="moderate", state='*')
    dp.register_message_handler(change_role_user, IsAdmin(), Text(startswith='89'), state=AdressList.admin_state)
    dp.register_message_handler(change_role_all, IsAdmin(), content_types=['document'], state=AdressList.admin_state)
    dp.register_message_handler(mail, IsAdmin(), commands='mail', state='*')
    dp.register_message_handler(send_message_all, IsAdmin(), state=AdressList.waiting_for_message)
    dp.register_callback_query_handler(change_role, Text(startswith='change'),
                                       state='*')
