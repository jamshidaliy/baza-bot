import requests
import schedule
import time
from datetime import datetime

# === SOZLAMALAR ===
TODOIST_TOKEN = "286baf4a646c56fa8cc00d3e3dd085f2b9809f6b"
TELEGRAM_TOKEN = "8666647454:AAGRvbbE8PnmP7cxzOOgkkWz-9nM_QIOtD4"
CHAT_ID = "-1002785026064"
TOPIC_ID = "211"
PROJECT_ID = "6gWV3gFXVmhWM2hX"

SECTIONS = {
    "Sunnat": "6gWV3hrV2f7WrMHX",
    "Jobir": "6gWV3p92Rp87XJ6X",
    "Jamshid": "6gWV3pmfc5h3c6h5",
}
BAJARILDI_SECTION = "6grf9mRCqCgrPm85"

def get_tasks(section_id):
    url = "https://api.todoist.com/api/v1/tasks"
    headers = {"Authorization": f"Bearer {TODOIST_TOKEN}"}
    params = {"project_id": PROJECT_ID, "section_id": section_id}
    res = requests.get(url, headers=headers, params=params)
    data = res.json()
    return data.get("results", [])

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "message_thread_id": TOPIC_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def build_and_send():
    now = datetime.now()
    vaqt = "Ertalab" if now.hour < 12 else "Kechqurun"
    message = f"<b>BAZA | {vaqt} holati ({now.strftime('%d.%m.%Y %H:%M')})</b>\n"
    message += "________________________\n\n"

    for name, section_id in SECTIONS.items():
        tasks = get_tasks(section_id)
        message += f"<b>{name}:</b>\n"
        if tasks:
            for task in tasks:
                message += f"  - {task['content']}\n"
        else:
            message += "  vazifa yoq\n"
        message += "\n"

    done = get_tasks(BAJARILDI_SECTION)
    message += "<b>Bajarildi:</b>\n"
    if done:
        for task in done:
            message += f"  - {task['content']}\n"
    else:
        message += "  hali bajarilgan yoq\n"

    send_message(message)
    print(f"Yuborildi: {now.strftime('%H:%M')}")

schedule.every().day.at("09:00").do(build_and_send)
schedule.every().day.at("18:00").do(build_and_send)

print("Bot ishga tushdi!")
build_and_send()

while True:
    schedule.run_pending()
    time.sleep(60)
