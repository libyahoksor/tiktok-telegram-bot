import os
import logging
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات بشكل كامل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN", "8916408881:AAHWVFjn5tLjJ4odlAnGpXS3AeD545JtRMA")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Received /start from {update.effective_user.id}")
    await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو من تيك توك وسأقوم بتحميله بدون علامة مائية.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    logging.info(f"Received message: {text}")

    # إذا أرسل المستخدم /start أو أمر مشابهاً
    if text.startswith("/start"):
        await start(update, context)
        return

    if "tiktok.com" not in text:
        await update.message.reply_text("الرجاء إرسال رابط تيك توك صحيح.")
        return

    msg = await update.message.reply_text("جاري جلب الفيديو...")

    try:
        async with httpx.AsyncClient(follow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20.0) as client:
            res = await client.get(text)
            final_url = str(res.url)

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
        logging.error(f"Error handling video: {e}")
        await msg.edit_text("حدث خطأ أثناء تحميل الفيديو. حاول مجدداً لاحقاً.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Exception while handling an update:", exc_info=context.error)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    # التقاط كافة الرسائل النصية
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_error_handler(error_handler)
    
    print("البوت يعمل الآن...")
    app.run_polling()
