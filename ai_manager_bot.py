# ai_manager_bot.py (YANGI VERSIYA – WEBHOOK + BUSINESS UCHUN)
import os
import json
import time
from dotenv import load_dotenv
import telebot
from telebot import types
import openai
from flask import Flask, request  # Webhook uchun

load_dotenv()

# .env dan olish
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
SALES_BOT = os.getenv("SALES_BOT_USERNAME", "@beautygateuz_bot")

if not TOKEN or not OPENAI_KEY or ADMIN_ID == 0:
    raise SystemExit("Iltimos .env faylini to'ldiring!")

openai.api_key = OPENAI_KEY
bot = telebot.TeleBot(TOKEN)

# Flask server
app = Flask(__name__)
DATA_FILE = "projects_store.json"

# --- Data helpers ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"projects": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return int(user_id) == ADMIN_ID

# --- OpenAI ---
def ask_openai_system(prompt, max_tokens=300):
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Siz professional sotuv menejeri. Qisqa, do'stona, o'zbek tilida javob bering. Har doim sotuv botga yo'naltiring."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("OpenAI error:", e)
        return "Kechirasiz, hozir AI javob bera olmayapti. Iltimos keyinroq urining."

# --- Bot commands ---
@bot.message_handler(commands=['start'])
def cmd_start(m):
    txt = ("Salom! Men sizning AI-Assistentingizman.\n\n"
           "Foydalanuvchi sifatida:\n"
           "- /info <project> — loyiha haqida\n"
           "- /help — yordam\n\n"
           "Admin: /addproject")
    bot.reply_to(m, txt)

@bot.message_handler(commands=['help', 'info', 'projects', 'addproject', 'setinfo', 'setredirect', 'setadmin'])
def handle_commands(m):
    # Barcha komandalarni bu yerga yo'naltiramiz
    text = m.text
    if text.startswith("/info"):
        parts = text.split(maxsplit=1)
        name = parts[1] if len(parts) > 1 else ""
        if not name:
            bot.reply_to(m, "Iltimos: /info <project_name>")
            return
        data = load_data()
        proj = data.get("projects", {}).get(name)
        if not proj:
            bot.reply_to(m, f"'{name}' topilmadi.")
            return
        prompt = f"Loyiha: {name}\nMa'lumot: {proj.get('info','')}\nFoydalanuvchi: {m.from_user.first_name}\nJavob: qisqa, do'stona, 3 afzallik, sotuv botga yo'naltir: {proj.get('sales_bot', SALES_BOT)}"
        ai = ask_openai_system(prompt)
        bot.reply_to(m, ai)

    elif text.startswith("/addproject"):
        if not is_admin(m.from_user.id): 
            bot.reply_to(m, "Faqat admin!")
            return
        parts = text.split(maxsplit=1)
        name = parts[1] if len(parts) > 1 else ""
        if not name:
            bot.reply_to(m, "/addproject <name>")
            return
        data = load_data()
        data["projects"][name] = {"info": "", "sales_bot": SALES_BOT, "created_at": time.time()}
        save_data(data)
        bot.reply_to(m, f"✅ '{name}' yaratildi. /setinfo {name}")

    # Boshqa admin komandalar (qisqartirildi, kerak bo'lsa qo'shing)
    else:
        bot.reply_to(m, "Noma'lum buyruq. /help")

# --- Oddiy matn xabarlar ---
@bot.message_handler(func=lambda m: True)
def handle_text(m):
    if os.path.exists("pending_info.json"):
        with open("pending_info.json", "r") as f:
            pend = json.load(f)
        if pend["admin"] == m.from_user.id:
            project = pend["project"]
            data = load_data()
            data["projects"][project]["info"] = m.text
            save_data(data)
            os.remove("pending_info.json")
            bot.reply_to(m, f"✅ '{project}' uchun ma'lumot saqlandi.")
            return

    data = load_data()
    projects = list(data["projects"].keys())
    if len(projects) == 1:
        p = projects[0]
        proj = data["projects"][p]
        prompt = f"Foydalanuvchi: {m.text}\nLoyiha: {p}\nMa'lumot: {proj.get('info','')}\nJavob: do'stona, 2 afzallik, sotuv botga yo'naltir: {proj.get('sales_bot', SALES_BOT)}"
        ai = ask_openai_system(prompt)
        bot.reply_to(m, ai)
    else:
        kb = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for p in projects:
            kb.add(p)
        bot.send_message(m.chat.id, "Qaysi loyiha haqida?", reply_markup=kb)

# --- Webhook route ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid', 403

@app.route('/')
def index():
    return "Bot ishlayapti!"

# --- Deploy uchun ---
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))  # Render PORT ni beradi
    print(f"Bot ishlayapti... Listening on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)

