import asyncio
import logging
from datetime import datetime
import pytz
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TELEGRAM_TOKEN = "8666647454:AAGRvbbE8PnmP7cxz00gkkWz-9nM_QI0tD4"
CHAT_ID = -1002785026064
THREAD_ID = 1
TZ = pytz.timezone("Asia/Tashkent")

JOBIR_MSG = "Jobir aka, bugun ishga 10:00 da kelishingizni eslatib qoyay degandim"
JAMSHID_MSG = "Jamshid aka, bugun ishga 10:00 da kelishingizni eslatib qoyay degandim"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

async def jobir():
                now = datetime.now(TZ)
                if now.weekday() in [1, 3, 5]:
                                    await bot.send_message(chat_id=CHAT_ID, message_thread_id=THREAD_ID, text=JOBIR_MSG)
                                    logger.info("Jobir eslatmasi yuborildi")

            async def jamshid():
                            now = datetime.now(TZ)
                            if now.weekday() in [0, 2, 4]:
                                                await bot.send_message(chat_id=CHAT_ID, message_thread_id=THREAD_ID, text=JAMSHID_MSG)
                                                logger.info("Jamshid eslatmasi yuborildi")

                        async def main():
                                        scheduler = AsyncIOScheduler(timezone=TZ)
                                        scheduler.add_job(jobir, "cron", hour=9, minute=0)
                                        scheduler.add_job(jamshid, "cron", hour=9, minute=0)
                                        scheduler.start()
                                        logger.info("Bot ishga tushdi!")
                                        while True:
                                                            await asyncio.sleep(60)

                                    if __name__ == "__main__":
                                                    asyncio.run(main())
                                                
