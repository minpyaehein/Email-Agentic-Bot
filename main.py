import time
from collections import deque

from config import (
    load_settings,
    validate_env,
    get_missing_env,
    telegram_configured,
    get_openrouter_model_chain,
)
from config_ui import start_config_ui
from database import init_database, save_analysis_to_db, get_analysis_rows
from email_service import fetch_new_primary_unread_emails
from ai_service import (
    is_student_email,
    analyse_email_with_ai,
    rule_only_analysis,
    enforce_analysis_consistency,
)
from telegram_service import (
    process_telegram_commands,
    build_telegram_report,
    send_to_telegram,
)


processed_email_uids = set()
email_queue = deque()

state = {
    "pending_replies": {},
    "telegram_last_update_id": None,
    "awaiting_reply_email_id": None,
}


def debug_today_importance_counts(settings):
    rows = get_analysis_rows(settings, "today", student_only=True)

    high = sum(1 for r in rows if r["importance"] == "high")
    medium = sum(1 for r in rows if r["importance"] == "medium")
    low = sum(1 for r in rows if r["importance"] == "low")

    print("DEBUG TODAY STUDENT COUNTS")
    print(f"Total: {len(rows)}")
    print(f"High: {high}")
    print(f"Medium: {medium}")
    print(f"Low: {low}")


def add_email_to_queue(settings, email_data):
    if len(email_queue) >= settings.MAX_QUEUE_SIZE:
        print("⚠️ Email queue full. Email skipped.")
        return False

    email_queue.append(email_data)
    return True


def process_email_queue(settings):
    if not email_queue:
        return

    email_data = email_queue.popleft()
    email_id = email_data["uid"]

    domain_check = is_student_email(email_data)

    print(
        f"🔎 Student signal check: "
        f"Score={domain_check.get('domain_score')} | "
        f"Student={domain_check.get('is_student')} | "
        f"Groups={domain_check.get('matched_groups', [])}"
    )

    # Important:
    # Do not skip borderline emails too early.
    # 0-9 = clearly not student
    # 10-24 = uncertain, let AI decide
    # 25+ = likely student
    LOW_CONFIDENCE_SKIP_SCORE = 10

    if (
        settings.STRICT_STUDENT_ONLY
        and not domain_check["is_student"]
        and domain_check.get("domain_score", 0) < LOW_CONFIDENCE_SKIP_SCORE
    ):
        analysis = rule_only_analysis(email_data, domain_check)
        analysis = enforce_analysis_consistency(analysis)

        save_analysis_to_db(settings, email_data, analysis)

        print(
            f"⏭ Student signal အလွန်နည်းသော email ကို summary မလုပ်ဘဲ DB ထဲသိမ်းထားသည်: "
            f"{email_data.get('subject', '')} | Score: {domain_check['domain_score']}"
        )

        if settings.NOTIFY_NON_STUDENT:
            report_text, reply_markup = build_telegram_report(email_id, email_data, analysis)
            send_to_telegram(settings, report_text, reply_markup=reply_markup)

        return

    # If score is medium or high, ask AI.
    # If AI fails, rule-only fallback will still work.
    analysis = analyse_email_with_ai(settings, email_data, domain_check)

    if analysis is None:
        analysis = rule_only_analysis(email_data, domain_check)
        analysis = enforce_analysis_consistency(analysis)

    save_analysis_to_db(settings, email_data, analysis)

    if analysis.get("target_domain") == "student":
        state["pending_replies"][email_id] = {
            "email": email_data,
            "analysis": analysis,
        }

        report_text, reply_markup = build_telegram_report(email_id, email_data, analysis)
        send_to_telegram(settings, report_text, reply_markup=reply_markup)

        print(
            f"✅ Telegram သို့ Student Email စစ်ဆေးချက် ပို့ပြီးပါပြီ။ "
            f"Priority: {analysis.get('importance')} | "
            f"AI: {analysis.get('provider_used', 'unknown')} | "
            f"Model: {analysis.get('model_used', 'unknown')} | "
            f"Attachments content read: False"
        )

    else:
        print(
            f"⏭ AI/Rule က other အဖြစ် သတ်မှတ်ထားသောကြောင့် Telegram မပို့ပါ: "
            f"{email_data.get('subject', '')} | "
            f"Score: {domain_check.get('domain_score')}"
        )

        if settings.NOTIFY_NON_STUDENT:
            report_text, reply_markup = build_telegram_report(email_id, email_data, analysis)
            send_to_telegram(settings, report_text, reply_markup=reply_markup)


def main():
    settings = load_settings()

    print("AI Email Agent စတင်အလုပ်လုပ်ပါပြီ...")
    print("Mode: Student-only summary + Attachment filename-only + OpenRouter multi-model")
    print("Mail Mode: Gmail Primary UNREAD emails since today 00:00")
    print("Attachment Mode: Count + filename only. Attachment content will NOT be read.")

    print(f"📧 Email User: {settings.EMAIL_USER}")
    print(f"🌐 IMAP Server: {settings.IMAP_SERVER}")
    print(f"🧠 OpenRouter Enabled: {settings.USE_OPENROUTER}")

    print("🧠 Model Order:")
    for idx, model in enumerate(get_openrouter_model_chain(settings), start=1):
        print(f"   {idx}. {model}")

    print(f"ℹ️ {settings.SCRIPT_START_DATE} နောက်ပိုင်း Primary unread mail တွေကို စောင့်ကြည့်ပါမည်။")

    start_config_ui(settings)

    init_database(settings)
    print("✅ Database ပြင်ဆင်ပြီးပါပြီ။")
    print("✅ Student-only summary mode enabled.")
    print("✅ Attachment count + filename-only mode enabled.")
    print("✅ Config UI enabled.")
    print(f"⚙️ Config UI: http://{settings.CONFIG_UI_HOST}:{settings.CONFIG_UI_PORT}")

    if not validate_env(settings, verbose=True):
        print("⏳ Config မပြည့်စုံသေးပါ။ UI ကနေ ဖြည့်ပြီး Save လုပ်ပါ။")

    debug_today_importance_counts(settings)

    last_env_ok = None

    while True:
        try:
            settings = load_settings()
            env_ok = validate_env(settings, verbose=False)

            if env_ok != last_env_ok:
                if env_ok:
                    print("✅ Config ပြည့်စုံပါပြီ။ Email monitoring စတင်နိုင်ပါပြီ။")
                else:
                    missing = get_missing_env(settings)
                    print(f"⚠️ Config မပြည့်စုံသေးပါ: {', '.join(missing)}")
                    print(f"➡️ UI မှာဖြည့်ပါ: http://{settings.CONFIG_UI_HOST}:{settings.CONFIG_UI_PORT}")

                last_env_ok = env_ok

            if telegram_configured(settings):
                process_telegram_commands(settings, state)

            if not env_ok:
                time.sleep(settings.LOOP_SLEEP_SECONDS)
                continue

            new_emails = fetch_new_primary_unread_emails(settings, processed_email_uids)

            if new_emails:
                print(f"🔔 Primary unread email {len(new_emails)} စောင် တွေ့ရှိသည်။")

                for email_data in new_emails:
                    added = add_email_to_queue(settings, email_data)

                    if added:
                        attachments = email_data.get("attachments", [])
                        attachment_count = len(attachments) if isinstance(attachments, list) else 0

                        print(
                            f"📥 Queue ထဲထည့်ပြီးပါပြီ: "
                            f"{email_data.get('subject', '')} | "
                            f"Attachments: {attachment_count} | "
                            f"Queue size: {len(email_queue)}"
                        )

            process_email_queue(settings)

        except KeyboardInterrupt:
            print("\n👋 Program ကို အသုံးပြုသူမှ ပိတ်လိုက်ပါသည်။")
            break

        except Exception as main_error:
            print(f"❌ ပတ်လမ်းအတွင်း အမှားတစ်ခုတက်သွားသည်: {main_error}")

        time.sleep(settings.LOOP_SLEEP_SECONDS)


if __name__ == "__main__":
    main()