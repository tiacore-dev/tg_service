import logging
import os
from dotenv import load_dotenv
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import types
from aiogram import Bot, F, Router
from request import set_late, get_details
from formatters import format_route_info, format_parcels

load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

router_keyboard = Router()

run_chats = os.getenv("ROUTER_CHATS").split(",")
logger.info(f"оступные пользователи: {run_chats}")
# ✅ Отображаем клавиатуру при команде /keyboard


@router_keyboard.message(F.text == "/keyboard")
async def show_keyboard(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) not in run_chats:
        logger.warning(
            f"Not authorized user trying to get keyboard: {user_id}")
        return
    logger.info(f"Пользователь {user_id} вызвал клавиатуру")
    await message.answer("Выберите опцию:", reply_markup=get_main_keyboard())


@router_keyboard.message(F.text == "/remove_keyboard")
async def remove_keyboard(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} скрыл клавиатуру")
    await message.answer("Клавиатура скрыта!", reply_markup=ReplyKeyboardRemove())

# Создаём клавиатуру


def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Список рейсов на сегодня")],
            [KeyboardButton(text="Список рейсов на вчера")]
        ],
        resize_keyboard=True,  # Уменьшает клавиатуру под размер экрана
        one_time_keyboard=False  # Оставляет клавиатуру на экране
    )
    return keyboard


async def send_routes(user_id, routes, bot: Bot):
    for route in routes:
        text = format_route_info(route)
        await bot.send_message(
            user_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📋 Детали", callback_data=f"details:{route['number']}")],
                    [InlineKeyboardButton(
                        text="⚠️ Сообщить о задержке", callback_data=f"late:{route['number']}")]
                ]
            )
        )


# Обработчик callback-кнопок

@router_keyboard.callback_query(lambda call: call.data.split(':')[0] in ["details", "late"])
async def handle_inline_button(call: types.CallbackQuery):
    user_id = call.message.chat.id
    action, number = call.data.split(':')  # Убрали text из callback_data
    logger.info(
        f"Получен запрос от пользователя {user_id} для номера {number} с действием {action}.")

    try:
        if action == "details":
            details = await get_details(number)
            if not details:  # Если сервер вернул `[]` или `None`
                text = "❌ Детали отсутствуют"
            else:
                text = format_parcels(details)
                await call.message.edit_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="⚠️ Сообщить о задержке", callback_data=f"late:{number}")]
                    ])
                )

        elif action == "late":
            await call.message.edit_text(
                text=f"⚠️ Вы уверены, что хотите сообщить о задержке рейса {number}?",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Да", callback_data=f"yes:{number}")],
                    [InlineKeyboardButton(
                        text="❌ Нет", callback_data=f"no:{number}")],
                ])
            )

        await call.answer()

    except Exception as e:
        logger.error(
            f"Ошибка при обработке callback-кнопки от пользователя {user_id}: {e}")


# Обработчик callback-кнопок
@router_keyboard.callback_query(lambda call: call.data.split(':')[0] in ["yes", "no"])
async def handle_yes_no_button(call: types.CallbackQuery):
    user_id = call.message.chat.id
    action, number = call.data.split(':')
    logger.info(
        f"Получен запрос от пользователя {user_id} для номера {number} с действием {action}.")
    try:
        if action == "yes":
            await set_late(number)
            await call.message.edit_text(text=f"Уведомление успешно отправлено для номера рейса {number}")

        elif action == "no":
            await call.message.edit_text(text=f"Уведоление не отправлено для рейса: {number}")

        await call.answer()
    except Exception as e:
        logger.error(
            f"Ошибка при обработке callback-кнопки от пользователя {user_id}: {e}")
