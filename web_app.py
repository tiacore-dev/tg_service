import re
import logging
import os
from dotenv import load_dotenv
from aiohttp import web, ClientSession
import aiohttp

logger = logging.getLogger("telegram_bot")
# Aiohttp маршрут для получения сообщений
# Загрузить переменные окружения
load_dotenv()
TG_API_TOKEN = os.getenv('TG_API_TOKEN')


async def debug_multipart_request(body_bytes, headers):

    content_type = headers.get("Content-Type", "")
    match = re.search(r'boundary=(.+)', content_type)
    if not match:
        logger.warning("⚠️ Boundary not found in Content-Type")
        return

    boundary = match.group(1).strip()
    boundary_bytes = f"--{boundary}".encode()

    logger.info(f"🧬 Parsed multipart structure with boundary: {boundary}")

    parts = body_bytes.split(boundary_bytes)
    logger.info(f"📦 Found {len(parts) - 2} part(s) + end delimiter")

    for i, part in enumerate(parts):
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue

        logger.info(f"\n📍 Part {i}")
        lines = part.split(b"\r\n")
        for line in lines[:10]:  # Логируем максимум 10 строк
            try:
                logger.info(f"🔹 {line.decode('utf-8')}")
            except Exception:
                logger.info(f"🔹 {line[:50]!r} (binary or undecodable)")

        if len(lines) > 10:
            logger.info("🔹 ...")

    logger.info("✅ Multipart body analysis complete.")


async def handle_post_request(request):
    try:
        # Читаем тело запроса один раз как байты
        body_bytes = await request.read()

        # logger.info(f"📥 Headers: {dict(request.headers)}")
        # logger.info(f"📦 Content-Type: {request.content_type}")
        # logger.info(f"🧱 Content-Length: {request.content_length}")
        # logger.info(f"🧾 Charset: {request.charset}")
        # logger.info(f"🧬 Raw body (first 1000 bytes): {body_bytes[:1000]!r}")
        # await debug_multipart_request(body_bytes, request.headers)

        # Подменяем тело запроса обратно, чтобы работал multipart()
        request._read_bytes = body_bytes

        reader = await request.multipart()
        chat_id = None
        text = ""
        files = []

        while True:
            part = await reader.next()
            if part is None:
                break

            if part.name == "userid":
                chat_id = await part.text()
                logger.info(f"📨 Received chat_id: {chat_id}")
            elif part.name == "text":
                text = await part.text()
                logger.info(
                    f"📝 Received text: {text[:100]}{'...' if len(text) > 100 else ''}")
            elif part.name == "attachments" and part.filename:
                file_data = await part.read()
                files.append({
                    "filename": part.filename,
                    "content": file_data
                })
                logger.info(
                    f"📎 Received file: {part.filename} ({len(file_data)} bytes)")

        if not chat_id:
            logger.warning("⚠️ Missing chat_id (userid) in form-data")
            return web.json_response({"error": "Missing chat_id"}, status=400)

        logger.info(
            f"📦 Parsed request | chat_id: {chat_id} | files: {[f['filename'] for f in files]}")

        # Отправка текста
        if text.strip():
            msg_data = {"chat_id": chat_id, "text": text}
            async with ClientSession() as session:
                async with session.post(
                    f"https://api.telegram.org/bot{TG_API_TOKEN}/sendMessage", json=msg_data
                ) as resp:
                    msg_result = await resp.json()
                    logger.info(f"✅ Telegram message sent: {msg_result}")

        # Отправка файлов
        if files:
            async with ClientSession() as session:
                for file in files:
                    form = aiohttp.FormData()
                    form.add_field("chat_id", chat_id)
                    form.add_field(
                        "document", file["content"], filename=file["filename"])

                    logger.info(
                        f"📤 Uploading file {file['filename']} to Telegram...")

                    async with session.post(
                        f"https://api.telegram.org/bot{TG_API_TOKEN}/sendDocument", data=form
                    ) as resp:
                        doc_result = await resp.json()
                        logger.info(
                            f"📎 File {file['filename']} sent: {doc_result}")

        return web.json_response({"status": "ok"})

    except Exception as e:
        logger.exception(f"🔥 Error in handle_post_request: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
