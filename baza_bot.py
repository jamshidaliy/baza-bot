import requests
import schedule
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

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

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message", {})
    thread_id = str(message.get("message_thread_id", ""))
    if thread_id != TOPIC_ID:
        return jsonify({"ok": True})
    if message.get("from", {}).get("is_bot"):
        return jsonify({"ok": True})
    username = message.get("from", {}).get("username", "")
    text = message.get("text", "").strip()
    if not text or not username:
        return jsonify({"ok": True})
    section_id = USERNAME_TO_SECTION.get(username)
    if section_id:
        success = add_task(text, section_id)
        if success:
            send_message(f"Task qoshildi @{username}:\n<i>{text}</i>")
    return jsonify({"ok": True})

@app.route("/")
def index():
    return "BAZA Bot ishlayapti!"

def run_schedule():
    schedule.every().day.at("04:00").do(build_and_send)
    schedule.every().day.at("13:00").do(build_and_send)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    t = threading.Thread(target=run_schedule, daemon=True)
    t.start()
    print("Bot ishga tushdi!")
    app.run(host="0.0.0.0", port=10000)
