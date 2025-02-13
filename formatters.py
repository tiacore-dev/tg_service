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

        # Заголовок блока
        formatted_text += f"\n📦 *Отправка:* {send_city} → {rec_city}\n"

        if not parcels:
            formatted_text += "_Нет посылок_\n"
            continue

        # Детали по каждой посылке
        for idx, parcel in enumerate(parcels, start=1):
            number = parcel['number']
            customer = parcel['customer']
            del_type = parcel['delType']

            formatted_text += f"{idx}. `{number}` - {customer} {format_delivery_type(del_type)}\n"

    return formatted_text


# Функция отображения типа доставки
def format_delivery_type(del_type):
    if "Склад-Дверь" in del_type:
        return "🏠 Склад-Дверь"
    elif "Склад-Склад" in del_type:
        return "🏢 Склад-Склад"
    elif "Дверь-Склад" in del_type:
        return "🚪 Дверь-Склад"
    return del_type
