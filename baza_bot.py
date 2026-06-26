import asyncio
import logging
from datetime import datetime
import pytz
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === SOZLAMALAR ===
TELEGRAM_TOKEN = "8666647454:AAGRvbbE8PnmP7cxz00gkkWz-9nM_QI0tD4"
CHAT_ID = -1002785026064
MULOQOT_THREAD_ID = 1
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

# === XABARLAR ===
JOBIR_MSG = "Jobir aka, bugun ishga 10:00 da kelishingizni eslatib qo'yay degandim"
JAMSHID_MSG = "Jamshid aka, bugun ishga 10:00 da kelishingizni eslatib qo'yay degandim"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)

async def send_jobir_reminder():
        now = datetime.now(TASHKENT_TZ)
        weekday = now.weekday()
        if weekday in [1, 3, 5]:  # Se, Pay, Shan
            await bot.send_message(
                            chat_id=CHAT_ID,
                            message_thread_id=MULOQOT_THREAD_ID,
                            text=JOBIR_MSG
            )
                    logger.info(f"Jobir eslatmasi yuborildi: {now}")

async def send_jamshid_reminder():
        now = datetime.now(TASHKENT_TZ)
        weekday = now.weekday()
        if weekday in [0, 2, 4]:  # Du, Chor, Ju
            await bot.send_message(
                            chat_id=CHAT_ID,
                            message_thread_id=MULOQOT_THREAD_ID,
                            text=JAMSHID_MSG
            )
                    logger.info(f"Jamshid eslatmasi yuborildi: {now}")

async def main():
        scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)
        scheduler.add_job(send_jobir_reminder, "cron", hour=9, minute=0)
        scheduler.add_job(send_jamshid_reminder, "cron", hour=9, minute=0)
        scheduler.start()
        logger.info("Bot ishga tushdi!")
        while True:
                    await asyncio.sleep(60)

    if __name__ == "__main__":
            asyncio.run(main())
