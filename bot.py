import os
import json
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

# ⚙️ توکن و آیدی از متغیرهای محیطی خونده می‌شن (برای Koyeb)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# 📁 فایل‌های ذخیره‌سازی
USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"
BLOCKED_FILE = "blocked.json"


# ═══════════════════════════════════════
# 📁 توابع دیتابیس
# ═══════════════════════════════════════

def load_json(filename, default=None):
    if default is None:
        default = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default


def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_users():
    return load_json(USERS_FILE, {})


def save_user(user):
    users = get_users()
    users[str(user.id)] = {
        "name": user.full_name,
        "username": user.username or "",
        "first_seen": users.get(str(user.id), {}).get(
            "first_seen", datetime.now().isoformat()
        ),
        "last_seen": datetime.now().isoformat()
    }
    save_json(USERS_FILE, users)


def get_blocked():
    return load_json(BLOCKED_FILE, [])


def is_blocked(user_id):
    return str(user_id) in get_blocked()


def block_user(user_id):
    blocked = get_blocked()
    if str(user_id) not in blocked:
        blocked.append(str(user_id))
        save_json(BLOCKED_FILE, blocked)


def unblock_user(user_id):
    blocked = get_blocked()
    if str(user_id) in blocked:
        blocked.remove(str(user_id))
        save_json(BLOCKED_FILE, blocked)


# ═══════════════════════════════════════
# 🎛 کیبوردها
# ═══════════════════════════════════════

def user_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📩 ارسال پیام به پشتیبانی")],
            [KeyboardButton("ℹ️ راهنما"), KeyboardButton("🆔 آیدی من")]
        ],
        resize_keyboard=True
    )


def admin_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📊 آمار ربات"), KeyboardButton("📢 ارسال همگانی")],
            [KeyboardButton("👥 لیست کاربران"), KeyboardButton("🚫 لیست بلاک‌شده‌ها")],
            [KeyboardButton("🔙 برگشت به حالت عادی")]
        ],
        resize_keyboard=True
    )


# ═══════════════════════════════════════
# 👤 دستورات کاربر
# ═══════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user)

    if user.id == ADMIN_ID:
        await update.message.reply_text(
            f"سلام ادمین عزیز 👑\n\n"
            f"به پنل مدیریت خوش اومدی.\n"
            f"از دکمه‌های پایین استفاده کن.",
            reply_markup=admin_keyboard()
        )
        return

    if is_blocked(user.id):
        await update.message.reply_text("⛔️ شما از ربات بلاک شده‌اید.")
        return

    await update.message.reply_text(
        f"سلام {user.first_name} 👋\n\n"
        f"به پشتیبانی **Helli Channel** خوش اومدی!\n\n"
        f"هر مشکلی داری، همینجا بگو. تیم پشتیبانی در اسرع وقت جوابت می‌ده 💬",
        reply_markup=user_keyboard(),
        parse_mode="Markdown"
    )


async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🆔 آیدی عددی شما:\n`{user.id}`",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **راهنما**\n\n"
        "🔹 برای ارسال پیام به پشتیبانی، هر متن/عکس/ویدیو/فایلی بفرست.\n"
        "🔹 تیم پشتیبانی به‌زودی جوابت رو می‌ده.\n"
        "🔹 اگه سوالی داری، همینجا بپرس.",
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════
# 📨 دریافت پیام از کاربر
# ═══════════════════════════════════════

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if user.id == ADMIN_ID:
        return

    if is_blocked(user.id):
        await message.reply_text("⛔️ شما از ربات بلاک شده‌اید.")
        return

    save_user(user)

    header = (
        f"📩 **پیام جدید از کاربر**\n\n"
        f"👤 نام: {user.full_name}\n"
        f"🆔 آیدی: `{user.id}`\n"
        f"🔗 یوزرنیم: @{user.username or 'ندارد'}\n"
        f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"━━━━━━━━━━━━━━━"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚫 بلاک کاربر", callback_data=f"block_{user.id}"),
            InlineKeyboardButton("👤 پروفایل", callback_data=f"profile_{user.id}")
        ]
    ])

    try:
        if message.text:
            admin_msg = await context.bot.send_message(
                ADMIN_ID, f"{header}\n\n💬 {message.text}",
                parse_mode="Markdown", reply_markup=keyboard
            )
        elif message.photo:
            admin_msg = await context.bot.send_photo(
                ADMIN_ID, message.photo[-1].file_id,
                caption=f"{header}\n\n🖼 عکس",
                parse_mode="Markdown", reply_markup=keyboard
            )
        elif message.video:
            admin_msg = await context.bot.send_video(
                ADMIN_ID, message.video.file_id,
                caption=f"{header}\n\n🎥 ویدیو",
                parse_mode="Markdown", reply_markup=keyboard
            )
        elif message.voice:
            admin_msg = await context.bot.send_voice(
                ADMIN_ID, message.voice.file_id,
                caption=f"{header}\n\n🎤 پیام صوتی",
                parse_mode="Markdown", reply_markup=keyboard
            )
        elif message.document:
            admin_msg = await context.bot.send_document(
                ADMIN_ID, message.document.file_id,
                caption=f"{header}\n\n📎 فایل: {message.document.file_name}",
                parse_mode="Markdown", reply_markup=keyboard
            )
        elif message.sticker:
            admin_msg = await context.bot.send_sticker(
                ADMIN_ID, message.sticker.file_id
            )
            await context.bot.send_message(
                ADMIN_ID, header, parse_mode="Markdown", reply_markup=keyboard
            )
        elif message.audio:
            admin_msg = await context.bot.send_audio(
                ADMIN_ID, message.audio.file_id,
                caption=f"{header}\n\n🎵 صوتی",
                parse_mode="Markdown", reply_markup=keyboard
            )
        else:
            await message.reply_text("⚠️ این نوع پیام پشتیبانی نمی‌شه.")
            return

        messages = load_json(MESSAGES_FILE, {})
        messages[str(admin_msg.message_id)] = user.id
        save_json(MESSAGES_FILE, messages)

        await message.reply_text(
            "✅ پیامتون ارسال شد.\n"
            "به‌زودی جواب می‌گیرید 🙏",
            reply_markup=user_keyboard()
        )

    except Exception as e:
        print(f"خطا: {e}")
        await message.reply_text("❌ خطا در ارسال پیام. لطفاً بعداً تلاش کنید.")


# ═══════════════════════════════════════
# 👑 توابع ادمین
# ═══════════════════════════════════════

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_users()
    blocked = get_blocked()

    await update.message.reply_text(
        f"📊 **آمار ربات**\n\n"
        f"👥 تعداد کاربران: `{len(users)}`\n"
        f"🚫 بلاک‌شده‌ها: `{len(blocked)}`\n"
        f"✅ فعال: `{len(users) - len(blocked)}`\n"
        f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        parse_mode="Markdown"
    )


async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_users()
    if not users:
        await update.message.reply_text("هنوز کاربری ثبت نشده.")
        return

    text = "👥 **لیست کاربران:**\n\n"
    for i, (uid, info) in enumerate(list(users.items())[:50], 1):
        name = info.get("name", "?")
        uname = info.get("username", "")
        uname_str = f" (@{uname})" if uname else ""
        text += f"{i}. {name}{uname_str}\n   `{uid}`\n"

    if len(users) > 50:
        text += f"\n... و {len(users) - 50} نفر دیگر"

    await update.message.reply_text(text, parse_mode="Markdown")


async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["broadcasting"] = True
    await update.message.reply_text(
        "📢 **ارسال همگانی**\n\n"
        "پیام خودتو بفرست (متن، عکس، ویدیو...).\n"
        "برای لغو، بنویس: `/cancel`",
        parse_mode="Markdown"
    )


async def admin_blocked_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    blocked = get_blocked()
    if not blocked:
        await update.message.reply_text("هیچ کاربری بلاک نشده ✅")
        return

    text = "🚫 **لیست بلاک‌شده‌ها:**\n\n"
    for i, uid in enumerate(blocked, 1):
        text += f"{i}. `{uid}`\n"

    text += "\nبرای آنبلاک کردن، بنویس:\n`/unblock آیدی_کاربر`"
    await update.message.reply_text(text, parse_mode="Markdown")


async def admin_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال:\n`/unblock 123456789`", parse_mode="Markdown")
        return
    try:
        uid = int(context.args[0])
        unblock_user(uid)
        await update.message.reply_text(f"✅ کاربر `{uid}` آنبلاک شد.", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ آیدی نامعتبر.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["broadcasting"] = False
    await update.message.reply_text("لغو شد ✅", reply_markup=admin_keyboard())


# ═══════════════════════════════════════
# 📥 هندلر ادمین
# ═══════════════════════════════════════

async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text

    if text == "📊 آمار ربات":
        await admin_stats(update, context)
        return
    if text == "👥 لیست کاربران":
        await admin_users_list(update, context)
        return
    if text == "📢 ارسال همگانی":
        await admin_broadcast_start(update, context)
        return
    if text == "🚫 لیست بلاک‌شده‌ها":
        await admin_blocked_list(update, context)
        return
    if text == "🔙 برگشت به حالت عادی":
        await update.message.reply_text(
            "برگشت به حالت عادی ✅",
            reply_markup=user_keyboard()
        )
        return

    if context.user_data.get("broadcasting"):
        users = get_users()
        blocked = get_blocked()
        success, failed = 0, 0

        status = await update.message.reply_text(
            f"⏳ در حال ارسال به {len(users)} کاربر..."
        )

        for uid in users.keys():
            if uid in blocked:
                continue
            try:
                await context.bot.copy_message(
                    chat_id=int(uid),
                    from_chat_id=update.effective_chat.id,
                    message_id=update.message.message_id
                )
                success += 1
            except:
                failed += 1

        await status.edit_text(
            f"✅ ارسال شد\n\n"
            f"موفق: {success}\n"
            f"ناموفق: {failed}"
        )
        context.user_data["broadcasting"] = False
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "ℹ️ برای جواب دادن، روی پیام کاربر **ریپلای** کنید.\n"
            "یا از دکمه‌های پایین استفاده کنید.",
            parse_mode="Markdown",
            reply_markup=admin_keyboard()
        )
        return

    replied_id = update.message.reply_to_message.message_id
    messages = load_json(MESSAGES_FILE, {})
    user_id = messages.get(str(replied_id))

    if not user_id:
        await update.message.reply_text(
            "❌ این پیام مربوط به کاربری نیست.\n"
            "(یعنی کاربر پیامش رو پاک کرده یا خیلی وقته)"
        )
        return

    try:
        await context.bot.send_message(
            user_id,
            "📬 **پاسخ پشتیبانی:**",
            parse_mode="Markdown"
        )
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
        await update.message.reply_text("✅ پاسخ برای کاربر ارسال شد.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")


# ═══════════════════════════════════════
# 🔘 دکمه‌های شیشه‌ای
# ═══════════════════════════════════════

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    data = query.data

    if data.startswith("block_"):
        uid = int(data.split("_")[1])
        block_user(uid)
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ آنبلاک", callback_data=f"unblock_{uid}")
            ]])
        )
        await query.message.reply_text(f"🚫 کاربر `{uid}` بلاک شد.", parse_mode="Markdown")

    elif data.startswith("unblock_"):
        uid = int(data.split("_")[1])
        unblock_user(uid)
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚫 بلاک", callback_data=f"block_{uid}")
            ]])
        )
        await query.message.reply_text(f"✅ کاربر `{uid}` آنبلاک شد.", parse_mode="Markdown")

    elif data.startswith("profile_"):
        uid = data.split("_")[1]
        users = get_users()
        info = users.get(uid, {})
        await query.message.reply_text(
            f"👤 **پروفایل کاربر**\n\n"
            f"نام: {info.get('name', '?')}\n"
            f"یوزرنیم: @{info.get('username') or 'ندارد'}\n"
            f"آیدی: `{uid}`\n"
            f"اولین بار: {info.get('first_seen', '?')[:10]}\n"
            f"آخرین بار: {info.get('last_seen', '?')[:10]}",
            parse_mode="Markdown"
        )


# ═══════════════════════════════════════
# 🚀 اجرا
# ═══════════════════════════════════════

def main():
    if not BOT_TOKEN:
        print("❌ خطا: BOT_TOKEN تنظیم نشده!")
        return
    if not ADMIN_ID:
        print("❌ خطا: ADMIN_ID تنظیم نشده!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", show_id))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("unblock", admin_unblock))

    app.add_handler(CallbackQueryHandler(button_callback))

    app.add_handler(MessageHandler(
        filters.User(ADMIN_ID) & ~filters.COMMAND,
        handle_admin_text
    ))

    app.add_handler(MessageHandler(
        ~filters.User(ADMIN_ID) & (
            filters.TEXT | filters.PHOTO | filters.VIDEO |
            filters.VOICE | filters.Document.ALL |
            filters.AUDIO | filters.Sticker.ALL
        ),
        handle_user_message
    ))

    print("🤖 ربات روشن شد...")
    print("✅ همه قابلیت‌ها فعاله!")
    app.run_polling()


if __name__ == "__main__":
    main()
