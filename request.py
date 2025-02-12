import os
import logging
import json
import aiohttp
from aiohttp import ClientSession
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)


url_routes = os.getenv('URL_ROUTES')
url_late = os.getenv('URL_LATE')
token = os.getenv('TOKEN')
db_url = os.getenv('DB_URL')
db_add_user_endpoint = os.getenv('DB_ADD_USER_ENDPOINT')
db_sent_message_endpoint = os.getenv('DB_SENT_MESSAGE_ENDPOINT')


async def get_routes(date):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "token": token,
                "date": date
            }
            logger.info(f"Дата: {date}")
            headers = {'Content-Type': 'application/json'}
            logger.info("Отправа запроса на роуты")
            async with session.post(url_routes, data=json.dumps(payload), headers=headers) as response:
                logger.info(
                    f"Статус: {response.status}")
                if response.status == 200:
                    text_response = await response.text()  # Получаем текст
                    logger.info(f"Полученный ответ: {text_response}")
                    try:
                        # Пробуем преобразовать в JSON
                        return json.loads(text_response)
                    except json.JSONDecodeError as json_error:
                        logger.error(
                            f"Ошибка при декодировании JSON: {json_error}")
                        return {'error': f"Неправильный формат ответа: {text_response}"}
                else:

                    text_response = await response.content()  # Получаем текст
                    logger.info(f"Полученный ответ: {text_response}")
                    return {'error': f"HTTP Error: {response.status}"}
    except Exception as e:
        logger.error(f"Ошибка при выполнении POST запроса: {e}")
        return {'error': str(e)}


async def set_late(number):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "token": token,
                "number": number
            }
            logger.info(f"Дата: {number}")
            headers = {'Content-Type': 'application/json'}
            logger.info("Отправа запроса на роуты")
            async with session.post(url_late, data=json.dumps(payload), headers=headers) as response:
                logger.info(
                    f"Статус: {response.status}")
                if response.status == 200:
                    text_response = await response.text()  # Получаем текст
                    logger.info(f"Полученный ответ: {text_response}")
                    try:
                        # Пробуем преобразовать в JSON
                        return json.loads(text_response)
                    except json.JSONDecodeError as json_error:
                        logger.error(
                            f"Ошибка при декодировании JSON: {json_error}")
                        return {'error': f"Неправильный формат ответа: {text_response}"}
                else:

                    text_response = await response.content()  # Получаем текст
                    logger.info(f"Полученный ответ: {text_response}")
                    return {'error': f"HTTP Error: {response.status}"}
    except Exception as e:
        logger.error(f"Ошибка при выполнении POST запроса: {e}")
        return {'error': str(e)}


async def send_request(text, payload):
    """Отправка POST-запросов"""
    async with ClientSession() as session:
        if text == 'add_user':
            url = db_url+db_add_user_endpoint
        elif text == 'send_message':
            url = db_url+db_sent_message_endpoint
        else:
            logger.error("No url provided")
            return
        headers = {'Content-Type': 'application/json'}
        async with session.post(url, data=json.dumps(payload), headers=headers) as response:
            return await response.json()
