import os
from flask import Flask, request
import telebot
import httpx

# ENV o'zgaruvchilarini o'qish
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# Grok AI endpointi
GROK_API_URL = "https://api.grok.ai/v1/completions"  # o'zingizning endpoint bilan almashtiring

def get_grok_response(prompt):
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": "gpt-4o-mini",  # kerakli model nomini kiriting
        "prompt": prompt,
        "max_tokens": 200
    }

    try:
        response = httpx.post(GROK_API_URL, headers=headers, json=json_data, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Grok AI javobini olish (data formatiga qarab o'zgartirish kerak bo'lishi mumkin)
        return data.get("text") or data.get("output") or "AI javobini olishda xato"
    except Exception as e:
        print("Grok AI xatoligi:", e)
        return "AI javobini olishda xatolik yuz berdi."

# Webhook route
@app.route("/", methods=["POST"])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
    except Exception as e:
        print("Webhook xatoligi:", e)
    return "OK", 200

# Bot message handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print("User so‘rovi:", message.text)
    response_text = get_grok_response(message.text)
    print("AI javobi:", response_text)
    bot.send_message(message.chat.id, response_text)

if __name__ == "__main__":
    # Render.com yoki boshqa hosting URL sini qo‘shing
    webhook_url = "https://atir-ai-bot-1.onrender.com/"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

    # Flask app ishga tushurish
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
