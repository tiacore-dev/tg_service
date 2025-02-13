def format_route_info(data: dict) -> str:
    return (
        f"*🚍 Номер рейса:* `{data['number']}`\n"
        f"*📍 Маршрут:* {data['name']}\n"
        f"*👤 Водитель:* {data['user']}\n"
        f"*🚗 Авто:* {data['auto']}"
    )


# Функция форматирования информации о посылках
def format_parcels(data):
    formatted_text = ""

    for route in data:
        send_city = route['sendCity']
        rec_city = route['recCity']
        parcels = route['parcels']

        # Заголовок блока с отступом
        formatted_text += f"\n📦 *Отправка:* {send_city} → {rec_city}\n\n"

        if not parcels:
            formatted_text += "_Нет посылок_\n\n"
            continue

        # Детали по каждой посылке с пустой строкой между
        for idx, parcel in enumerate(parcels, start=1):
            number = parcel['number']
            customer = parcel['customer']
            # Используем форматирование типа доставки
            del_type = format_delivery_type(parcel['delType'])

            formatted_text += (
                f"{idx}. Номер: {number}\n"
                f"🏢 *{customer}*\n"
                f"🚪 *Тип доставки:* {del_type}\n\n"
            )

    return formatted_text.strip()


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
