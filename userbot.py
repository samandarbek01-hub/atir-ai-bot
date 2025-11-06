# userbot.py (GROK API bilan)
from pyrogram import Client, filters
import httpx
import os

# Variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
PULT_BOT_TOKEN = os.getenv("PULT_BOT_TOKEN")

app = Client("me", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE)
pult = Client("pult", bot_token=PULT_BOT_TOKEN)

TASK = "Sen akasiya atir sotuv menejerisan. Do'stona, o'zbek tilida javob ber. Har doim @beautygateuz_bot ga yo'naltir."

async def ai(text):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROK_KEY')}"},
            json={
                "model": "grok-beta",
                "messages": [
                    {"role": "system", "content": TASK},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.7
            }
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

@app.on_message(filters.private & filters.incoming & ~filters.me & ~filters.bot)
async def from_human(client, message):
    reply = await ai(message.text)
    await message.reply(reply + "\n\nBuyurtma: @beautygateuz_bot")

@pult.on_message(filters.private & filters.command("task"))
async def new_task(client, message):
    global TASK
    TASK = message.text.partition(" ")[2]
    await message.reply(f"Yangi vazifa:\n{TASK}")

@pult.on_message(filters.private & filters.command("code"))
async def get_code(client, message):
    code = message.text.partition(" ")[2]
    with open("code.txt", "w") as f:
        f.write(code)
    await message.reply("Kod saqlandi!")

print("Grok AI Userbot ishlayapti...")
app.run()
