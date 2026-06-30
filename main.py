from bale import Bot, Message
from bale.ui import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import os
import logging
import traceback
from database import Database

load_dotenv()
TOKEN = os.getenv("TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")  # 👈 اضافه شد

bot = Bot(token=TOKEN)
db = Database()

# =========================
# STATE
# =========================

waiting_users = set()
warned_users = set()

logging.basicConfig(
    filename="bot_errors.log",
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def log_error(where, err):
    print(where, err)
    logging.error(f"{where} | {err}\n{traceback.format_exc()}")

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print("BOT ONLINE")

# =========================
# MESSAGE HANDLER
# =========================

@bot.event
async def on_message(message: Message):
    try:
        user = message.author
        if user.is_bot:
            return

        user_id = user.user_id
        chat_type = message.chat.type
        text = message.text or ""

        # ================= PRIVATE =================
        if chat_type == "private":

            # ✅ START HANDLER (برای deep link)
            if text.startswith("/start"):
                parts = text.split()
                payload = parts[1] if len(parts) > 1 else None

                keyboard = InlineKeyboardMarkup()

                if payload == "register_unit":
                    waiting_users.add(user_id)

                    await message.reply("📥 شماره واحد خود را فقط به صورت عددی ارسال کنید:")
                    return

                keyboard.add(
                    InlineKeyboardButton(
                        text="🏢 ثبت واحد",
                        url=f"https://ble.ir/{BOT_USERNAME}?start=register_unit"
                    )
                )

                await message.reply(
                    "👋 سلام\nبرای استفاده باید واحد ثبت کنی.",
                    components=keyboard
                )
                return

            # ================= ثبت عدد =================
            if user_id in waiting_users:
                if not text.isdigit():
                    await message.reply("❌ فقط عدد وارد کن")
                    return

                db.add_user(
                    user_id=user_id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                    unit=text
                )

                waiting_users.discard(user_id)
                warned_users.discard(user_id)

                await message.reply("✅ ثبت شد")
                return

            return

        # ================= GROUP =================
        if chat_type in ["group", "supergroup"]:
            if db.user_exists(user_id):
                data = {"unit": db.get_unit(user_id) or "نامشخص"}
                await message.reply(f"🏢 واحد: {data.get('unit','نامشخص')}")
                return

        # ================= FIRST MESSAGE =================
        if user_id not in warned_users:
            warned_users.add(user_id)

            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    text="🏢 ثبت واحد",
                    url=f"https://ble.ir/{BOT_USERNAME}?start=register_unit"
                )
            )

            await message.reply(
                "⚠️ شماره واحد خود را ثبت کنید \n بعد از ثبت، وضعیت شما فعال می‌شود",
                components=keyboard
            )
            return

        # ================= DELETE NEXT MESSAGES =================
        try:
            await message.delete()
        except:
            pass

    except Exception as e:
        log_error("on_message", e)

# =========================
# RUN
# =========================

bot.run()