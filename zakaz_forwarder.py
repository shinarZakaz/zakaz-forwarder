from telethon import TelegramClient, events
from datetime import datetime
import asyncio
import requests
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties

# === Telegram akkaunt (UserBot) ===
api_id = 28726254
api_hash = "c31ca470f833be87e923d61e13f4d36b"

# === Aiogram bot (operator uchun) ===
BOT_TOKEN = "8036833811:AAFW3IAdglcPSu_1EQ3VwjVwaKTIkHORFSs"
OPERATORS_CHAT_ID = -1003100346143  # Guruh ID

# === Kalit so‘zlar (sening to‘liq ro‘yxating) ===
KEYWORDS = [
    "zakaz", "buyurtma", "заказ", "order",
    "olmoqchiman", "kerak", "bering", "olay", "xohlayman", "нужно", "хочу", "hisoblab",
    "kg", "so'm", "narx", "tovar", "mahsulot", "product", "blok", "tara", "kosa", "pirojni",
    "qoshiq", "spashka", "vilka", "kapalak", "qilich", "sous", "sousnik", "lanchbox",
    "lanche", "ps1", "ps07", "75gr", "50gr", "25gr", "3litr", "don", "dona", "trubka",
    "koktel", "stakan", "karobka", "nabor", "set", "upakovka", "tarilka", "kotta", "kichik",
    "1914", "2313", "2316", "2619", "wpawka", "smuzi", "qowu", "qora", "qizil", "oq",
    "kofe", "trubichka", "sovus", "marojnik", "pero", "ps", "tarelka", "plastik", "karobka",
    "lanchbox", "Lowka", "trub", "po'kak", "tarilka", "праз коса", "кора коса",
    "ланч б", "кич тарелка", "тогора", "контенер", "500*12", "500*21", "400", "100"
]

# === E’tiborga olinmaydigan so‘zlar ===
IGNORE = [
    "salom", "assalom", "rahmat", "ok", "alo", "hello", "manzil", "adres",
    "qarz", "opa", "aka", "iltimos", "rahmatli", "bervor", "tayyor", "davernest"
]

# === Telegram mijoz (UserBot) ===
client = TelegramClient("zakaz_userbot", api_id, api_hash)
order_counter = 0

# === Operatorlar uchun bot (Aiogram) ===
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# === AQLLI ZAKAZ ANIQLASH FUNKSIYASI ===
def is_order_message(text):
    text = text.lower()

    # Raqamni aniqlash
    has_number = bool(re.search(r'\b\d+\b', text))

    # Birliklar (ta, kg, dona va hokazo)
    has_unit = any(u in text for u in ["ta", "kg", "gr", "blok", "litr", "dona", "set", "quti"])

    # Mahsulot nomlari
    has_product = any(p in text for p in [
        "ps", "kosa", "trubka", "trubichka", "vilka", "qoshiq", "sous", "kapalak",
        "karobka", "nabor", "tarelka", "plastik", "marojnik", "pero", "smuzi",
        "wpawka", "kofe", "sovus", "1914", "2313", "2316", "2619"
    ])

    # Kamida 2 tasi mavjud bo‘lsa — zakaz
    if (has_number and has_unit) or (has_number and has_product) or (has_product and has_unit):
        return True
    return False


# === Guruhdagi “Qabul qildim” tugmasi ===
@dp.callback_query(F.data.startswith("accept_"))
async def accept_order(callback_query: types.CallbackQuery):
    order_id = callback_query.data.split("_")[1]
    operator = callback_query.from_user
    message = callback_query.message

    new_text = message.html_text.replace(
        "🟡 <i>Buyurtma hali qabul qilinmagan</i>",
        f"✅ Buyurtma qabul qilindi: <b>{operator.full_name}</b>"
    )

    await message.edit_text(new_text)
    await callback_query.answer(f"{order_id} sizga biriktirildi ✅")
    print(f"📦 {order_id} qabul qilindi: {operator.full_name}")


# === Mijozlardan kelgan xabarlarni kuzatish ===
@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    global order_counter

    if not event.is_private:
        return  # faqat shaxsiy yozishmalar

    sender = await event.get_sender()
    text = (event.raw_text or "").lower().strip()

    # Belgilarni tozalash
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = text.replace("ў", "u").replace("қ", "k").replace("ғ", "g")
    text = re.sub(r"\s+", " ", text)

    # Oddiy so‘zlar — e’tiborga olinmaydi
    if any(w in text for w in IGNORE):
        print(f"⚠️ E'tiborga olinmadi (oddiy gap): {text}")
        return

    # Media bormi?
    has_media = event.photo or event.video or event.voice or event.document

    # Aqlli tahlil orqali aniqlash
    is_order = is_order_message(text)
    
    # Agar haqiqiy zakaz bo‘lsa yoki media yuborilgan bo‘lsa
    if is_order or has_media:
        order_counter += 1
        order_id = f"#{order_counter:04d}"

        msg_text = (
            f"🆕 <b>Yangi zakaz {order_id}</b>\n"
            f"👤 <b>{sender.first_name or ''}</b>\n"
            f"🆔 <code>{sender.id}</code>\n"
            f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"{event.raw_text or '[Media fayl]'}\n\n"
            f"🟡 <i>Buyurtma hali qabul qilinmagan</i>"
        )

        keyboard = {
            "inline_keyboard": [
                [{"text": "✅ Qabul qildim", "callback_data": f"accept_{order_id}"}]
            ]
        }

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": OPERATORS_CHAT_ID,
            "text": msg_text,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }

        try:
            requests.post(url, json=data)
            print(f"✅ Zakaz {order_id} guruhga yuborildi: {text[:50]}")
        except Exception as e:
            print("❌ Guruhga yuborishda xato:", e)
    else:
        print(f"📨 Oddiy xabar (o‘tkazildi): {text}")


# === UserBot va OperatorBot bir vaqtda ishga tushadi ===
async def start_both():
    print("🤖 UserBot ishga tushmoqda...")
    await client.start()
    print("✅ Tayyor! Endi zakazlar avtomatik guruhga yuboriladi.")
    asyncio.create_task(dp.start_polling(bot))
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(start_both())
