# USERBOT + PULT (1 fayl ichida)
from pyrogram import Client, filters
import openai
import os

# Render Variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
PULT_BOT_TOKEN = os.getenv("PULT_BOT_TOKEN")  # yangi
openai.api_key = os.getenv("OPENAI_KEY")

app = Client("me", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE)
pult = Client("pult", bot_token=PULT_BOT_TOKEN)  # pult bot

# Vazifa (default)
TASK = "Sen akasiya atir sotuv menejerisan. Har javobga chegirma qo‘sh."

# AI javob funksiyasi
async def ai(text):
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": TASK},
                  {"role": "user", "content": text}]
    )
    return resp.choices[0].message.content

# 1. Odamdan xabar → AI javob beradi
@app.on_message(filters.private & filters.incoming & ~filters.me & ~filters.bot)
async def from_human(client, message):
    reply = await ai(message.text)
    await message.reply(reply + "\n\n📦 Buyurtma: @beautygateuz_bot")

# 2. Pult botga vazifa berish
@pult.on_message(filters.private & filters.command("task"))
async def new_task(client, message):
    global TASK
    TASK = message.text.partition(" ")[2]
    await message.reply(f"✅ Yangi vazifa:\n{TASK}")

# 3. Pult botga kod yuborish
@pult.on_message(filters.private & filters.command("code"))
async def get_code(client, message):
    code = message.text.partition(" ")[2]
    # Render logs ga yozish uchun faylga saqlaymiz
    with open("code.txt", "w") as f:
        f.write(code)
    await message.reply("✅ Kod qabul qilindi! Userbot davom etyapti.")

print("Userbot + Pult ishlayapti...")
app.run()
