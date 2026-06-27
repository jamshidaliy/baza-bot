import requests
import schedule
import time
import threading
from datetime import datetime
import pytz

TODOIST_TOKEN = "286baf4a646c56fa8cc00d3e3dd085f2b9809f6b"
TELEGRAM_TOKEN = "8666647454:AAGRvbbE8PnmP7cxzOOgkkWz-9nM_QIOtD4"
CHAT_ID = -1002785026064
TOPIC_ZADANIYA = 211
TOPIC_MULOQOT = 1
PROJECT_ID = "6gWV3gFXVmhWM2hX"
TZ = pytz.timezone("Asia/Tashkent")

USERNAME_TO_SECTION = {
    "jamshid_aliyy": "6gWV3pmfc5h3c6h5",
    "ravoquz":       "6gWV3hrV2f7WrMHX",
    "jobirmx":       "6gWV3p92Rp87XJ6X",
}

SECTIONS = {
    "Sunnat":  "6gWV3hrV2f7WrMHX",
    "Jobir":   "6gWV3p92Rp87XJ6X",
    "Jamshid": "6gWV3pmfc5h3c6h5",
}
BAJARILDI_SECTION = "6grf9mRCqCgrPm85"
last_update_id = 0

def get_tasks(section_id):
    url = "https://api.todoist.com/api/v1/tasks"
    headers = {"Authorization": f"Bearer {TODOIST_TOKEN}"}
    params = {"project_id": PROJECT_ID, "section_id": section_id}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        return res.json().get("results", [])
    except Exception as e:
        print(f"get_tasks xato: {e}")
        return []

def add_task(content, section_id):
    url = "https://api.todoist.com/api/v1/tasks"
    headers = {"Authorization": f"Bearer {TODOIST_TOKEN}", "Content-Type": "application/json"}
    data = {"content": content, "project_id": PROJECT_ID, "section_id": section_id}
    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"add_task xato: {e}")
        return False

def send_message(text, topic_id=None):
    if topic_id is None:
        topic_id = TOPIC_ZADANIYA
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "message_thread_id": topic_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, data=data, timeout=10)
        return res.json()
    except Exception as e:
        print(f"send_message xato: {e}")

def format_due(task):
    due = task.get("due")
    if not due:
        return ""
    date_str = due.get("date", "")
    if not date_str:
        return ""
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return f" ({d.strftime('%d.%m')})"
    except:
        return ""

def build_status_message():
    now = datetime.now(TZ)
    hour = now.hour
    if hour < 12:
        vaqt = "Ertalab"
    elif hour < 15:
        vaqt = "Tushdan keyin"
    else:
        vaqt = "Kechqurun"
    message = f"<b>BAZA | {vaqt} holati</b>\n"
    message += f"<i>{now.strftime('%d.%m.%Y %H:%M')} Toshkent</i>\n"
    message += "________________________\n\n"
    for name, section_id in SECTIONS.items():
        tasks = get_tasks(section_id)
        message += f"<b>{name}:</b>\n"
        if tasks:
            for task in tasks:
                due = format_due(task)
                message += f"  - {task['content']}{due}\n"
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
    return message

def send_status():
    msg = build_status_message()
    send_message(msg, TOPIC_ZADANIYA)
    print(f"Holat yuborildi: {datetime.now(TZ).strftime('%H:%M')}")

def send_reminder():
    now = datetime.now(TZ)
    weekday = now.weekday()
    if weekday in [0, 2, 4]:
        msg = "Jamshid aka, bugun 10:00 da keladigan kuningiz, bir eslatay degandim"
        send_message(msg, TOPIC_MULOQOT)
        print(f"Jamshid eslatma: {now.strftime('%d.%m %H:%M')}")
    elif weekday in [1, 3, 5]:
        msg = "Jobir aka, bugun 10:00 da keladigan kuningiz, bir eslatay degandim"
        send_message(msg, TOPIC_MULOQOT)
        print(f"Jobir eslatma: {now.strftime('%d.%m %H:%M')}")
    else:
        print("Yakshanba - eslatma yoq")

def poll_telegram():
    global last_update_id
    print("Polling boshlandi...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}
            res = requests.get(url, params=params, timeout=35)
            updates = res.json().get("result", [])
            for update in updates:
                last_update_id = update["update_id"]
                message = update.get("message", {})
                if not message:
                    continue
                thread_id = message.get("message_thread_id")
                from_data = message.get("from", {})
                if from_data.get("is_bot"):
                    continue
                username = from_data.get("username", "")
                text = message.get("text", "").strip()
                if not text:
                    continue
                print(f"Xabar: @{username} thread={thread_id} text={text[:40]}")
                if thread_id != TOPIC_ZADANIYA:
                    print(f"Thread mos emas: {thread_id} != {TOPIC_ZADANIYA}")
                    continue
                if text == "?":
                    msg = build_status_message()
                    send_message(msg, TOPIC_ZADANIYA)
                    print(f"? javob berildi: @{username}")
                    continue
                if text.startswith("+"):
                    task_text = text[1:].strip()
                    if not task_text:
                        continue
                    section_id = USERNAME_TO_SECTION.get(username)
                    if section_id:
                        success = add_task(task_text, section_id)
                        if success:
                            send_message(f"Task qoshildi @{username}:\n<i>{task_text}</i>")
                            print(f"Task qoshildi: @{username} -> {task_text}")
                        else:
                            send_message(f"Xatolik @{username}")
                    else:
                        send_message(f"@{username} tizimda topilmadi")
                        print(f"Noma'lum: @{username}")
        except Exception as e:
            print(f"Polling xato: {e}")
            time.sleep(5)

def run_schedule():
    schedule.every().day.at("04:00").do(send_status)
    schedule.every().day.at("04:00").do(send_reminder)
    schedule.every().day.at("08:30").do(send_status)
    schedule.every().day.at("13:00").do(send_status)
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    print("BAZA Bot ishga tushdi!")
    print(f"Vaqt: {datetime.now(TZ).strftime('%d.%m.%Y %H:%M')} Toshkent")
    t1 = threading.Thread(target=run_schedule, daemon=True)
    t1.start()
    t2 = threading.Thread(target=poll_telegram, daemon=True)
    t2.start()
    send_status()
    while True:
        time.sleep(60)
