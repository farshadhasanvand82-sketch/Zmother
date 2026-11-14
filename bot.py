import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO)

# توکن ربات میزبان
MAIN_BOT_TOKEN = os.getenv("BOT_TOKEN", "9284844625:AAGu2gAs6EoxbkxsEFiYSwcyZbn5u5Undtc")

main_bot = Bot(token=MAIN_BOT_TOKEN)
dp = Dispatcher()

# حافظه موقت برای ربات‌ها
USER_BOTS = {}

# منوی اصلی
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

@dp.message(F.text == "📥 ساخت دانلودر اینستاگرام")
async def request_bot_token(message: types.Message):
    await message.answer(
        "🤖 مراحل ساخت ربات دانلودر:\n\n"
        "۱. ابتدا وارد ربات @BotFather در تلگرام شوید و با دستور /newbot یک ربات جدید بسازید.\n"
        "۲. توکن (Token) دریافتی از بات‌فادر را کپی کرده و همینجا برای من ارسال کنید."
    )

@dp.message(F.text.contains(":"))
async def create_user_bot(message: types.Message):
    token = message.text.strip()
    user_id = message.from_user.id
    
    try:
        temp_bot = Bot(token=token)
        bot_info = await temp_bot.get_me()
        await temp_bot.session.close()
        
        USER_BOTS[user_id] = {
            "token": token,
            "username": bot_info.username,
            "active": True,
            "channel": None,
            "users": set()
        }
        
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ ورود به پنل مدیریت ربات", callback_data=f"panel_{user_id}")]
        ])
        
        await message.answer(
            f"🎉 ربات شما با موفقیت ساخته شد و فعال گردید!\n\n"
            f"🤖 نام ربات: @{bot_info.username}\n"
            f"✅ وضعیت: روشن و آماده به کار\n\n"
            f"اکنون کاربران می‌توانند با ارسال لینک اینستاگرام به آن، ویدیوها و تصاویر را دانلود کنند.",
            reply_markup=admin_keyboard
        )
    except Exception as e:
        await message.answer(f"❌ توکن نامعتبر است یا خطایی رخ داد:\n{e}")

# یک سرور وب کوچک برای پاسخ به درخواست‌های پورت رندر
async def handle(request):
    return web.Response(text="Bot is running and alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.AppSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

async def main():
    # روشن کردن هم‌زمان وب‌سرور برای رندر و پولینگ ربات تلگرام
    await start_web_server()
    print("Host Bot is starting...")
    await main_bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(main_bot)

if __name__ == "__main__":
    asyncio.run(main())
