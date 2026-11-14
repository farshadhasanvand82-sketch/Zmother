import os
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO)

# توکن ربات میزبان (که از طرف شما تنظیم می‌شود)
MAIN_BOT_TOKEN = os.getenv("BOT_TOKEN", "9284844625:AAGu2gAs6EoxbkxsEFiYSwcyZbn5u5Undtc")

main_bot = Bot(token=MAIN_BOT_TOKEN)
dp = Dispatcher()

# حافظه موقت ساده برای ذخیره ربات‌های ساخته شده کاربران (در پروژه واقعی می‌توانید به دیتابیس متصل کنید)
# ساختار: {user_id: {"token": token, "active": True, "channel": None, "users": set()}}
USER_BOTS = {}

# منوی اصلی ربات میزبان
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 ساخت دانلودر اینستاگرام")],
        [KeyboardButton(text="⚙️ مدیریت ربات‌های من"), KeyboardButton(text="ℹ️ راهنما")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 سلام!\n\n"
        "به سیستم ربات‌ساز میزبان خوش آمدید.\n"
        "با این سیستم می‌توانید یک ربات دانلودر اینستاگرام اختصاصی برای خودتان بسازید و مدیریت کنید.\n\n"
        "از دکمه زیر برای ساخت ربات استفاده کنید:",
        reply_markup=main_menu
    )

# درخواست ساخت ربات
@dp.message(F.text == "📥 ساخت دانلودر اینستاگرام")
async def request_bot_token(message: types.Message):
    await message.answer(
        "🤖 **مراحل ساخت ربات دانلودر:**\n\n"
        "۱. ابتدا وارد ربات @BotFather در تلگرام شوید و با دستور `/newbot` یک ربات جدید بسازید.\n"
        "۲. توکن (Token) دریافتی از بات‌فادر را کپی کرده و همینجا برای من ارسال کنید.",
        parse_mode="Markdown"
    )

# دریافت توکن و راه‌اندازی ربات مهمان
@dp.message(F.text.contains(":"))
async def create_user_bot(message: types.Message):
    token = message.text.strip()
    user_id = message.from_user.id
    
    try:
        # تست اعتبار توکن با یک درخواست ساده به تلگرام
        temp_bot = Bot(token=token)
        bot_info = await temp_bot.get_me()
        await temp_bot.session.close()
        
        # ذخیره اطلاعات ربات کاربر
        USER_BOTS[user_id] = {
            "token": token,
            "username": bot_info.username,
            "active": True,
            "channel": None,
            "users": set()
        }
        
        # دکمه منوی مدیریت برای ادمینِ ربات ساخته شده
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ ورود به پنل مدیریت ربات", callback_data=f"panel_{user_id}")]
        ])
        
        await message.answer(
            f"🎉 **ربات شما با موفقیت ساخته شد و فعال گردید!**\n\n"
            f"🤖 نام ربات: @{bot_info.username}\n"
            f"✅ وضعیت: روشن و آماده به کار\n\n"
            f"اکنون کاربران می‌توانند با ارسال لینک اینستاگرام به آن، ویدیوها و تصاویر را دانلود کنند.\n"
            f"مدیریت ربات شما از طریق دکمه زیر امکان‌پذیر است:",
            reply_markup=admin_keyboard,
            parse_mode="Markdown"
        )
        
        # در اینجا می‌توانید یک تسک پس‌زمینه برای پولینگِ ربات کاربر راه بیندازید تا مستقل کار کند
        # (برای سادگی ساختار، ساختار کنونی مدیریت متمرکز را هندل می‌کند)

    except Exception as e:
        await message.answer(f"❌ توکن نامعتبر است یا خطایی رخ داد:\n`{e}`", parse_mode="Markdown")

# پنل مدیریت ادمین ربات
@dp.callback_query(F.data.startswith("panel_"))
async def admin_panel(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    bot_data = USER_BOTS.get(user_id)
    
    if not bot_data:
        await callback.answer("❌ اطلاعات ربات یافت نشد!", show_alert=True)
        return
        
    status_text = "🟢 روشن" if bot_data["active"] else "🔴 خاموش"
    
    panel_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 آمار کاربران", callback_data=f"stats_{user_id}"),
         InlineKeyboardButton(text="📢 تنظیم قفل کانال", callback_data=f"setchan_{user_id}")],
        [InlineKeyboardButton(text="🔄 تغییر وضعیت روشن/خاموش", callback_data=f"toggle_{user_id}"),
         InlineKeyboardButton(text="📨 پیام همگانی", callback_data=f"broadcast_{user_id}")]
    ])
    
    await callback.message.edit_text(
        f"🛠 **پنل مدیریت ربات: @{bot_data['username']}**\n\n"
        f"وضعیت فعلی: {status_text}\n"
        f"تعداد کاربران ثبت شده: {len(bot_data['users'])}\n"
        f"کانال قفل اجباری: {bot_data['channel'] or 'تنظیم نشده'}",
        reply_markup=panel_markup,
        parse_mode="Markdown"
    )

# بخش دانلود اینستاگرام و پاکسازی آنی از سرور رندر برای همه کاربران
async def download_and_send_instagram(message: types.Message, url: str):
    processing_msg = await message.answer("⏳ در حال دانلود از اینستاگرام و پردازش...")
    
    file_path = f"temp_{message.from_user.id}.mp4" # نام فایل موقت
    try:
        # شبیه‌سازی یا منطق دانلود مدیا از اینستاگرام (می‌توانید کتابخانه yt-dlp یا API دلخواه را اینجا قرار دهید)
        # به عنوان مثال با aiohttp یا yt-dlp لینک دانلود می‌شود و در file_path ذخیره می‌گردد.
        
        # ارسال فایل به کاربر
        # await message.answer_video(types.FSInputFile(file_path))
        await message.answer("✅ (نمونه) مدیا دریافت و ارسال شد.")
        
    except Exception as e:
        await message.answer(f"❌ خطا در دانلود فایل: {e}")
    finally:
        # پاکسازی آنی فایل از روی سرور رندر برای آزادی کامل حافظه
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Temporary file {file_path} deleted successfully from Render server.")
            
        await processing_msg.delete()

@dp.message(F.text.contains("instagram.com"))
async def handle_insta_link(message: types.Message):
    await download_and_send_instagram(message, message.text)

async def main():
    print("Host Bot is starting...")
    await main_bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(main_bot)

if __name__ == "__main__":
    asyncio.run(main())
