import os
import re
import requests
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

DATE_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?$")

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


def parse_due_date(date_part):
    m = DATE_RE.match(date_part.strip())
    if not m:
        return None
    day_s, month_s, year_s = m.groups()
    day, month = int(day_s), int(month_s)
    now = datetime.now(TZ)
    year = int(year_s) if year_s else now.year
    if year < 100:
        year += 2000
    try:
        due = datetime(year, month, day)
    except ValueError:
        return None
    if not year_s and due.date() < now.date():
        try:
            due = datetime(year + 1, month, day)
        except ValueError:
            return None
    return due.strftime("%Y-%m-%d")


def add_task(content, section_id, due_date=None, retries=2):
    url = f"{TODOIST_BASE}/tasks"
    data = {"content": content, "project_id": PROJECT_ID, "section_id": section_id}
    if due_date:
        data["due_date"] = due_date
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


def delete_webhook():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook"
        requests.get(url, params={"drop_pending_updates": "false"}, timeout=15)
        print("Webhook ochirildi (agar mavjud bolsa)")
    except Exception as e:
        print(f"deleteWebhook xato: {e}")


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
                    raw = text[1:].strip()
                    if not raw:
                        continue

                    task_text = raw
                    due_date = None
                    if "|" in raw:
                        content_part, date_part = raw.rsplit("|", 1)
                        parsed = parse_due_date(date_part)
                        if parsed:
                            task_text = content_part.strip()
                            due_date = parsed

                    section_id = USERNAME_TO_SECTION.get(username.lower())
                    if section_id:
                        success = add_task(task_text, section_id, due_date=due_date)
                        if success:
                            due_info = f" (muddat: {due_date})" if due_date else ""
                            send_message(f"Task qoshildi @{username}: {task_text}{due_info}", TOPIC_ZADANIYA)
                            print(f"Task qoshildi: @{username} -> {task_text} due={due_date}")
                        else:
                            send_message(f"Task qoshishda xatolik @{username}", TOPIC_ZADANIYA)
                    else:
                        send_message(f"@{username} tizimda topilmadi", TOPIC_ZADANIYA)
                        print(f"Nomalum username: @{username}")

        except Exception as e:
            print(f"Polling xato: {e}")
            time.sleep(5)


def run_schedule():
    sent_log = set()
    target_hours = (9, 14, 18)
    print("Schedule sozlandi: 09:00, 14:00, 18:00 Toshkent")
    while True:
        try:
            now = datetime.now(TZ)
            if now.hour in target_hours and now.minute == 0:
                key = f"{now.strftime('%Y-%m-%d')}-{now.hour}"
                if key not in sent_log:
                    send_status()
                    sent_log.add(key)
            if len(sent_log) > 30:
                sent_log.clear()
        except Exception as e:
            print(f"Schedule xato: {e}")
        time.sleep(20)


if __name__ == "__main__":
    print("BAZA Bot ishga tushdi!")
    print(f"Vaqt: {datetime.now(TZ).strftime('%d.%m.%Y %H:%M')} Toshkent")

    delete_webhook()

    t1 = threading.Thread(target=run_schedule, daemon=True)
    t1.start()

    t2 = threading.Thread(target=poll_telegram, daemon=True)
    t2.start()

    send_status()

    while True:
        time.sleep(60)
