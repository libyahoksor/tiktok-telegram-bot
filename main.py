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

# جلب التوكن من متغيرات البيئة أو وضعه بشكل آمن
TOKEN = os.getenv("BOT_TOKEN", "ضع_التوكن_الجديد_هنا")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو من تيك توك وسأقوم بتحميله بدون علامة مائية.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "tiktok.com" not in url:
        await update.message.reply_text("الرجاء إرسال رابط تيك توك صحيح.")
        return

    msg = await update.message.reply_text("جاري جلب الفيديو...")

    try:
        # استخدام httpx لطلبات غير متزامنة بالكامل (Non-blocking)
        async with httpx.AsyncClient(follow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'}) as client:
            # 1. تتبع الرابط لفك التوجيه
            res = await client.get(url)
            final_url = str(res.url)

            # 2. طلب API من TikWM
            api_url = "https://www.tikwm.com/api/"
            api_res = await client.post(api_url, data={'url': final_url})
            response = api_res.json()

        if response.get('code') == 0:
            video_url = response['data']['play']
            if not video_url.startswith("http"):
                video_url = "https://www.tikwm.com" + video_url

            await update.message.reply_video(video=video_url, caption="تم التحميل بنجاح! ✨")
            await msg.delete()
        else:
            await msg.edit_text("تعذر جلب الفيديو، تأكد من أن الحساب ليس خاصاً أو أن الرابط صحيح.")

    except Exception as e:
        logging.error(f"Error: {e}")
        await msg.edit_text("حدث خطأ أثناء تحميل الفيديو. حاول مجدداً لاحقاً.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("البوت يعمل الآن...")
    app.run_polling()
