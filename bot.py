import os
import telebot
import openai
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

# Подключение к базе данных
def connect_db():
    return psycopg2.connect(DATABASE_URL)

# Функция записи транзакции в базу данных
def save_transaction(user_id, amount, category):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO transactions (user_id, amount, category) VALUES (%s, %s, %s)", 
                (user_id, amount, category))
    conn.commit()
    cur.close()
    conn.close()

# Функция запроса статистики
def get_statistics(user_id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT category, SUM(amount) FROM transactions WHERE user_id = %s GROUP BY category", (user_id,))
    stats = cur.fetchall()
    cur.close()
    conn.close()
    return stats

# Обработчик команд
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Я бот для учета финансов. Просто отправь мне сумму и категорию.")

# Обработка сообщений от пользователя
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        
        reply = response["choices"][0]["message"]["content"]
        bot.send_message(message.chat.id, reply)
        
        # Простая логика для записи расходов
        parts = message.text.split()
        if len(parts) >= 2 and parts[0].isdigit():
            amount = float(parts[0])
            category = " ".join(parts[1:])
            save_transaction(message.chat.id, amount, category)
            bot.send_message(message.chat.id, f"✅ Записал: {amount} в категорию '{category}'")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")
        print(e)

# Запуск бота
bot.polling(none_stop=True)
