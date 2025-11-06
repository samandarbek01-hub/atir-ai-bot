# ai_manager_bot.py (YANGI VERSIYA – ADMIN KO‘RSATMA BERADI)
import os
import json
from dotenv import load_dotenv
import telebot
from telebot import types
import openai
from flask import Flask, request

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
SALES_BOT = os.getenv("SALES_BOT_USERNAME", "@beautygateuz_bot")

if not TOKEN or not OPENAI_KEY or ADMIN_ID == 0:
    raise SystemExit("Iltimos .env faylini to'ldiring!")

openai.api_key = OPENAI_KEY
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Ma'lumotlarni saqlash
DATA_FILE = "prompt_store.json"

def load_prompt():
    if not os.path.exists(DATA_FILE):
        return "Siz professional sotuvchi. Do'stona, qisqa javob bering. Har doim sotuv botga yo'naltiring."
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("prompt", "")

def save_prompt(prompt):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"prompt": prompt}, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return int(user_id) == ADMIN_ID

# /start
@bot.message_handler(commands=['start'])
def cmd_start(m):
    if is_admin(m.from_user.id):
        bot.reply_to(m, "Salom, admin!\n/setprompt — yangi ko‘rsatma berish")
    else:
        bot.reply_to(m, "Salom! Men sizning AI yordamchingizman.\nYozing — javob beraman!")

# /setprompt — admin uchun
@bot.message_handler(commands=['setprompt'])
def cmd_setprompt(m):
    if not is_admin(m.from_user.id):
        bot.reply_to(m, "Bu buyruq faqat admin uchun!")
        return
    bot.reply_to(m, "Yangi ko‘rsatma yuboring (masalan: 'Bugun atir sotuvini reklama qil'):")
    bot.register_next_step_handler(m, save_new_prompt)

def save_new_prompt(m):
    if not is_admin(m.from_user.id):
        return
    new_prompt = m.text.strip()
    save_prompt(new_prompt)
    bot.reply_to(m, f"✅ Yangi ko‘rsatma saqlandi:\n\n{new_prompt}")

# Har qanday xabar — AI javob beradi
@bot.message_handler(func=lambda m: True)
def handle_all(m):
    system_prompt = load_prompt()
    user_msg = m.text

    full_prompt = f"""
Ko‘rsatma: {system_prompt}
Sotuv bot: {SALES_BOT}

Foydalanuvchi xabari: {user_msg}

Javob: qisqa, do'stona, o'zbek tilida, sotuv botga yo'naltiring.
"""

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Siz professional AI yordamchi."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        ai_reply = resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        ai_reply = "Kechirasiz, hozir javob bera olmayapman. Keyinroq urinib ko‘ring."

    bot.reply_to(m, ai_reply)

# Flask webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid', 403

@app.route('/')
def index():
    return "Bot ishlayapti! Admin: /setprompt"

# Render uchun
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    print(f"Bot ishlayapti... Listening on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)
