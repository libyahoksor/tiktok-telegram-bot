import os
import logging
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("8937294006:AAEcv9o2a2fT2lxCsOyEIyMlPyGwfFD9Grc")

# مجموعة لتخزين معرّفات المستخدمين الفريدين (In-Memory Tracking)
users_db = set()

def save_user(user_id: int):
    """حفظ معرّف المستخدم حسابياً"""
    users_db.add(user_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    msg = (
        "أهلاً بك! 👋\n\n"
        "أنا بوت تحميل الفيديوهات بدون علامة مائية.\n"
        "يمكنك إرسال رابط فيديو من:\n"
        "• TikTok 🎵\n"
        "• Instagram 📸\n"
        "• Facebook 📘\n"
        "• Twitter / X 🐦\n\n"
        "أرسل الرابط وسأقوم بمعالجته فوراً."
    )
    await update.message.reply_text(msg)

async def users_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر لمعرفة عدد مستخدمي البوت"""
    count = len(users_db)
    await update.message.reply_text(f"📊 **إحصائيات البوت:**\nعدد المستخدمين الكلي: {count}")

async def download_tiktok(url: str, client: httpx.AsyncClient):
    """جلب فيديو تيك توك عبر TikWM API"""
    api_res = await client.post("https://www.tikwm.com/api/", data={'url': url, 'hd': 1})
    res_data = api_res.json()
    if res_data.get('code') == 0 and 'data' in res_data:
        video_url = res_data['data'].get('play') or res_data['data'].get('wmplay')
        if video_url and not video_url.startswith("http"):
            video_url = "https://www.tikwm.com" + video_url
        return video_url
    return None

async def download_generic(url: str, client: httpx.AsyncClient):
    """جلب الفيديوهات عبر Cobalt API (يدعم الانستقرام، الفيسبوك، وتويتر)"""
    payload = {
        "url": url,
        "videoQuality": "720",
        "downloadMode": "auto"
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # استخدام سيرفر عمومي متوافق مع API
    api_res = await client.post("https://api.cobalt.tools/api/json", json=payload, headers=headers)
    
    if api_res.status_code == 200:
        data = api_res.json()
        if data.get("status") == "stream" or data.get("status") == "picker":
            return data.get("url")
        elif data.get("status") == "redirect":
            return data.get("url")
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)

    text = update.message.text.strip() if update.message.text else ""

    if text.startswith("/start"):
        await start(update, context)
        return
    elif text.startswith("/users") or text == "المستخدمين":
        await users_count(update, context)
        return

    # فحص توافق الرابط مع المنصات
    platforms = ["tiktok.com", "instagram.com", "facebook.com", "fb.watch", "twitter.com", "x.com"]
    if not any(p in text for p in platforms):
        await update.message.reply_text("الرجاء إرسال رابط صحيح من (تيك توك، انستقرام، فيسبوك، أو تويتر).")
        return

    msg = await update.message.reply_text("جاري معالجة الفيديو...")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        async with httpx.AsyncClient(follow_redirects=True, headers=headers, timeout=30.0) as client:
            video_url = None

            # 1. التوجيه لـ TikTok API
            if "tiktok.com" in text:
                video_url = await download_tiktok(text, client)
            # 2. التوجيه لباقي المنصات (Instagram / Facebook / Twitter)
            else:
                video_url = await download_generic(text, client)

        if video_url:
            await update.message.reply_video(video=video_url, caption="تم التحميل بنجاح! ✨")
            await msg.delete()
        else:
            await msg.edit_text("تعذر جلب الفيديو، تأكد من أن الرابط صحيح وأن الحساب عام وليس خاصاً.")

    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        await msg.edit_text("حدث خطأ أثناء معالجة الفيديو. حاول مجدداً لاحقاً.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("users", users_count))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    print("البوت يعمل الآن...")
    app.run_polling()
