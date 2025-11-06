# ai_manager_bot.py (Admin boshqaruv + tabiiy AI)
import os
import json
from dotenv import load_dotenv
import telebot
from openai import OpenAI
from flask import Flask, request
import httpx

load_dotenv()

# ================== Konfiguratsiya ==================
TOKEN = os.getenv("TELEGRAM_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))

if not TOKEN or not XAI_API_KEY or ADMIN_ID == 0:
    raise SystemExit("Xato: .env faylini to'ldiring!")

DATA_FILE = "prompt_store.json"

# ================== Grok Client ==================
try:
    client = OpenAI(
        api_key=XAI_API_KEY,
        base_url="https://api.x.ai/v1",
        http_client=httpx.Client()
    )
    print("Grok API muvaffaqiyatli ulandi!")
except Exception as e:
    print(f"Grok API ulashda xato: {e}")
    client = None

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ================== Helper Functions ==================
def load_prompt():
    if not os.path.exists(DATA_FILE):
        # Default prompt
        return (
            "Siz professional sotuvchi AI. Foydalanuvchiga do'stona va tabiiy javob bering. "
            "Foydalanuvchi mahsulot, aksiya yoki xarid haqida so‘rasa, aniq va sodda javob bering. "
            "Foydalanuvchini majburlamay, faqat kerak bo‘lsa sotuvga yo‘naltiring. "
            "Foydalanuvchiga g‘oyib reklama qilmasdan, tabiiy suhbat qiling."
        )
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("prompt", "")

def save_prompt(prompt):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"prompt": prompt}, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return int(user_id) == ADMIN_ID

# ================== Bot Commands ==================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    if is_admin(m.from_user.id):
        bot.send_message(m.chat.id, "Salom, admin!\n/setprompt — AI xulqini va mahsulot ma’lumotlarini yangilash")
    else:
        bot.send_message(m.chat.id, "Salom! Men sizning AI yordamchingizman.\nSavolingizni yozing — javob beraman!")

@bot.message_handler(commands=['setprompt'])
def cmd_setprompt(m):
    if not is_admin(m.from_user.id):
        bot.send_message(m.chat.id, "Bu buyruq faqat admin uchun!")
        return
    bot.send_message(m.chat.id, "Yangi ko‘rsatma/prompt yuboring (mahsulot, aksiya va AI xulqi uchun):")
    bot.register_next_step_handler(m, save_new_prompt)

def save_new_prompt(m):
    if not is_admin(m.from_user.id):
        return
    new_prompt = m.text.strip()
    save_prompt(new_prompt)
    bot.send_message(m.chat.id, f"Yangi ko‘rsatma saqlandi:\n\n{new_prompt}")

# ================== Foydalanuvchi xabarlarini AI bilan ishlash ==================
@bot.message_handler(func=lambda m: True)
def handle_all(m):
    if m.chat.type not in ['private', 'group', 'supergroup']:
        return

    user_msg = m.text
    system_prompt = load_prompt()

    # Grok Chat so‘rovi
    if client is None:
        ai_reply = "Kechirasiz, AI xizmati hozir ishlamayapti."
    else:
        try:
            resp = client.chat.completions.create(
                model="grok-3-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=250,
                temperature=0.8
            )
            ai_reply = resp.choices[0].message.content.strip()
        except Exception as e:
            print("GROK XATOLIK:", str(e))
            ai_reply = "Kechirasiz, hozir javob bera olmayapman."

    # Javob yuborish
    try:
        bot.send_message(m.chat.id, ai_reply)
    except Exception as e:
        print("Javob yuborish xato:", e)

# ================== Webhook ==================
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

# ================== Run ==================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Grok bot ishlayapti... Listening on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)
