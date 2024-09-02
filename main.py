import telebot
from dotenv import load_dotenv
import os
import requests
import json
from flask import Flask, request
import threading

load_dotenv()

app = Flask(__name__)

tg_api_token=os.getenv('TG_API_TOKEN')
url_tg=f'https://api.telegram.org/bot{tg_api_token}/sendMessage'

headers_tg={
        'Content-Type': 'application/x-www-form-urlencoded'
    }
bot = telebot.TeleBot(tg_api_token)


db_url=os.getenv('DB_URL')
db_add_user_endpoint=os.getenv('DB_ADD_USER_ENDPOINT')
db_sent_message_endpoint=os.getenv('DB_SENT_MESSAGE_ENDPOINT')
headers_db={'Content-Type': 'application/json'}


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    user_id=user.id
    message_text=message.text
    username=user.username
    if len(message_text)>7:
        message_text=message_text.split(' ')
        key=message_text[1]
        
        # Отправка ответа пользователю (по желанию)
        payload={"key" : key, "username" : username, "id" : user_id}
        response=requests.post(db_url+db_add_user_endpoint, data=json.dumps(payload), headers=headers_db)
        
        bot.reply_to(message, f"Вы успешно авторизованы! {response.text}")
    else:
        bot.reply_to(message, f"Не получил значение 'key'.")

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def sent_message(message):
    user = message.from_user
    user_id=str(user.id)
    payload={"userid" : user_id, "text" : message.text}
    response=requests.post(db_url+db_sent_message_endpoint,data=json.dumps(payload), headers=headers_db)
    bot.reply_to(message, f"{response.text}")


# Flask маршруты
@app.route('/')
def home():
    return 'I`m working now!'

@app.route('/sent-message/', methods=['POST'])
def post_request():
    json_data = request.json  # Получение данных из тела POST запроса
    data={"chat_id" : json_data['userid'], "text" : json_data['text']}
    response=requests.post(url_tg, data=data, headers=headers_tg)
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