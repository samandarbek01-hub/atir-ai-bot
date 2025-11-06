import os
import telebot
from flask import Flask, request
from dotenv import load_dotenv
import httpx

# 🔹 .env faylni o‘qish
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")
XAI_API_KEY = os.getenv("XAI_API_KEY")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 🔹 Grok (xAI) API orqali javob olish funksiyasi
def get_ai_reply(message_text):
    try:
        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "grok-beta",  # yoki "grok-2-latest" bo‘lishi mumkin
            "messages": [
                {"role": "system", "content": "Sen yordamchi asistentsan, reklama qilma, insondek gapir."},
                {"role": "user", "content": message_text}
            ]
        }

        response = httpx.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI xatosi:", e)
        return "Kechirasiz, hozircha javob bera olmadim 😔"

# 🔹 Oddiy foydalanuvchi xabariga javob
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_text = message.text

    # Admin uchun maxsus buyruqlar
    if str(message.chat.id) == str(ADMIN_ID):
        if user_text.startswith("/send"):
            try:
                _, user_id, msg = user_text.split(" ", 2)
                bot.send_message(int(user_id), msg)
                bot.reply_to(message, "✅ Xabar yuborildi!")
            except:
                bot.reply_to(message, "❌ Foydalanish: /send <user_id> <xabar>")
            return

    # Oddiy foydalanuvchilar uchun AI javobi
    reply = get_ai_reply(user_text)
    bot.send_message(message.chat.id, reply)


# 🔹 Flask orqali Telegram webhookni boshqarish
@app.route('/', methods=['GET'])
def index():
    bot.remove_webhook()

    base_url = os.getenv('RENDER_EXTERNAL_URL', '').strip()
    if not base_url.startswith("https://"):
        base_url = f"https://{base_url}"

    webhook_url = f"{base_url}/{TOKEN}"
    bot.set_webhook(url=webhook_url)

    return f"🤖 Bot webhook o‘rnatildi: {webhook_url}", 200


@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
