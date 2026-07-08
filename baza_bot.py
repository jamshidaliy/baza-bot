import os
import requests
import schedule
import time
import threading
from datetime import datetime
import pytz

TODOIST_TOKEN = os.environ["TODOIST_API_TOKEN"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = -1002785026064
TOPIC_ZADANIYA = 211
TOPIC_MULOQOT = 1
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

TODOIST_BASE = "https://api.todoist.com/api/v1"
TODOIST_HEADERS = {"Authorization": f"Bearer {TODOIST_TOKEN}"}

last_update_id = 0


def get_tasks(section_id, retries=2):
    url = f"{TODOIST_BASE}/tasks"
    params = {"project_id": PROJECT_ID, "section_id": section_id}
    for attempt in range(retries + 1):
        try:
            res = requests.get(url, headers=TODOIST_HEADERS, params=params, timeout=15)
            if res.status_code != 200:
                print(f"get_tasks xato: HTTP {res.status_code} - {res.text[:200]}")
                time.sleep(2)
                continue
            return res.json().get("results", [])
        except Exception as e:
            print(f"get_tasks xato (urinish {attempt + 1}): {e}")
            time.sleep(2)
    return []


def add_task(content, section_id, retries=2):
    url = f"{TODOIST_BASE}/tasks"
    data = {"content": content, "project_id": PROJECT_ID, "section_id": section_id}
    for attempt in range(retries + 1):
        try:
            res = requests.post(url, headers=TODOIST_HEADERS, json=data, timeout=15)
            if res.status_code in (200, 204):
                return True
            print(f"add_task xato: HTTP {res.status_code} - {res.text[:200]}")
            time.sleep(2)
        except Exception as e:
            print(f"add_task xato (urinish {attempt + 1}): {e}")
            time.sleep(2)
    return False


def send_message(text, topic_id=None):
    if topic_id is None:
        topic_id = TOPIC_ZADANIYA
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "message_thread_id": topic_id,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        res = requests.post(url, data=data, timeout=15)
        if res.status_code != 200:
            print(f"send_message xato: HTTP {res.status_code} - {res.text[:200]}")
        return res.json()
    except Exception as e:
        print(f"send_message xato: {e}")
        return None


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
    except Exception:
        return ""


def build_status_message():
    now = datetime.now(TZ)
    hour = now.hour
    if hour < 12:
        vaqt = "Ertalab"
    elif hour < 16:
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
                message += f" - {task['content']}{due}\n"
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

    return message


def send_status():
    try:
        msg = build_status_message()
        send_message(msg, TOPIC_ZADANIYA)
        print(f"Holat yuborildi: {datetime.now(TZ).strftime('%H:%M')}")
    except Exception as e:
        print(f"send_status xato: {e}")


def poll_telegram():
    global last_update_id
    print("Polling boshlandi...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 25}
            res = requests.get(url, params=params, timeout=30)
            if res.status_code != 200:
                print(f"getUpdates xato: HTTP {res.status_code} - {res.text[:200]}")
                time.sleep(3)
                continue

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

                username = (from_data.get("username") or "").strip()
                text = (message.get("text") or "").strip()
                if not text:
                    continue

                print(f"Xabar: @{username} thread={thread_id} text={text[:40]!r}")

                if thread_id != TOPIC_ZADANIYA:
                    continue

                if text == "?":
                    msg = build_status_message()
                    send_message(msg, TOPIC_ZADANIYA)
                    print(f"javob berildi: @{username}")
                    continue

                if text.startswith("+"):
                    task_text = text[1:].strip()
                    if not task_text:
                        continue
                    section_id = USERNAME_TO_SECTION.get(username.lower())
                    if section_id:
                        success = add_task(task_text, section_id)
                        if success:
                            send_message(f"Task qoshildi @{username}: {task_text}", TOPIC_ZADANIYA)
                            print(f"Task qoshildi: @{username} -> {task_text}")
                        else:
                            send_message(f"Task qoshishda xatolik @{username}", TOPIC_ZADANIYA)
                    else:
                        send_message(f"@{username} tizimda topilmadi", TOPIC_ZADANIYA)
                        print(f"Nomalum username: @{username}")

        except Exception as e:
            print(f"Polling xato: {e}")
            time.sleep(5)


def run_schedule():
    schedule.every().day.at("04:00").do(send_status)
    schedule.every().day.at("09:00").do(send_status)
    schedule.every().day.at("13:00").do(send_status)
    print("Schedule sozlandi: 09:00, 14:00, 18:00 Toshkent")
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Schedule xato: {e}")
        time.sleep(20)


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
