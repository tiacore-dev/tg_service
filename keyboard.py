import logging
import os
from dotenv import load_dotenv
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import types
from aiogram import Bot, F, Router
from request import set_late, get_details
from formatters import format_route_info, format_route_page
from utils import slugify, find_route_by_slug

load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

router_keyboard = Router()


run_chats = os.getenv("ROUTER_CHATS").split(",")
logger.info(f"Доступные пользователи: {run_chats}")
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


def build_city_pagination_keyboard(number, send_slug, rec_slug):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚠️ Сообщить о задержке",
                                  callback_data=f"late:{number}:{send_slug}:{rec_slug}")]
        ]
    )


async def send_routes(user_id, routes, bot: Bot):
    for route in routes:
        number = route["number"]  # ← извлекаем прямо отсюда
        send = slugify(route['sendCity'])
        rec = slugify(route['recCity'])

        text = format_route_info(route)
        await bot.send_message(
            user_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📋 Детали", callback_data=f"details:{number}:{send}:{rec}")],
                    [InlineKeyboardButton(
                        text="⚠️ Сообщить о задержке", callback_data=f"late:{number}")]
                ]
            )
        )


# Обработчик callback-кнопок


@router_keyboard.callback_query(lambda call: call.data.startswith("details"))
async def handle_details(call: types.CallbackQuery):
    try:
        action, number, send_slug, rec_slug = call.data.split(":")
        user_id = call.message.chat.id
        logger.info(
            f"Получен запрос от пользователя {user_id} для номера {number} с действием {action}.")
        details = await get_details(number)
        route = find_route_by_slug(details, send_slug, rec_slug)

        if not route:
            await call.message.edit_text("❌ Маршрут не найден")
            return

        current_text = call.message.text or call.message.caption
        new_text, _, modified = format_route_page([route], 0, current_text)
        new_markup = build_city_pagination_keyboard(
            number, send_slug, rec_slug)

        markup_changed = dict(new_markup) != (
            dict(call.message.reply_markup) if call.message.reply_markup else None)

        if not modified and not markup_changed:
            await call.answer("🔄 Уже на этой странице")
            return

        await call.message.edit_text(
            text=new_text,
            reply_markup=new_markup,
            parse_mode="Markdown"
        )
        await call.answer()

    except Exception as e:
        logger.error(f"Ошибка при пагинации по городам: {e}")


@router_keyboard.callback_query(lambda call: call.data.startswith("late"))
async def handle_inline_button(call: types.CallbackQuery):
    user_id = call.message.chat.id
    action, number = call.data.split(':')  # Убрали text из callback_data
    logger.info(
        f"Получен запрос от пользователя {user_id} для номера {number} с действием {action}.")
    try:

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
