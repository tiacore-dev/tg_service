import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers import router  # Импортируем router из handlers
from logger import logger
from web_app import handle_post_request


# Загрузить переменные окружения
load_dotenv()
API_TOKEN = os.getenv('TG_API_TOKEN')

# Создаем объекты бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
# Регистрируем router с хендлерами
dp.include_router(router)

# Flask-like сервер на Aiohttp
app = web.Application()

app.router.add_post('/sent-message/', handle_post_request)


async def start_web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5010)
    logger.info("Запуск веб-сервера на порту 5010")
    await site.start()


async def main():
    logger.info('Бот запущен')
    await bot.delete_webhook(drop_pending_updates=True)  # Удаляем Webhook
    logger.info('Webhook удален, запускаем Polling...')
    await asyncio.gather(
        start_web_server(),  # Запуск веб-сервера
        dp.start_polling(bot)  # Запуск бота
    )


if __name__ == "__main__":
    asyncio.run(main())
