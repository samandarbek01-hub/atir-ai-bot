import os
from flask import Flask, request
import telebot
import httpx

# .env fayldan o'qish
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")  # Grok AI API kaliti
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

GROK_API_URL = "https://api.grok.ai/v1/complete"  # Grok AI endpoint

# AI javobini olish funksiyasi
def ask_grok_ai(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "model": "grok-mantic-1",  # kerakli model
        "temperature": 0.7,
        "max_tokens": 500
    }
    with httpx.Client(timeout=30) as client:
        response = client.post(GROK_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result.get("text", "AI javobini yaratolmadi.")
        else:
            return f"Xatolik {response.status_code}: {response.text}"

# Telegram webhook endpoint
@app.route("/", methods=["POST"])
def webhook():
    json_data = request.get_json()
    if json_data:
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    return "ok", 200

# Oddiy xabarlarni qabul qilish
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, "typing")
    ai_reply = ask_grok_ai(message.text)
    bot.reply_to(message, ai_reply)

if __name__ == "__main__":
    # Render.com URL ni .env ga qo'y
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
