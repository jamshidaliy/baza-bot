import requests
import schedule
import time
import threading
from datetime import datetime, date
import pytz

TODOIST_TOKEN = "286baf4a646c56fa8cc00d3e3dd085f2b9809f6b"
TELEGRAM_TOKEN = "8666647454:AAGRvbbE8PnmP7cxz00gkkWz-9nM_QI0tD4"
CHAT_ID = "-1002785026064"
TOPIC_ID = "211"
PROJECT_ID = "6gWV3gFXVmhWM2hX"
TZ = pytz.timezone("Asia/Tashkent")

USERNAME_TO_SECTION = {
    "jamshid_aliyy": "6gWV3pmfc5h3c6h5",
    "ravoquz": "6gWV3hrV2f7WrMHX",
    "jobirmx": "6gWV3p92Rp87XJ6X",
}

SECTIONS = {
    "Sunnat": "6gWV3hrV2f7WrMHX",
    "Jobir": "6gWV3p92Rp87XJ6X",
    "Jamshid": "6gWV3pmfc5h3c6h5",
}
BAJARILDI_SECTION = "6grf9mRCqCgrPm85"
last_update_id = 0


def get_tasks(section_id):
    url = "https://api.todoist.com/api/v1/tasks"
    headers = {"Authorization": f"Bearer {TODOIST_TOKEN}"}
    params = {"project_id": PROJECT_ID, "section_id": section_id}
    res = requests.get(url, headers=headers, params=params)
    return res.json().get("results", [])


def add_task(content, section_id, due_date=None):
    url = "https://api.todoist.com/api/v1/tasks"
    headers = {"Authorization": f"Bearer {TODOIST_TOKEN}", "Content-Type": "application/json"}
    data = {"content": content, "project_id": PROJECT_ID, "section_id": section_id}
    if due_date:
        data["due_date"] = due_date
    res = requests.post(url, headers=headers, json=data)
    return res.status_code == 200


def format_due(task):
    due = task.get("due")
    if not due:
        return ""
    due_str = due.get("date", "")
    try:
        due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
        today = date.today()
        diff = (due_date - today).days
        if diff < 0:
            return f" ⚠️ {abs(diff)}k kechikkan"
        elif diff == 0:
            return " U0001f534 bugun"
        elif diff == 1:
            return " U0001f7e1 ertaga"
        else:
            return f" ({due_str})"
    except:
        return f" ({due_str})"


def send_message(text, thread_id=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    if thread_id:
        data["message_thread_id"] = thread_id
    requests.post(url, json=data)


def send_summary():
    now = datetime.now(TZ)
    vaqt = "Ertalab" if now.hour < 12 else "Kechqurun"
    message = f"<b>BAZA | {vaqt} holati ({now.strftime('%d.%m.%Y %H:%M')})</b>\n\n"
    for name, section_id in SECTIONS.items():
        tasks = get_tasks(section_id)
        message += f"<b>{name}:</b>\n"
        if tasks:
            for task in tasks:
                due_str = format_due(task)
                message += f" - {task['content']}{due_str}\n"
        else:
            message += " vazifa yoq\n"
        message += "\n"
    done = get_tasks(BAJARILDI_SECTION)
    message += "<b>Bajarildi:</b>\n"
    if done:
        for task in done:
            message += f" - {task['content']}\n"
    else:
        message += " hali bajarilgan yoq\n"
    send_message(message, thread_id=TOPIC_ID)


def send_jobir_reminder():
    now = datetime.now(TZ)
    if now.weekday() in [1, 3, 5]:
        send_message("Jobir aka bugun 10:00 da keladigan vaqtingizni eslatay degandim.", thread_id="1")


def send_jamshid_reminder():
    now = datetime.now(TZ)
    if now.weekday() in [0, 2, 4]:
        send_message("Jamshid aka bugun 10:00 da keladigan vaqtingizni eslatay degandim.", thread_id="1")


def get_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 30}
    try:
        res = requests.get(url, params=params, timeout=35)
        updates = res.json().get("result", [])
        for update in updates:
            last_update_id = update["update_id"]
            message = update.get("message", {})
            thread_id = str(message.get("message_thread_id", ""))
            if thread_id != TOPIC_ID:
                continue
            if message.get("from", {}).get("is_bot"):
                continue
            username = message.get("from", {}).get("username", "")
            text = message.get("text", "").strip()
            if text == "?":
                send_summary()
            elif text.startswith("+"):
                parts = text[1:].strip().split("|")
                content = parts[0].strip()
                due_date = parts[1].strip() if len(parts) > 1 else None
                section_id = USERNAME_TO_SECTION.get(username)
                if section_id and content:
                    ok = add_task(content, section_id, due_date)
                    if ok:
                        msg = f"✅ Vazifa qoshildi: {content}"
                        if due_date:
                            msg += f" ({due_date})"
                        send_message(msg, thread_id=TOPIC_ID)
                    else:
                        send_message("❌ Xatolik yuz berdi.", thread_id=TOPIC_ID)
    except Exception as e:
        print(f"Xato: {e}")


def run_bot():
    while True:
        get_updates()


if __name__ == "__main__":
    schedule.every().day.at("09:00").do(send_summary)
    schedule.every().day.at("18:00").do(send_summary)
    schedule.every().day.at("09:00").do(send_jobir_reminder)
    schedule.every().day.at("09:00").do(send_jamshid_reminder)
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("Bot ishga tushdi!")
    while True:
        schedule.run_pending()
        time.sleep(30)
