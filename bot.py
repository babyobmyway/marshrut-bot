import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from app.config_reader import load_config
from app.handlers.common import register_handlers_common
from app.handlers.adresses import register_handlers_adresses
from app.handlers.history import register_handlers_history
from app.handlers.excel_parcer import register_handlers_excel, IsAdmin
from app.handlers.adminscommand import register_handlers_administrate

logger = logging.getLogger(__name__)
config = load_config("config/bot.ini")
bot = Bot(token=config.tg_bot.token)


async def set_commands(bot_tg: Bot):
    commands = [
        BotCommand(command="/start", description="Начать работу"),
        BotCommand(command="/adress", description="Добавить адрес"),
    ]
    await bot_tg.set_my_commands(commands)


async def main():
    # Настройка логирования в stdout
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.error("Starting bot")
    # Парсинг файла конфигурации

    # Объявление и инициализация объектов бота и диспетчера
    dp = Dispatcher(bot, storage=MemoryStorage())

    dp.bind_filter(IsAdmin)
    # Регистрация хэндлеров
    register_handlers_common(dp)
    register_handlers_adresses(dp)
    register_handlers_history(dp)
    register_handlers_excel(dp)
    register_handlers_administrate(dp)
    # Установка команд бота
    await set_commands(bot)
    # Запуск поллинга
    # await dp.skip_updates()  # пропуск накопившихся апдейтов (необязательно)
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
