from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from app.handlers.common import AdressList
from aiogram.dispatcher.filters import Text
from app.handlers.history import save_history
import aiogram.utils.markdown as fmt
import re
import requests


def invert_coords(coords):
    coordinates = coords[9:] + '%2C' + coords[:9]
    return coordinates


def keys_for_adresses(name):
    keys_list = list(name.keys())
    length = len(keys_list)
    return length


def check_address(coords):
    locationformat = re.sub(r' ', r'+', coords)
    apikey = '7e08f740-d6d8-48e1-b3b5-20282fb6f481'
    url = f"https://geocode-maps.yandex.ru/1.x/?apikey={apikey}&format=json&geocode" \
          f"=Россия+Челябинская+область+Челябинск+{locationformat} "
    r = requests.get(url, verify=False)
    json_data = r.json()
    address_str = json_data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"][
        "pos"]
    if len(address_str) == 18:
        coordinates = address_str[9:] + '%2C' + address_str[:9]
    else:
        coordinates = address_str[10:] + '%2C' + address_str[:9]
    return coordinates.replace(' ', '')


async def adress_start(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton('Маршрут')
    button1 = types.KeyboardButton('Отправить свое местоположение', request_location=True)
    keyboard.add(button, button1)
    await state.update_data(adress=[])
    await message.answer('Введите адрес формата "Ленина 22" или "Свободы 2" (учтите, что обязательно сначала '
                         'улица/проспект/переулок, а уже потом адрес через пробел) или отправьте свое '
                         'местоположение', reply_markup=keyboard)
    await state.set_state(AdressList.waiting_for_add_adress.state)


async def adress(message: types.Message, state: FSMContext):
    messagetext = message.text
    # Проверка адреса на корректность
    coords = check_address(messagetext)
    numbers = re.findall(r'\d+', messagetext)
    if len(numbers) == 0 or coords == '55.159902%2C61.402554':
        await message.answer('Неверно задан адрес')
        return
    # Конец проверки

    # Сохранение полученного адреса [ [str_adress], [status], [coords_adress] ]
    user_data = await state.get_data()
    adresses = user_data['adress']
    new_adress = [messagetext, ' ✅', coords]
    adresses.append(new_adress)
    await state.update_data(adress=adresses)
    # Конец сохранения полученного

    keyboard = types.InlineKeyboardMarkup()
    for i in adresses:
        index_element = adresses.index(i)
        print(index_element)
        str_index_element = str(index_element)
        button1 = types.InlineKeyboardButton(text=i[0] + i[1], callback_data='delete' + str_index_element)
        keyboard.add(button1)
    await message.answer("Адресс был успешно добавлен введите следующий "
                         "адресс, либо постройте маршрут", reply_markup=keyboard)


async def location(message: types.Message, state: FSMContext):
    if message.location is None:
        return await message.answer('Ваше местоположение неопределено')
    longitude = message.location.longitude
    latitude = message.location.latitude
    coordinate = f'{latitude}' + '%2C' + f"{longitude}"
    user_data = await state.get_data()
    adresses = user_data['adress']
    for i in adresses:
        if i[0] == 'Ваше местоположение':
            return await message.answer("Вы уже отправляли ваше местоположение")
    new_adress = ['Ваше местоположение', ' ✅', coordinate]
    adresses.append(new_adress)
    await state.update_data(adress=adresses)
    keyboard = types.InlineKeyboardMarkup()
    for i in adresses:
        index_element = adresses.index(i)
        button1 = types.InlineKeyboardButton(text=i[0] + i[1], callback_data=f'delete{index_element}')
        keyboard.add(button1)
    await message.answer("Адресс был успешно добавлен введите следующий "
                         "адресс, либо постройте маршрут", reply_markup=keyboard)


async def route(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('История'))
    url = 'https://yandex.ru/maps/56/chelyabinsk/?ll=61.389544%2C55.151143&mode=routes&rtext='
    coords = await state.get_data()
    dict_with_adresses = coords['adress']
    for i in dict_with_adresses:
        if i[2] != '':
            url += i[2] + '~'
    count_symbols = url.count('~')
    if count_symbols < 2:
        await message.answer('Не хватает адресов для построения маршрута')
        return
    await save_history(message.chat.id, url[:-1])
    await message.answer(
        f"{fmt.hide_link(url)}<a href='{url[:-1]}'>Ссылку</a> на маршрут удобнее открывать с установленным приложением"
        f"\nЕсли Вы открыли ссылку в Вашем браузере по клику, нажмите на кнопку 'Оптимизировать' в левой части экрана"
        f"\nТакже открытую ссылку в приложении можно использовать с функцией Навигатора"
        f"\nДля построения нового маршрута введите команду /adress",
        parse_mode=types.ParseMode.HTML,
        reply_markup=keyboard)
    await state.set_state(AdressList.waiting_for_start_adress.state)
    await state.update_data(adress=[])


async def delete_adress(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    last_index_data = call.data[-1]
    adres_of_list = user_data['adress']
    adres_of_list[int(last_index_data)][1] = ' ❌'
    adres_of_list[int(last_index_data)][2] = ''
    await state.update_data(adress=adres_of_list)
    keyboard = types.InlineKeyboardMarkup()
    for i in adres_of_list:
        index_element = adres_of_list.index(i)
        button1 = types.InlineKeyboardButton(text=i[0] + i[1], callback_data=f'delete{index_element}')
        keyboard.add(button1)
    await call.answer('Адрес удален', show_alert=True)
    await call.message.answer('Обновленный список адресов с учетом текущего статуса', reply_markup=keyboard)


def register_handlers_adresses(dp: Dispatcher):
    dp.register_message_handler(adress_start, commands="adress", state=AdressList.waiting_for_start_adress)
    dp.register_message_handler(adress, Text(contains=' '), state=AdressList.waiting_for_add_adress)
    dp.register_message_handler(location, content_types=['location'], state=AdressList.waiting_for_add_adress)
    dp.register_message_handler(route, Text(equals='Маршрут'), state=AdressList.waiting_for_add_adress)
    dp.register_callback_query_handler(delete_adress, Text(startswith='delete'),
                                       state=AdressList.waiting_for_add_adress)
