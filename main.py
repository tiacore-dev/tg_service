import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeChat)
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
app = web.Application(client_max_size=200 * 1024 ** 2)

app.router.add_post('/sent-message/', handle_post_request)


async def start_web_server():
    logger.info(f"🔍 Проверка переменной PORT: {port}")

    if not port:
        logger.error("❌ PORT не установлен! Укажите порт в .env")
        return

    try:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", int(port))  # Приводим к `int`
        logger.info(f"🚀 Запуск веб-сервера на порту {port}")
        await site.start()
    except Exception as e:
        logger.error(f"❌ Ошибка запуска сервера: {e}")


async def set_bot_commands():
    # Сбрасываем все команды перед установкой новых
    # Сброс по умолчанию
    await bot.set_my_commands([], scope=BotCommandScopeDefault())
    # Сброс в приватных чатах
    await bot.set_my_commands([], scope=BotCommandScopeAllPrivateChats())
    # Сброс в группах
    await bot.set_my_commands([], scope=BotCommandScopeAllGroupChats())
    await bot.set_my_commands([], scope=BotCommandScopeAllChatAdministrators())

    # Основные команды для всех пользователей
    common_commands = [
        BotCommand(command="/start", description="Запустить бота"),
    ]

    # Команды только для избранных пользователей
    special_commands = [
        BotCommand(command="/keyboard", description="Показать клавиатуру"),
        BotCommand(command="/remove_keyboard",
                   description="Скрыть клавиатуру"),
    ]

    # Устанавливаем базовые команды для всех пользователей
    await bot.set_my_commands(common_commands, scope=BotCommandScopeAllPrivateChats())

    # Получаем список избранных чатов
    run_chats = os.getenv("ROUTER_CHATS").split(",")

    # Устанавливаем дополнительные команды для избранных пользователей
    for chat_id in run_chats:
        await bot.set_my_commands(common_commands + special_commands, scope=BotCommandScopeChat(chat_id=int(chat_id)))


async def main():
    logger.info('Бот запущен')
    await set_bot_commands()  # Добавляем команды в Telegram
    await asyncio.gather(
        start_web_server(),  # Запуск веб-сервера
        dp.start_polling(bot)  # Запуск бота
    )


if __name__ == "__main__":
    asyncio.run(main())
