import logging
import os
from dotenv import load_dotenv
from aiohttp import web, ClientSession
import aiohttp

logger = logging.getLogger(__name__)
# Aiohttp маршрут для получения сообщений
# Загрузить переменные окружения
load_dotenv()
TG_API_TOKEN = os.getenv('TG_API_TOKEN')


async def handle_post_request(request):
    try:
        reader = await request.multipart()
        chat_id = None
        text = ""
        files = []

        # Читаем части формы
        while True:
            part = await reader.next()
            if part is None:
                break

            if part.name == "userid":
                chat_id = await part.text()
            elif part.name == "text":
                text = await part.text()
            elif part.name == "attachments" and part.filename:
                file_data = await part.read()
                files.append({
                    "filename": part.filename,
                    "content": file_data
                })

        if not chat_id:
            return web.json_response({"error": "Missing chat_id"}, status=400)

        logger.info(
            f"📩 New request: chat_id={chat_id}, text={text}, files={[f['filename'] for f in files]}")

        # Отправка текста
        if text.strip():
            msg_data = {"chat_id": chat_id, "text": text}
            async with ClientSession() as session:
                async with session.post(f"https://api.telegram.org/bot{TG_API_TOKEN}/sendMessage", json=msg_data) as resp:
                    msg_result = await resp.json()
                    logger.info(f"✅ Message sent: {msg_result}")

        # Отправка файлов
        if files:
            async with ClientSession() as session:
                for file in files:
                    form = aiohttp.FormData()
                    form.add_field("chat_id", chat_id)
                    form.add_field(
                        "document", file["content"], filename=file["filename"])

                    logger.info(f"📤 Sending file {file['filename']}...")

                    async with session.post(f"https://api.telegram.org/bot{TG_API_TOKEN}/sendDocument", data=form) as resp:
                        doc_result = await resp.json()
                        logger.info(
                            f"📎 File sent {file['filename']}: {doc_result}")

        return web.json_response({"status": "ok"})

    except Exception as e:
        logger.exception(f"🔥 Error in handle_post_request: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
