from bale import Bot, Message
from bale.ui import InlineKeyboardMarkup, InlineKeyboardButton, MenuKeyboardMarkup, MenuKeyboardButton
from dotenv import load_dotenv
import os
import logging
from bale import CallbackQuery
import traceback
from database import Database

load_dotenv()
TOKEN = os.getenv("TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")

bot = Bot(token=TOKEN)
db = Database()

# =========================
# STATE
# =========================

waiting_users = set()   # مرحله شماره تلفن
waiting_unit = set()    # مرحله شماره واحد
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

            # ================= ADMIN PANEL =================
            # ================= ADMIN PANEL =================
            if text == "🛠 پنل ادمین":

                is_admin = False

                try:
                    groups = db.get_groups()

                    for group_id in groups:
                        try:
                            admins = await bot.get_chat_administrators(group_id)

                            if any(a.user.user_id == user_id for a in admins):
                                is_admin = True
                                break

                        except Exception:
                            continue

                except Exception as e:
                    log_error("check_admin", e)
                    await message.reply("❌ خطا در بررسی ادمین")
                    return

                if not is_admin:
                    await message.reply("❌ فقط اونر یا ادمین گروه دسترسی دارند")
                    return

                try:
                    users = db.get_all_users()
                except Exception as e:
                    log_error("get_all_users", e)
                    await message.reply("❌ خطا در دیتابیس")
                    return

                if not users:
                    await message.reply("❌ هیچ کاربری ثبت نشده")
                    return

                msg = "📋 لیست کاربران ثبت‌شده:\n\n"

                for u in users:
                    msg += (
                        f"👤 {u[1] or '-'} {u[2] or ''}\n"
                        f"📱 {u[4] or '-'}\n"
                        f"🏢 واحد: {u[5] or '-'}\n"
                        f"━━━━━━━━━━━━━━\n"
                    )

                keyboard = InlineKeyboardMarkup()

                status = db.get_show_unit()

                keyboard.add(
                    InlineKeyboardButton(
                        text=f"{'🟢' if status else '🔴'} نمایش واحد",
                        callback_data="toggle_show_unit"
                    )
                )

                await message.reply(
                    msg,
                    components=keyboard
                )
                return

            # ================= START =================
            if text.startswith("/start"):
                parts = text.split()
                payload = parts[1] if len(parts) > 1 else None

                keyboard = InlineKeyboardMarkup()

                if payload == "register_unit":
                    waiting_users.add(user_id)

                    keyboard = MenuKeyboardMarkup()
                    keyboard.add(
                        MenuKeyboardButton(
                            text="📱 اشتراک شماره تلفن",
                            request_contact=True
                        )
                    )

                    keyboard.add(
                        MenuKeyboardButton(
                            text="🛠 پنل ادمین"
                        )
                    )

                    await message.reply(
                        "📱 شماره تلفن خود را با دکمه زیر ارسال کنید:",
                        components=keyboard
                    )
                    return

                keyboard.add(
                    InlineKeyboardButton(
                        text="🏢 ثبت واحد",
                        url=f"https://ble.ir/{BOT_USERNAME}?start=register_unit"
                    )
                )

                await message.reply(
                    "👋 سلام\nبرای استفاده باید ثبت‌نام کنی.",
                    components=keyboard
                )
                return

            # ================= STEP 1: PHONE =================
            if user_id in waiting_users:

                contact = getattr(message, "contact", None)

                if not contact:
                    await message.reply("❌ لطفاً از دکمه اشتراک شماره استفاده کن")
                    return

                phone = contact.phone_number

                db.add_phone(
                    user_id,
                    user.first_name,
                    user.last_name,
                    user.username,
                    phone
                )

                waiting_users.discard(user_id)
                waiting_unit.add(user_id)

                await message.reply("📥 شماره ثبت شد\nحالا شماره واحد خود را وارد کنید:")
                return

            # ================= STEP 2: UNIT =================
            if user_id in waiting_unit:

                if not text.isdigit():
                    await message.reply("❌ فقط عدد وارد کن")
                    return

                db.update_unit(user_id, text)

                waiting_unit.discard(user_id)
                warned_users.discard(user_id)

                await message.reply("✅ ثبت‌نام کامل شد 🎉")
                return

            return

        # ================= GROUP =================
        if chat_type in ["group", "supergroup"]:

            db.add_group(message.chat.chat_id)

            if db.user_exists(user_id):

                if db.get_show_unit():
                    data = {"unit": db.get_unit(user_id) or "نامشخص"}
                    await message.reply(
                        f"🏢 واحد: {data.get('unit','نامشخص')}"
                    )

                return

        # ================= FIRST MESSAGE =================
        # ================= FIRST MESSAGE =================
        if user_id not in warned_users:
            warned_users.add(user_id)

            # حذف اولین پیام کاربر
            try:
                await message.delete()
            except:
                pass

            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    text="🏢 ثبت واحد",
                    url=f"https://ble.ir/{BOT_USERNAME}?start=register_unit"
                )
            )

            username = (
                f"@{user.username}"
                if getattr(user, "username", None)
                else user.first_name
            )

            # ارسال پیام معمولی (نه ریپلای)
            await bot.send_message(
                chat_id=message.chat.chat_id,
                text=f"{username}\n\n⚠️ لطفاً ابتدا ثبت‌نام کنید.",
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

@bot.event
async def on_callback(callback: CallbackQuery):

    if callback.data != "toggle_show_unit":
        return

    state = db.get_show_unit()

    db.set_show_unit(not state)

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text=f"{'🟢' if not state else '🔴'} نمایش واحد",
            callback_data="toggle_show_unit"
        )
    )

    users = db.get_all_users()

    msg = "📋 لیست کاربران ثبت‌شده:\n\n"

    for u in users:
        msg += (
            f"👤 {u[1] or '-'} {u[2] or ''}\n"
            f"📱 {u[4] or '-'}\n"
            f"🏢 واحد: {u[5] or '-'}\n"
            f"━━━━━━━━━━━━━━\n"
        )

    await callback.message.edit(
        text=msg,
        components=keyboard
    )

bot.run()