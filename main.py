import telebot
from dotenv import load_dotenv
import os
import requests
import json
from flask import Flask, request
import threading
import logging

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    filename='bot.log',  # Имя файла для логирования
    level=logging.DEBUG,  # Уровень логирования
    format='%(asctime)s - %(levelname)s - %(message)s'  # Формат логов
)

app = Flask(__name__)

tg_api_token = os.getenv('TG_API_TOKEN')
url_tg = f'https://api.telegram.org/bot{tg_api_token}/sendMessage'

headers_tg = {
    'Content-Type': 'application/x-www-form-urlencoded'
}
bot = telebot.TeleBot(tg_api_token)

db_url = os.getenv('DB_URL')
db_add_user_endpoint = os.getenv('DB_ADD_USER_ENDPOINT')
db_sent_message_endpoint = os.getenv('DB_SENT_MESSAGE_ENDPOINT')
headers_db = {'Content-Type': 'application/json'}


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    user_id = user.id
    message_text = message.text
    username = user.username
    message_text = message_text.split(' ')
    
    if len(message_text) > 1:
        key = message_text[1]
    else:
        key = ""

    logging.info(f'User {username} (ID: {user_id}) started the bot with key: {key}')
    
    payload = {"key": key, "username": username, "id": user_id}
    response = requests.post(db_url + db_add_user_endpoint, data=json.dumps(payload), headers=headers_db)
    
    if response.text:
        try:
            response_data = response.json()
            if 'error' in response_data and 'error_msg' in response_data:
                bot.reply_to(message, f"Произошла ошибка авторизации. {response_data['error_msg']}")
                logging.error(f'Authorization error for user {username}: {response_data["error_msg"]}')
            else:
                bot.reply_to(message, "Вы успешно авторизованы!")
                logging.info(f'User {username} (ID: {user_id}) authorized successfully.')
        except json.JSONDecodeError:
            bot.reply_to(message, "Ошибка при обработке ответа от сервера.")
            logging.error('JSON decode error in authorization response.')
    else:
        bot.reply_to(message, "Ошибка запроса к серверу")
        logging.error('Empty response from the server during authorization.')


# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def sent_message(message):
    user = message.from_user.id
    user_id = str(user)
    payload = {"userid": user_id, "text": message.text}
    
    logging.info(f'User ID: {user_id} sent a message: {message.text}')
    
    response = requests.post(db_url + db_sent_message_endpoint, data=json.dumps(payload), headers=headers_db)
    
    if response.text:
        try:
            response_data = response.json()
            if 'error' in response_data and 'error_msg' in response_data:
                bot.reply_to(message, f"Произошла ошибка при отправке сообщения. {response_data['error_msg']}")
                logging.error(f'Message sending error for user {user_id}: {response_data["error_msg"]}')
        except json.JSONDecodeError:
            bot.reply_to(message, "Ошибка при обработке ответа от сервера.")
            logging.error('JSON decode error in message sending response.')
    else:
        bot.reply_to(message, "Ошибка запроса к серверу")
        logging.error('Empty response from the server during message sending.')


# Flask маршруты
@app.route('/')
def home():
    return 'I`m working now!'


@app.route('/sent-message/', methods=['POST'])
def post_request():
    json_data = request.json  # Получение данных из тела POST запроса
    data = {"chat_id": json_data['userid'], "text": json_data['text']}
    response = requests.post(url_tg, data=data, headers=headers_tg)
    
    logging.info(f'Sent message to Telegram: {data}')
    
    return response.json()


# Запуск Flask в отдельном потоке
def run_flask():
    app.run(debug=False, host='0.0.0.0', port=5010)


def run_bot():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    # Запуск Flask в отдельном потоке
    threading.Thread(target=run_flask).start()

    # Запуск Telegram бота в основном потоке
    run_bot()
