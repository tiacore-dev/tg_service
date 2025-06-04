import logging
import os

from aiogram import Bot, F, Router, types
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv

from formatters import format_route_info, format_route_page
from request import get_details, set_late

load_dotenv()

# Настройка логирования
logger = logging.getLogger("telegram_bot")

router_keyboard = Router()


run_chats = os.getenv("ROUTER_CHATS").split(",")
logger.info(f"Доступные пользователи: {run_chats}")
# ✅ Отображаем клавиатуру при команде /keyboard


@router_keyboard.message(F.text == "/keyboard")
async def show_keyboard(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) not in run_chats:
        logger.warning(f"Not authorized user trying to get keyboard: {user_id}")
        await message.answer("Перейдите в личные сообщения.")
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
            [KeyboardButton(text="Список рейсов на вчера")],
        ],
        resize_keyboard=True,  # Уменьшает клавиатуру под размер экрана
        one_time_keyboard=False,  # Оставляет клавиатуру на экране
    )
    return keyboard


def build_city_pagination_keyboard(number, page, total_pages):
    buttons = []

    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад", callback_data=f"details:{number}:{page - 1}"
            )
        )
    if page < total_pages - 1:
        buttons.append(
            InlineKeyboardButton(
                text="➡️ Вперёд", callback_data=f"details:{number}:{page + 1}"
            )
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [
                InlineKeyboardButton(
                    text="⚠️ Сообщить о задержке", callback_data=f"late:{number}"
                )
            ],
        ]
    )


async def send_routes(user_id, routes, bot: Bot):
    for route in routes:
        number = route["number"]
        text = format_route_info(route)  # откуда name, user, auto
        await bot.send_message(
            user_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📋 Детали", callback_data=f"details:{number}:0"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⚠️ Сообщить о задержке", callback_data=f"late:{number}"
                        )
                    ],
                ]
            ),
        )


# Обработчик callback-кнопок


@router_keyboard.callback_query(lambda call: call.data.startswith("details"))
async def handle_details(call: types.CallbackQuery):
    try:
        parts = call.data.split(":")
        if len(parts) != 3:
            logger.warning(f"Некорректный callback_data: {call.data}")
            await call.answer("⚠️ Неверный формат", show_alert=True)
            return

        _, number, page = parts
        page = int(page)
        user_id = call.message.chat.id

        logger.info(
            f"[details] Пользователь {user_id} открыл рейс {number}, стр. {page}"
        )

        details = await get_details(number)
        if not details:
            await call.message.edit_text("❌ Манифесты отсутствуют")
            return

        if page < 0 or page >= len(details):
            await call.answer("📄 Страница вне диапазона", show_alert=True)
            return

        current_text = call.message.text or call.message.caption
        text, total_pages, modified = format_route_page(details, page, current_text)
        keyboard = build_city_pagination_keyboard(number, page, total_pages)

        markup_changed = dict(keyboard) != (
            dict(call.message.reply_markup) if call.message.reply_markup else None
        )

        if not modified and not markup_changed:
            await call.answer("🔄 Уже на этой странице")
            return

        await call.message.edit_text(
            text=text, reply_markup=keyboard, parse_mode="Markdown"
        )
        await call.answer()

    except Exception as e:
        logger.error(f"Ошибка при пагинации по городам: {e}")


@router_keyboard.callback_query(lambda call: call.data.startswith("late"))
async def handle_inline_button(call: types.CallbackQuery):
    user_id = call.message.chat.id
    action, number = call.data.split(":")  # Убрали text из callback_data
    logger.info(
        f"Получен запрос от пользователя {user_id} для номера {number} с действием {action}."
    )
    try:
        await call.message.edit_text(
            text=f"⚠️ Вы уверены, что хотите сообщить о задержке рейса {number}?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Да", callback_data=f"yes:{number}")],
                    [InlineKeyboardButton(text="❌ Нет", callback_data=f"no:{number}")],
                ]
            ),
        )
        await call.answer()

    except Exception as e:
        logger.error(
            f"Ошибка при обработке callback-кнопки от пользователя {user_id}: {e}"
        )


# Обработчик callback-кнопок
@router_keyboard.callback_query(lambda call: call.data.split(":")[0] in ["yes", "no"])
async def handle_yes_no_button(call: types.CallbackQuery):
    user_id = call.message.chat.id
    action, number = call.data.split(":")
    logger.info(
        f"Получен запрос от пользователя {user_id} для номера {number} с действием {action}."
    )
    try:
        if action == "yes":
            await set_late(number)
            await call.message.edit_text(
                text=f"Уведомление успешно отправлено для номера рейса {number}"
            )

        elif action == "no":
            await call.message.edit_text(
                text=f"Уведоление не отправлено для рейса: {number}"
            )

        await call.answer()
    except Exception as e:
        logger.error(
            f"Ошибка при обработке callback-кнопки от пользователя {user_id}: {e}"
        )
