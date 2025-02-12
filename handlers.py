import logging
from datetime import datetime, timedelta
import pytz
from aiogram.types import ReplyKeyboardRemove
from aiogram import Bot, Router, types, F
from request import get_routes, send_request


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Создаем роутер для регистрации хендлеров
router = Router()

# Указываем часовой пояс Новосибирска
tz_novosibirsk = pytz.timezone('Asia/Novosibirsk')


@router.message(F.text == "/keyboard")
async def show_keyboard(message: types.Message):
    from keyboard import run_chats, get_main_keyboard
    user_id = message.from_user.id
    if str(user_id) not in run_chats:
        logger.warning(
            f"Not authorized user trying to get keyboard: {user_id}")
        return
    logger.info(f"Пользователь {user_id} вызвал клавиатуру")
    await message.answer("Выберите опцию:", reply_markup=get_main_keyboard())


@router.message(F.text == "/remove_keyboard")
async def remove_keyboard(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} скрыл клавиатуру")
    await message.answer("Клавиатура скрыта!", reply_markup=ReplyKeyboardRemove())


@router.message(F.text == "Список рейсов на сегодня")
async def handle_button1(message: types.Message, bot: Bot):
    from keyboard import send_routes
    user_id = message.chat.id
    logger.info(f"Пользователь {user_id} нажал 'Список рейсов на сегодня'")

    now = datetime.now(tz_novosibirsk)
    today = now.strftime("%Y-%m-%d")
    logger.info(f"Текущая дата (Новосибирск): {today}")

    routes = await get_routes(today)
    logger.info(f"Получены маршруты на сегодня: {routes}")

    await send_routes(user_id, routes, bot)
    logger.info(f"Отправлены маршруты пользователю {user_id}")


@router.message(F.text == "Список рейсов на вчера")
async def handle_button2(message: types.Message, bot: Bot):
    from keyboard import send_routes
    user_id = message.chat.id
    logger.info(f"Пользователь {user_id} нажал 'Список рейсов на вчера'")

    now = datetime.now(tz_novosibirsk)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"Дата вчерашнего дня (Новосибирск): {yesterday}")

    routes = await get_routes(yesterday)
    logger.info(f"Получены маршруты на вчера: {routes}")

    await send_routes(user_id, routes, bot)
    logger.info(f"Отправлены маршруты пользователю {user_id}")

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
    logger.info(f"Ответ от сервера авторизации: {response_data}")

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
    logger.info(f"Ответ от сервера отправки сообщений: {response_data}")

    if 'error' in response_data and 'error_msg' in response_data:
        await message.answer(f"Ошибка отправки сообщения: {response_data['error_msg']}")
        logger.error(
            f'Message sending error for user {user_id}: {response_data["error_msg"]}')
