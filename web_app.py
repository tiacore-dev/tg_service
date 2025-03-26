import logging
import os
from io import BytesIO
import base64
from dotenv import load_dotenv
from aiohttp import web, ClientSession
import aiohttp

logger = logging.getLogger(__name__)
# Aiohttp маршрут для получения сообщений
# Загрузить переменные окружения
load_dotenv()
TG_API_TOKEN = os.getenv('TG_API_TOKEN')


async def handle_post_request(request):
    json_data = await request.json()
    logger.info(f"📩 Incoming request data: {json_data}")
    chat_id = json_data.get('userid')
    text = json_data.get('text')
    attachments = json_data.get('attachments')
    if not text:
        text = ""
    data = {"chat_id": chat_id, "text": text}
    logger.info(f"📝 Sending message to chat_id={chat_id}: {text}")
    # Отправляем сначала текст
    async with ClientSession() as session:
        async with session.post(f'https://api.telegram.org/bot{TG_API_TOKEN}/sendMessage', json=data) as response:
            result = await response.json()
            logger.info(f"✅ Message response from Telegram: {result}")
        if attachments:
            for attachment in attachments:
                file_name = attachment['fileName']
                base64_data = attachment['base64Data']
                if not file_name or not base64_data:
                    logger.warning(
                        "⚠️ Skipping attachment: missing fileName or base64Data")
                    continue
                try:
                    file_bytes = base64.b64decode(base64_data)
                    file_obj = BytesIO(file_bytes)
                    file_obj.name = file_name

                    send_doc_url = f"https://api.telegram.org/bot{TG_API_TOKEN}/sendDocument"
                    form = aiohttp.FormData()
                    form.add_field("chat_id", str(chat_id))
                    form.add_field("document", file_obj, filename=file_name)
                    logger.info(
                        f"📤 Sending document {file_name} to Telegram...")
                    async with session.post(send_doc_url, data=form) as resp:
                        result = await resp.json()
                        logger.info(
                            f"📎 Sent file {file_name} to Telegram: {result}")
                except Exception as e:
                    logger.error(f"❌ Failed to send file {file_name}: {e}")

    return web.json_response({"status": "ok"})
