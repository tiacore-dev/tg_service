import logging
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Router, types, F
from request import get_routes, send_request

logger = logging.getLogger(__name__)
# Создаем роутер для регистрации хендлеров
router = Router()

# Указываем часовой пояс Новосибирска
tz_novosibirsk = pytz.timezone('Asia/Novosibirsk')


@router.message(F.text == "Список рейсов на сегодня")
async def handle_button1(message: types.Message, bot: Bot):
    from keyboard import send_routes
    user_id = message.chat.id
    logger.info(
        f"Пользователь {user_id} нажал 'Список рейсов на сегодня'")
    # Получаем текущую дату и время в Новосибирске
    now = datetime.now(tz_novosibirsk)
    # Получаем дату в формате "ДД-ММ-ГГГГ"
    today = now.strftime("%Y-%m-%d")
    routes = await get_routes(today)
    await send_routes(user_id, routes, bot)


@router.message(F.text == "Список рейсов на вчера")
async def handle_button2(message: types.Message, bot: Bot):
    from keyboard import send_routes
    user_id = message.chat.id
    logger.info(
        f"Пользователь {user_id} нажал 'Список рейсов на вчера'")
    # Получаем вчерашнюю дату
    now = datetime.now(tz_novosibirsk)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    routes = await get_routes(yesterday)
    await send_routes(user_id, routes, bot)


# Обработчик команды /start
@router.message(F.text == "/start")
async def send_welcome(message: types.Message):
    user = message.from_user
    user_id = user.id
    username = user.username
    key = message.text.split(' ')[1] if len(
        message.text.split(' ')) > 1 else ""

    logger.info(
        f'User {username} (ID: {user_id}) started the bot with key: {key}')

    payload = {"key": key, "username": username, "id": user_id}
    response_data = await send_request("add_user", payload)

    if 'error' in response_data and 'error_msg' in response_data:
        await message.answer(f"Ошибка авторизации: {response_data['error_msg']}")
        logger.error(
            f'Authorization error for user {username}: {response_data["error_msg"]}')
    else:
        await message.answer("Вы успешно авторизованы!")
        logger.info(
            f'User {username} (ID: {user_id}) authorized successfully.')


# Обработчик текстовых сообщений
@router.message(F.content_type == 'text')
async def sent_message(message: types.Message):
    user_id = str(message.from_user.id)
    payload = {"userid": user_id, "text": message.text}
    logger.info(f'User ID: {user_id} sent a message: {message.text}')

    response_data = await send_request("send_message", payload)
    if 'error' in response_data and 'error_msg' in response_data:
        await message.answer(f"Ошибка отправки сообщения: {response_data['error_msg']}")
        logger.error(
            f'Message sending error for user {user_id}: {response_data["error_msg"]}')
