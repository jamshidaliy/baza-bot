import requests
import schedule
import time
import threading
from datetime import datetime

TODOIST_TOKEN = "286baf4a646c56fa8cc00d3e3dd085f2b9809f6b"
TELEGRAM_TOKEN = "8666647454:AAGRvbbE8PnmP7cxzOOgkkWz-9nM_QIOtD4"
CHAT_ID = "-1002785026064"
TOPIC_ID = "211"
PROJECT_ID = "6gWV3gFXVmhWM2hX"

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

def add_task(content, section_id):
    url = "https://api.todoist.com/api/v1/tasks"
    headers = {"Authorization": f"Bearer {TODOIST_TOKEN}", "Content-Type": "application/json"}
    data = {"content": content, "project_id": PROJECT_ID, "section_id": section_id}
    res = requests.post(url, headers=headers, json=data)
    return res.status_code == 200

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "message_thread_id": TOPIC_ID, "text": text, "parse_mode": "HTML"}
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
    print(f"Yuborildi: {datetime.now().strftime('%H:%M')}")

def poll_telegram():
    global last_update_id
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}
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
                if not text or not username:
                    continue
                # Faqat + bilan boshlangan xabarlar
                if not text.startswith("+"):
                    continue
                task_text = text[1:].strip()
                if not task_text:
                    continue
                section_id = USERNAME_TO_SECTION.get(username)
                if section_id:
                    success = add_task(task_text, section_id)
                    if success:
                        send_message(f"✅ Task qoshildi @{username}:\n<i>{task_text}</i>")
                        print(f"Task qoshildi: {username} -> {task_text}")
                else:
                    print(f"Noma'lum username: {username}")
        except Exception as e:
            print(f"Polling xato: {e}")
            time.sleep(5)

schedule.every().day.at("04:00").do(build_and_send)
schedule.every().day.at("13:00").do(build_and_send)

t = threading.Thread(target=poll_telegram, daemon=True)
t.start()
print("Bot ishga tushdi!")
build_and_send()

while True:
    schedule.run_pending()
    time.sleep(60)
