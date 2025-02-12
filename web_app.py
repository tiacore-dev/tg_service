import logging
import os
from dotenv import load_dotenv
from aiohttp import web, ClientSession

logger = logging.getLogger(__name__)
# Aiohttp маршрут для получения сообщений
# Загрузить переменные окружения
load_dotenv()
TG_API_TOKEN = os.getenv('TG_API_TOKEN')


async def handle_post_request(request):
    json_data = await request.json()
    data = {"chat_id": json_data['userid'], "text": json_data['text']}

    async with ClientSession() as session:
        async with session.post(f'https://api.telegram.org/bot{TG_API_TOKEN}/sendMessage', json=data) as response:
            result = await response.json()

    logger.info(f'Sent message to Telegram: {data}')
    return web.json_response(result)
