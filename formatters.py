MAX_MESSAGE_LENGTH = 4096


def format_route_info(data: dict) -> str:
    return (
        f"*🚍 Номер рейса:* `{data['number']}`\n"
        f"*📍 Маршрут:* {data['name']}\n"
        f"*👤 Водитель:* {data['user']}\n"
        f"*🚗 Авто:* {data['auto']}"
    )


# Функция отображения типа доставки
def format_delivery_type(del_type):
    if "Склад-Дверь" in del_type:
        return "🏠 Склад-Дверь"
    elif "Склад-Склад" in del_type:
        return "🏢 Склад-Склад"
    elif "Дверь-Склад" in del_type:
        return "🚪 Дверь-Склад"
    elif "Дверь-Дверь" in del_type:  # Добавили новый тип доставки
        return "🏡 Дверь-Дверь"
    return del_type  # Оставляем оригинальный текст, если нет совпадения


def format_route_page(data, page, previous_text: str | None = None):
    if page < 0 or page >= len(data):
        return "❌ Неверная страница", 1, True

    route = data[page]
    send_city = route["sendCity"]
    rec_city = route["recCity"]
    parcels = route["parcels"]

    text = f"📦 *Отправка:* {send_city} → {rec_city}\n\n"

    if not parcels:
        text += "_Нет посылок_"
    else:
        for idx, parcel in enumerate(parcels, start=1):
            text += (
                f"{idx}. Номер: {parcel['number']}\n"
                f"🏢 *{parcel['customer']}*\n"
                f"🚪 *Тип доставки:* {format_delivery_type(parcel['delType'])}\n"
                f"📦 *Мест:* {parcel['count']}\n\n"
            )

    text = text.strip()

    # Проверка: отличается ли текст
    modified = text != (previous_text or "").strip()

    return text, len(data), modified


def split_long_text(text: str, max_length=MAX_MESSAGE_LENGTH) -> list[str]:
    lines = text.split("\n")
    chunks = []
    current = ""

    for line in lines:
        # учтём перенос строки
        if len(current) + len(line) + 1 > max_length:
            chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"

    if current:
        chunks.append(current.strip())

    return chunks
