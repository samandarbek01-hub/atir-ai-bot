from pyrogram import Client, filters
import openai
import os

# Render Variables dan olish
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_KEY

app = Client("my_account", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE)

SALES_BOT = "@beautygateuz_bot"

async def ai_response(text):
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen akasiya atir sotuv menejerisan. Do'stona, o'zbek tilida javob ber. Har doim @beautygateuz_bot ga yo'naltir."},
                {"role": "user", "content": text}
            ],
            max_tokens=200
        )
        return resp.choices[0].message.content
    except:
        return "Kechirasiz, hozir javob bera olmayapman."

@app.on_message(filters.private & ~filters.me)
async def handle_private(client, message):
    ai_reply = await ai_response(message.text)
    await message.reply(ai_reply + f"\n\nBuyurtma uchun: {SALES_BOT}")

print("Userbot ishlayapti...")
app.run()
