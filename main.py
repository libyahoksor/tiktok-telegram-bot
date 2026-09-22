import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = '8336552342:AAFdSKeHEKAvKupKbolezAfs72lnEG4Z66U'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو من تيك توك وسأقوم بتحميله بدون علامة مائية.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "tiktok.com" not in url:
        await update.message.reply_text("الرجاء إرسال رابط تيك توك صحيح.")
        return

    msg = await update.message.reply_text("جاري جلب الفيديو...")

    try:
        # 1. تتبع الرابط إذا كان مختصراً لفك التوجيه (Redirect)
        session = requests.Session()
        res = session.get(url, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        final_url = res.url

        # 2. استخدام API جديد ومستقر (TikWM API)
        api_url = "https://www.tikwm.com/api/"
        response = requests.post(api_url, data={'url': final_url}).json()

        if response.get('code') == 0:
            # رابط الفيديو بدون علامة مائية
            video_url = response['data']['play']
            # للتعامل مع الروابط النسبية
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
