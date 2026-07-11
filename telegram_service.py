import time
import requests

from config import telegram_configured, get_openrouter_model_chain
from database import get_analysis_rows
from email_service import send_email_reply, build_attachment_summary_for_display
from text_utils import (
    safe_mm,
    make_separator,
    format_summary_section_mm,
)


def send_to_telegram(settings, text, reply_markup=None):
    if not telegram_configured(settings):
        print("⚠️ Telegram config မပြည့်စုံသေးပါ။")
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code != 200:
            print(f"Telegram API Error: {response.text}")
            return False

        return True

    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return False


def send_long_telegram_message(settings, text, chunk_size=3500):
    if not text:
        return

    if len(text) <= chunk_size:
        send_to_telegram(settings, text)
        return

    chunks = []
    current = ""

    for line in text.splitlines():
        if len(current) + len(line) + 1 > chunk_size:
            chunks.append(current)
            current = line
        else:
            current += "\n" + line if current else line

    if current:
        chunks.append(current)

    for idx, chunk in enumerate(chunks, start=1):
        prefix = f"Part {idx}/{len(chunks)}\n\n" if len(chunks) > 1 else ""
        send_to_telegram(settings, prefix + chunk)
        time.sleep(1)


def get_telegram_updates(settings, state):
    if not telegram_configured(settings):
        return []

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/getUpdates"

    params = {
        "timeout": 1
    }

    if state.get("telegram_last_update_id") is not None:
        params["offset"] = state["telegram_last_update_id"] + 1

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print(f"Telegram getUpdates error: {response.text}")
            return []

        data = response.json()

        if not data.get("ok"):
            return []

        return data.get("result", [])

    except Exception as e:
        print(f"Telegram update fetch error: {e}")
        return []


def answer_callback_query(settings, callback_query_id, text=""):
    if not telegram_configured(settings):
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/answerCallbackQuery"

    payload = {
        "callback_query_id": callback_query_id,
        "text": text
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"answerCallbackQuery error: {e}")


def format_priority_mm(importance):
    importance = str(importance or "low").lower()

    if importance == "high":
        return "🔥 အလွန်အရေးကြီး"

    if importance == "medium":
        return "⚠️ အရေးကြီး"

    return "ℹ️ သာမန်"


def format_reply_status_mm(reply_needed, reply_urgency):
    if not reply_needed:
        return "Reply ပြန်ရန်မလိုအပ်ပါ"

    if reply_urgency == "immediate":
        return "Reply ချက်ချင်းပြန်ရန်လိုသည်"

    return "Reply မကြာမီပြန်ရန်လိုသည်"


def readable_sender(sender_raw, sender_email=None):
    sender_raw = safe_mm(sender_raw, "")
    sender_email = safe_mm(sender_email, "")

    if sender_raw and sender_email and sender_email not in sender_raw:
        return f"{sender_raw}\n{sender_email}"

    return sender_raw or sender_email or "မဖော်ပြထားပါ"


def build_telegram_report(email_id, email_data, analysis):
    sender_text = readable_sender(email_data.get("sender_raw"), email_data.get("sender_email"))
    subject = safe_mm(email_data.get("subject"), "Subject မရှိပါ")

    attachment_display = email_data.get("attachment_display_summary")

    if not attachment_display:
        attachment_display = "Attachment file 0 ခု\nFile မရှိပါ။"
    else:
        attachment_display = str(attachment_display)
        attachment_display = attachment_display.replace(
            "Attachment file 0 ခု File မရှိပါ။",
            "Attachment file 0 ခု\nFile မရှိပါ။"
        )

    importance = analysis.get("importance", "low")
    reply_needed = analysis.get("reply_needed", False)
    reply_urgency = analysis.get("reply_urgency", "not_needed")
    is_scam = analysis.get("is_scam", False)

    text = (
        "📩 Student Email စစ်ဆေးချက်\n"
        f"{make_separator()}\n\n"

        "👤 ပေးပို့သူ\n"
        f"{sender_text}\n\n"

        "📌 ခေါင်းစဉ်\n"
        f"{subject}\n\n"

        "📎 Attachment\n"
        f"{attachment_display}\n\n"

        "⭐ အရေးကြီးမှု\n"
        f"{format_priority_mm(importance)}\n"
        f"အကြောင်းရင်း - {safe_mm(analysis.get('importance_reason'))}\n\n"

        f"{format_summary_section_mm(analysis.get('summary'))}\n\n"

        "✅ လုပ်ဆောင်ရန်\n"
        f"{safe_mm(analysis.get('action_item'), 'မရှိပါ')}\n\n"

        "⏰ Deadline\n"
        f"{safe_mm(analysis.get('deadline'), 'မဖော်ပြထားပါ')}\n\n"

        "💬 Reply အခြေအနေ\n"
        f"{format_reply_status_mm(reply_needed, reply_urgency)}\n\n"
    )

    if is_scam:
        text += (
            "\n🚨 သတိထားရန်\n"
            "ဒီ email သည် scam/phishing ဖြစ်နိုင်ပါတယ်။\n"
            f"အကြောင်းရင်း - {safe_mm(analysis.get('scam_reason'))}\n"
        )

    buttons = {
        "inline_keyboard": []
    }

    if is_scam:
        buttons["inline_keyboard"].append([
            {
                "text": "🗑 Ignore",
                "callback_data": f"ignore:{email_id}"
            }
        ])

    elif reply_needed:
        text += "\n\n✉️ Reply ပြန်လိုပါက Reply ကိုနှိပ်ပါ။"

        buttons["inline_keyboard"].append([
            {
                "text": "✉️ Reply",
                "callback_data": f"reply:{email_id}"
            },
            {
                "text": "🗑 Ignore",
                "callback_data": f"ignore:{email_id}"
            }
        ])


    return text, buttons


def build_today_all_mail_list(settings):
    rows = get_analysis_rows(settings, "today", student_only=True)

    if not rows:
        return (
            "📭 ဒီနေ့ Student Mail List\n"
            f"{make_separator()}\n\n"
            "ဒီနေ့ student-related mail မရှိသေးပါ။"
        )

    lines = [
        "📬 ဒီနေ့ Student Mail List",
        make_separator(),
        f"စုစုပေါင်း - {len(rows)} စောင်"
    ]

    for idx, r in enumerate(rows, start=1):
        lines.append("")
        lines.append(f"{idx}. {safe_mm(r['subject'], 'Subject မရှိပါ')}")
        lines.append(f"👤 ပေးပို့သူ - {safe_mm(r['sender'], 'မဖော်ပြထားပါ')}")
        lines.append(f"⭐ အရေးကြီးမှု - {format_priority_mm(r['importance'])}")
        lines.append(f"📎 Attachment - {r['attachment_count'] or 0} ခု")

        if (r["attachment_count"] or 0) > 0:
            lines.append(safe_mm(r["attachment_summary"], ""))

        lines.append(format_summary_section_mm(r["summary"]))
        lines.append(f"✅ လုပ်ဆောင်ရန် - {safe_mm(r['action_item'], 'မရှိပါ')}")
        lines.append(f"⏰ Deadline - {safe_mm(r['deadline'], 'မဖော်ပြထားပါ')}")
        lines.append(f"💬 Reply - {'လိုအပ်သည်' if r['reply_needed'] == 1 else 'မလိုအပ်ပါ'}")
       

        if r["is_scam"] == 1:
            lines.append("🚨 သတိထားရန် - Scam/Phishing ဖြစ်နိုင်သည်")

    return "\n".join(lines)


def build_period_report(settings, period="today"):
    rows = get_analysis_rows(settings, period, student_only=True)

    if period == "today":
        title = "ဒီနေ့ Student Mail Analysis"
    elif period == "week":
        title = "၇ ရက်စာ Student Mail Analysis"
    elif period == "month":
        title = "ဒီလ Student Mail Analysis"
    else:
        title = "Student Mail Analysis"

    if not rows:
        return (
            f"📭 {title}\n"
            f"{make_separator()}\n\n"
            "ဒီ period အတွင်း student-related mail analysis မရှိသေးပါ။"
        )

    total = len(rows)
    high = sum(1 for r in rows if r["importance"] == "high")
    medium = sum(1 for r in rows if r["importance"] == "medium")
    low = sum(1 for r in rows if r["importance"] == "low")
    scam = sum(1 for r in rows if r["is_scam"] == 1)
    reply_needed = sum(1 for r in rows if r["reply_needed"] == 1)

    try:
        attach_count = sum(int(r["attachment_count"] or 0) for r in rows)
    except Exception:
        attach_count = 0

    return "\n".join([
        f"📊 {title}",
        make_separator(),
        "",
        f"📩 စုစုပေါင်း - {total} စောင်",
        f"📎 Attachment file စုစုပေါင်း - {attach_count} ခု",
        "",
        f"🔥 အလွန်အရေးကြီး - {high}",
        f"⚠️ အရေးကြီး - {medium}",
        f"ℹ️ သာမန် - {low}",
        f"🚨 Scam ဖြစ်နိုင် - {scam}",
        f"💬 Reply လို - {reply_needed}",
    ])


def build_stats_report(settings):
    today_rows = get_analysis_rows(settings, "today", student_only=True)
    week_rows = get_analysis_rows(settings, "week", student_only=True)
    month_rows = get_analysis_rows(settings, "month", student_only=True)

    def count_summary(rows):
        return {
            "total": len(rows),
            "high": sum(1 for r in rows if r["importance"] == "high"),
            "medium": sum(1 for r in rows if r["importance"] == "medium"),
            "low": sum(1 for r in rows if r["importance"] == "low"),
            "scam": sum(1 for r in rows if r["is_scam"] == 1),
            "reply": sum(1 for r in rows if r["reply_needed"] == 1),
            "attachments": sum(int(r["attachment_count"] or 0) for r in rows),
        }

    lines = [
        "📈 Student Mail Analysis စာရင်းချုပ်",
        make_separator(),
        ""
    ]

    for title, rows in [
        ("📅 ဒီနေ့", today_rows),
        ("🗓 ၇ ရက်အတွင်း", week_rows),
        ("📆 ဒီလ", month_rows),
    ]:
        data = count_summary(rows)
        lines.append(title)
        lines.append(f"📩 စုစုပေါင်း - {data['total']}")
        lines.append(f"📎 Attachment files - {data['attachments']}")
        lines.append(f"🔥 အလွန်အရေးကြီး - {data['high']}")
        lines.append(f"⚠️ အရေးကြီး - {data['medium']}")
        lines.append(f"ℹ️ သာမန် - {data['low']}")
        lines.append(f"🚨 Scam ဖြစ်နိုင် - {data['scam']}")
        lines.append(f"💬 Reply လို - {data['reply']}")
        lines.append("")

    return "\n".join(lines).strip()


def send_pending_list(settings, state):
    pending_replies = state["pending_replies"]

    if not pending_replies:
        send_to_telegram(settings, "📭 Pending email မရှိပါ။")
        return

    lines = [
        "📌 Pending Student Emails",
        make_separator()
    ]

    for idx, (_, item) in enumerate(pending_replies.items(), start=1):
        email_data = item["email"]
        analysis = item["analysis"]
        attachments = email_data.get("attachments", [])

        lines.append("")
        lines.append(f"{idx}. {email_data.get('subject', '')}")
        lines.append(f"👤 ပေးပို့သူ - {email_data.get('sender_raw', '')}")
        lines.append(f"⭐ အရေးကြီးမှု - {format_priority_mm(analysis.get('importance'))}")
        lines.append(f"📎 Attachment - {len(attachments)} ခု")

        if attachments:
            lines.append(build_attachment_summary_for_display(settings, attachments))

        lines.append(f"⏰ Deadline - {analysis.get('deadline', 'မဖော်ပြထားပါ')}")
        lines.append(f"💬 Reply - {'လိုအပ်သည်' if analysis.get('reply_needed') else 'မလိုအပ်ပါ'}")
        lines.append(f"🧠 Model - {analysis.get('model_used', 'မဖော်ပြထားပါ')}")

    send_long_telegram_message(settings, "\n".join(lines))


def process_telegram_commands(settings, state):
    updates = get_telegram_updates(settings, state)

    for update in updates:
        state["telegram_last_update_id"] = update.get(
            "update_id",
            state.get("telegram_last_update_id")
        )

        if "callback_query" in update:
            callback = update["callback_query"]
            callback_id = callback.get("id")
            callback_data = callback.get("data", "")
            chat_id = str(callback.get("message", {}).get("chat", {}).get("id", ""))

            if chat_id != str(settings.TELEGRAM_CHAT_ID):
                continue

            if callback_data.startswith("reply:"):
                email_id = callback_data.split(":", 1)[1]

                if email_id not in state["pending_replies"]:
                    answer_callback_query(settings, callback_id, "Email မတွေ့ပါ")
                    send_to_telegram(settings, "❌ ဒီ Email ကို မတွေ့ပါ။ /pending နဲ့ကြည့်ပါ။")
                    continue

                item = state["pending_replies"][email_id]

                if item["analysis"].get("is_scam"):
                    answer_callback_query(settings, callback_id, "Scam ဖြစ်နိုင်လို့ reply မပို့ပါ")
                    send_to_telegram(settings, "🚫 Scam ဖြစ်နိုင်သော mail ဖြစ်လို့ reply မပို့ပါ။")
                    continue

                state["awaiting_reply_email_id"] = email_id
                answer_callback_query(settings, callback_id, "Reply စာရေးပါ")

                send_to_telegram(
                    settings,
                    f"✍️ Reply စာရေးပါ\n\n"
                    f"To: {item['email'].get('sender_email')}\n"
                    f"Subject: {item['email'].get('subject')}\n\n"
                    "နောက်ထပ် Telegram message ကို email reply အဖြစ် ပို့ပါမယ်။\n"
                    "မပို့ချင်တော့ရင် cancel လို့ရေးပါ။"
                )

            elif callback_data.startswith("ignore:"):
                email_id = callback_data.split(":", 1)[1]
                state["pending_replies"].pop(email_id, None)

                if state.get("awaiting_reply_email_id") == email_id:
                    state["awaiting_reply_email_id"] = None

                answer_callback_query(settings, callback_id, "Ignored")
                send_to_telegram(settings, "✅ Ignore လုပ်ပြီးပါပြီ။")

            continue

        message = update.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()

        if chat_id != str(settings.TELEGRAM_CHAT_ID):
            continue

        if not text:
            continue

        if state.get("awaiting_reply_email_id"):
            email_id = state["awaiting_reply_email_id"]

            if text.lower() in ["cancel", "/cancel", "မပို့တော့ပါ", "မပို့တော့ဘူး"]:
                state["awaiting_reply_email_id"] = None
                send_to_telegram(settings, "✅ Reply ပို့ခြင်းကို cancel လုပ်ပြီးပါပြီ။")
                continue

            if email_id not in state["pending_replies"]:
                state["awaiting_reply_email_id"] = None
                send_to_telegram(settings, "❌ ဒီ Email ကို မတွေ့တော့ပါ။")
                continue

            item = state["pending_replies"][email_id]

            if item["analysis"].get("is_scam"):
                state["awaiting_reply_email_id"] = None
                send_to_telegram(settings, "🚫 Scam ဖြစ်နိုင်သော mail ဖြစ်လို့ reply မပို့ပါ။")
                continue

            sent = send_email_reply(settings, item["email"], text)

            if sent:
                send_to_telegram(settings, f"✅ Reply ပို့ပြီးပါပြီ။\nTo: {item['email'].get('sender_email')}")
                state["pending_replies"].pop(email_id, None)
            else:
                send_to_telegram(settings, "❌ Reply ပို့ရာတွင် error ဖြစ်ပါတယ်။")

            state["awaiting_reply_email_id"] = None
            continue

        if text.startswith("/list"):
            send_long_telegram_message(settings, build_today_all_mail_list(settings))

        elif text.startswith("/today"):
            send_long_telegram_message(settings, build_period_report(settings, "today"))

        elif text.startswith("/week"):
            send_long_telegram_message(settings, build_period_report(settings, "week"))

        elif text.startswith("/month"):
            send_long_telegram_message(settings, build_period_report(settings, "month"))

        elif text.startswith("/stats"):
            send_long_telegram_message(settings, build_stats_report(settings))

        elif text.startswith("/pending"):
            send_pending_list(settings, state)

        elif text.startswith("/models"):
            send_to_telegram(
                settings,
                "🧠 Current AI Model Chain\n\n"
                + "\n".join([f"{idx}. {m}" for idx, m in enumerate(get_openrouter_model_chain(settings), start=1)])
            )

        elif text.startswith("/help"):
            send_to_telegram(
                settings,
                "အသုံးပြုနည်း:\n\n"
                "Program run လုပ်တာနဲ့ Gmail Primary unread mail တွေကို စစ်ဆေးပြီး "
                "student-related email များကို Telegram Bot ဆီပို့ပါမည်။\n\n"

                "Rules:\n"
                "- Student email ကိုပဲ အနှစ်ချုပ်ပြပါမည်။\n"
                "- Non-student email ကို အနှစ်ချုပ်မလုပ်ပါ။\n"
                "- Attachment မှာ file count နဲ့ filename ပြပါမယ်။\n\n"

                "Commands:\n"
                "/today - ဒီနေ့ report\n"
                "/week - ၇ ရက်စာ report\n"
                "/month - ဒီလ report\n"
                "/stats - စာရင်းချုပ်\n"
                "/pending - pending reply emails\n"
                "/list - ဒီနေ့ student mail list\n"
                "/help - Help"
            )

        else:
            send_to_telegram(
                settings,
                "ℹ️ Command မသိပါ။\n\n"
                "/today\n"
                "/week\n"
                "/month\n"
                "/stats\n"
                "/pending\n"
                "/list\n"
                "/help"
            )