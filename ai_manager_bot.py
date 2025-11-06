# ai_manager_bot.py (GROK + 502 XATOSI TUZATILGAN)
import os
import json
from dotenv import load_dotenv
import telebot
from telebot import types
from openai import OpenAI
from flask import Flask, request
import httpx

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
SALES_BOT = os.getenv("SALES_BOT_USERNAME", "@beautygateuz_bot")

if not TOKEN or not XAI_API_KEY or ADMIN_ID == 0:
    print("XATO: .env faylida XAI_API_KEY yoki boshqa kerakli o'zgaruvchi yo'q!")
    raise SystemExit("Xato: .env faylini to'ldiring!")

# Grok client — http_client bilan, proxies yo'q
try:
    client = OpenAI(
        api_key=XAI_API_KEY,
        base_url="https://api.x.ai/v1",
        http_client=httpx.Client()  # proxies=None emas, faqat httpx.Client()
    )
    print("Grok API muvaffaqiyatli ulandi!")
except Exception as e:
    print(f"Grok API ulashda xato: {e}")
    client = None

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

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

# /setprompt
@bot.message_handler(commands=['setprompt'])
def cmd_setprompt(m):
    if not is_admin(m.from_user.id):
        bot.reply_to(m, "Bu buyruq faqat admin uchun!")
        return
    bot.reply_to(m, "Yangi ko‘rsatma yuboring:")
    bot.register_next_step_handler(m, save_new_prompt)

def save_new_prompt(m):
    if not is_admin(m.from_user.id):
        return
    new_prompt = m.text.strip()
    save_prompt(new_prompt)
    bot.reply_to(m, f"Yangi ko‘rsatma saqlandi:\n\n{new_prompt}")

# HAR QANDAY XABAR
@bot.message_handler(func=lambda m: True)
def handle_all(m):
    if m.chat.type not in ['private', 'business', 'group', 'supergroup']:
        return

    user_msg = m.text
    system_prompt = load_prompt()

    full_prompt = f"""
Ko‘rsatma: {system_prompt}
Sotuv bot: {SALES_BOT}

Foydalanuvchi: {user_msg}

Javob: o'zbek tilida, do'stona, qisqa, sotuvga yo'naltiring.
"""

    # Grok javob
    if client is None:
        ai_reply = "Kechirasiz, AI xizmati hozir ishlamayapti."
    else:
        try:
            resp = client.chat.completions.create(
                model="grok-3-mini",
                messages=[
                    {"role": "system", "content": "Siz professional AI sotuvchi."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            ai_reply = resp.choices[0].message.content.strip()
        except Exception as e:
            print("GROK XATOLIK:", str(e))
            ai_reply = "Kechirasiz, hozir javob bera olmayapman."

    # Javob yuborish
    try:
        if m.chat.type == 'business':
            bot.send_message(m.chat.id, ai_reply)
        else:
            bot.reply_to(m, ai_reply)
    except Exception as e:
        print("Javob yuborish xato:", e)

# Webhook
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
    return "Grok AI bot ishlayapti! Admin: /setprompt"

# Render
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    print(f"Grok bot ishlayapti... Listening on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)
