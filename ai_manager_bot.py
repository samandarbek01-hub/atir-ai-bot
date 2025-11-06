import os
from flask import Flask, request, jsonify
import telebot
import httpx
from dotenv import load_dotenv  # .env uchun
import json
from datetime import datetime

load_dotenv()  # .env o'qish

# ENV o'zgaruvchilari
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", 0))

# Bot va app
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# xAI Grok API endpoint (2025 yil holatiga ko'ra)
GROK_API_URL = "https://api.x.ai/v1/chat/completions"  # To'g'ri endpoint

# Multi-turn uchun chat history (oddiy dict, production'da DB ishlatish kerak)
chat_history = {}

def get_grok_response(prompt, user_id):
    # Multi-turn: oldin xabarlarni qo'shish
    history = chat_history.get(user_id, [])
    messages = history + [{"role": "user", "content": prompt}]
    
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": "grok-beta",  # xAI modeli (2025 da mavjud)
        "messages": messages,
        "max_tokens": 500,  # Ko'proq token
        "temperature": 0.7
    }
    
    try:
        response = httpx.post(GROK_API_URL, headers=headers, json=json_data, timeout=30)
        response.raise_for_status()
        data = response.json()
        ai_reply = data['choices'][0]['message']['content']  # To'g'ri format
        
        # History yangilash
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": ai_reply})
        chat_history[user_id] = history[-10:]  # Oxirgi 10 xabar (xotira tejash)
        
        return ai_reply
    except Exception as e:
        print(f"Grok AI xatoligi: {e}")
        return "AI javob berishda xatolik yuz berdi. Keyinroq urinib ko'ring."

# Webhook route (xavfsizlik uchun token-based)
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Webhook xatoligi: {e}")
        return jsonify({"error": str(e)}), 500

# Message handler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print(f"User so'rovi ({message.from_user.id}): {message.text}")
    
    # Admin tekshirish
    if ADMIN_TELEGRAM_ID and message.from_user.id == ADMIN_TELEGRAM_ID:
        bot.reply_to(message, f"Admin salom! Javob: {get_grok_response(message.text, message.from_user.id)}")
        return
    
    # Oddiy foydalanuvchi
    response_text = get_grok_response(message.text, message.from_user.id)
    print(f"AI javobi: {response_text}")
    bot.reply_to(message, response_text)

if __name__ == "__main__":
    # Webhook o'rnatish (Render URL)
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'your-app.onrender.com')}/{TELEGRAM_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print(f"Webhook o'rnatildi: {webhook_url}")
    
    # Flask ishga tushirish
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
