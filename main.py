import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import load_dotenv
from handlers import router_main  # Импортируем router из handlers
from keyboard import router_keyboard
from logger import logger
from web_app import handle_post_request


# Загрузить переменные окружения
load_dotenv()
API_TOKEN = os.getenv('TG_API_TOKEN')
port = os.getenv('PORT')
# Создаем объекты бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
# Регистрируем router с хендлерами
dp.include_router(router_keyboard)
dp.include_router(router_main)

# Flask-like сервер на Aiohttp
app = web.Application()

app.router.add_post('/sent-message/', handle_post_request)


async def start_web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    logger.info(f"Запуск веб-сервера на порту {port}")
    await site.start()


async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/keyboard", description="Показать клавиатуру"),
        BotCommand(command="/remove_keyboard",
                   description="Скрыть клавиатуру"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logger.info('Бот запущен')
    await set_bot_commands()  # Добавляем команды в Telegram
    await asyncio.gather(
        start_web_server(),  # Запуск веб-сервера
        dp.start_polling(bot)  # Запуск бота
    )


if __name__ == "__main__":
    asyncio.run(main())
