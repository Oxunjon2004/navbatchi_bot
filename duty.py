import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.exceptions import ChatNotFound
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Telegram bot tokenini kiriting
API_TOKEN = '7737268583:AAGMGiFqNyDLCd3UgfCOcqZT9DYy1DH5Ak0'  # Bu yerga o'z bot tokeningizni kiriting
# Guruh ID (bu ID ga xabar yuboriladi)
GROUP_ID = -1002103861567  # O'zingizning guruh ID'ingizni kiriting
# Boshlang'ich adminlar ro'yxati (faqat ular botdan foydalanishi mumkin)
admin_list = [5205152968]  # O'z user ID'ingizni kiriting

# Bot va Dispatcher yaratamiz
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# Oldindan belgilangan navbatchilar ro'yxati
duty_list = ['Oxunjon', 'Samandar', 'Ziyodulla', 'Iftihor']

# Hozirgi navbatchini belgilash uchun o'zgaruvchi
current_duty = None

# Adminlar uchun barcha tugmalar
def admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Admin bilan bog'lanish"))
    markup.add(KeyboardButton("Guruhga xabar yuborish"))
    markup.add(KeyboardButton("Navbatchilar ro'yxatini ko'rish"))
    markup.add(KeyboardButton("Bugungi navbatchini bilish"))
    markup.add(KeyboardButton("Guruhga navbatchini yuborish"))  # Yangi tugma qo'shildi
    return markup

# Foydalanuvchilar uchun tugmalar (hammaga ko'rinadi)
def user_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Admin bilan bog'lanish"))
    markup.add(KeyboardButton("Bugungi navbatchini bilish"))
    return markup

# Faqat admin foydalanishi uchun tekshiruv funksiyasi
async def is_authorized(user_id):
    return user_id in admin_list

# /start buyrug'i uchun handler
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if await is_authorized(message.from_user.id):
        await message.reply("Xush kelibsiz! Quyidagi tugmalar yordamida botdan foydalanishingiz mumkin.", reply_markup=admin_keyboard())
    else:
        await message.reply("Xush kelibsiz! Sizga quyidagi tugmalar ko'rsatiladi.", reply_markup=user_keyboard())

# "Admin bilan bog'lanish" tugmasi
@dp.message_handler(lambda message: message.text == "Admin bilan bog'lanish")
async def contact_admin(message: types.Message):
    await message.reply(f"Bot adminiga murojaat qilish uchun quyidagi linkdan foydalaning: https://t.me/Qoqonlik_02")

# "Guruhga xabar yuborish" tugmasi bosilganda
@dp.message_handler(lambda message: message.text == "Guruhga xabar yuborish")
async def ask_for_group_message(message: types.Message):
    if await is_authorized(message.from_user.id):
        await message.reply("Guruhga yuboriladigan xabarni kiriting.")
        dp.register_message_handler(send_group_message, content_types=types.ContentType.TEXT)

# Guruhga xabar yuborish funksiyasi
async def send_group_message(message: types.Message):
    if await is_authorized(message.from_user.id):
        try:
            await bot.send_message(GROUP_ID, message.text)  # Foydalanuvchi yozgan matnni guruhga yuborish
            await message.reply("Xabar guruhga yuborildi.")
        except ChatNotFound:
            await message.reply("Guruh topilmadi.")

# "Navbatchilar ro'yxatini ko'rish" tugmasi
@dp.message_handler(lambda message: message.text == "Navbatchilar ro'yxatini ko'rish")
async def view_duty_list(message: types.Message):
    if await is_authorized(message.from_user.id):
        if not duty_list:
            await message.reply("Hozircha navbatchilar ro'yxati bo'sh.")
        else:
            await message.reply("Navbatchilar ro'yxati:\n" + "\n".join(duty_list))

# "Bugungi navbatchini bilish" tugmasi (hammaga ko'rinadi)
@dp.message_handler(lambda message: message.text == "Bugungi navbatchini bilish")
async def get_today_duty(message: types.Message):
    global current_duty
    if current_duty:
        await message.reply(f"Bugungi navbatchi: {current_duty}")
    else:
        await message.reply("Hozircha navbatchi belgilanmagan.")

# "Guruhga navbatchini yuborish" tugmasi (faqat adminlar uchun ko'rinadi)
@dp.message_handler(lambda message: message.text == "Guruhga navbatchini yuborish")
async def send_duty_to_group(message: types.Message):
    global current_duty
    if await is_authorized(message.from_user.id):
        if current_duty:
            try:
                duty_message = f"{current_duty}, siz bugungi navbatchisiz."
                await bot.send_message(GROUP_ID, duty_message)  # Navbatchini guruhga yuborish
                await message.reply("Bugungi navbatchi guruhga yuborildi.")
            except ChatNotFound:
                await message.reply("Guruh topilmadi.")
        else:
            await message.reply("Hozircha navbatchi belgilanmagan.")

# Har kuni ertalab navbatchilarni e'lon qilish funksiyasi
async def daily_announcement():
    global current_duty
    if duty_list:
        current_duty = duty_list.pop(0)  # Birinchi navbatchini olish
        duty_list.append(current_duty)  # Uni ro'yxat oxiriga qo'shish (aylantirish)
        duty_message = f"{current_duty}, siz bugungi navbatchisiz."
        try:
            await bot.send_message(GROUP_ID, duty_message)
        except ChatNotFound:
            logging.error("Guruh topilmadi")
    else:
        logging.error("Navbatchilar ro'yxati bo'sh.")
# Botni ishga tushirishda avtomatik ravishda jadval sozlash va birinchi marta chaqirish
async def on_startup(_):
    # Birinchi marta navbatchini avtomatik belgilash uchun chaqiramiz
    await daily_announcement()

    scheduler.add_job(daily_announcement, 'cron', hour=18, minute=0, timezone=tz)  
    scheduler.start()

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
