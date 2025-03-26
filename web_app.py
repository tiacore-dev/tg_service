from aiohttp import web, ClientSession, FormData
from io import BytesIO
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
        body = await request.read()
        content_type = request.headers.get("Content-Type", "")
        match = re.search(r'boundary=([-_a-zA-Z0-9]+)', content_type)
        if not match:
            return web.json_response({"error": "Boundary not found"}, status=400)

        boundary = match.group(1).strip()
        parts = body.split(f"--{boundary}".encode())
        chat_id = None
        text = ""
        files = []

        for part in parts:
            if not part or part == b"--\r\n" or part == b"--":
                continue

            headers_body_split = part.split(b"\r\n\r\n", 1)
            if len(headers_body_split) != 2:
                continue

            headers_raw, content = headers_body_split
            headers_text = headers_raw.decode(errors="ignore")

            # Определяем тип данных
            if 'name="userid"' in headers_text:
                chat_id = content.strip().decode(errors="ignore")
            elif 'name="text"' in headers_text:
                text = content.strip().decode(errors="ignore")
            elif 'filename="' in headers_text:
                filename_match = re.search(r'filename="([^"]+)"', headers_text)
                filename = filename_match.group(
                    1) if filename_match else "unknown"
                file_data = content.strip(b"\r\n")
                files.append({"filename": filename, "content": file_data})

        if not chat_id:
            return web.json_response({"error": "Missing chat_id"}, status=400)

        # Отправка текста
        if text:
            async with ClientSession() as session:
                msg = {"chat_id": chat_id, "text": text}
                async with session.post(f"https://api.telegram.org/bot{TG_API_TOKEN}/sendMessage", json=msg) as resp:
                    await resp.json()

        # Отправка файлов
        if files:
            async with ClientSession() as session:
                for f in files:
                    form = FormData()
                    form.add_field("chat_id", chat_id)
                    form.add_field("document", BytesIO(
                        f["content"]), filename=f["filename"])
                    async with session.post(f"https://api.telegram.org/bot{TG_API_TOKEN}/sendDocument", data=form) as resp:
                        await resp.json()

        return web.json_response({"status": "ok"})

    except Exception as e:
        logger.exception(f"🔥 Error in handle_post_request: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)
