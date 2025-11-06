from flask import Flask, request
import telebot
import os
import requests

# Muhit o'zgaruvchilarini o'qish
TOKEN = os.getenv("TELEGRAM_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Xabarlarni Grok (XAI) orqali javob berish
def get_ai_reply(user_message):
    try:
        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "grok-2-latest",
            "messages": [
                {"role": "system", "content": "Sen mijozlar bilan tabiiy suhbatlashadigan do'stona menejersen."},
                {"role": "user", "content": user_message}
            ]
        }

        response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            return content.strip()
        else:
            return "AI bilan aloqa o‘rnatilmadi, keyinroq urinib ko‘ring."
    except Exception as e:
        return f"Xatolik: {e}"

# Foydalanuvchi xabar yuborganda ishlaydi
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_text = message.text
    reply = get_ai_reply(user_text)
    bot.reply_to(message, reply)

# Webhook endpoint
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'OK', 200

# Asosiy sahifa (Render health check uchun)
@app.route('/', methods=['GET'])
def index():
    bot.remove_webhook()
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_URL')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    return "🤖 Bot ishga tushdi!", 200

# Serverni ishga tushurish
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
