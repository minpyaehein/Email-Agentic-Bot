import sqlite3
from datetime import datetime, timedelta

from text_utils import sanitize_header_value, sanitize_email_address


def init_database(settings):
    conn = sqlite3.connect(settings.DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT,
            received_at TEXT,
            sender TEXT,
            sender_email TEXT,
            subject TEXT,
            attachment_count INTEGER DEFAULT 0,
            attachment_summary TEXT,
            target_domain TEXT,
            domain_confidence INTEGER,
            is_scam INTEGER,
            scam_confidence INTEGER,
            importance TEXT,
            reply_needed INTEGER,
            reply_urgency TEXT,
            summary TEXT,
            action_item TEXT,
            deadline TEXT,
            provider_used TEXT,
            model_used TEXT
        )
    """)

    conn.commit()
    conn.close()


def email_already_saved(settings, email_key):
    email_key = sanitize_header_value(email_key)

    if not email_key:
        return False

    try:
        conn = sqlite3.connect(settings.DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM email_analysis WHERE email_id = ? LIMIT 1",
            (email_key,)
        )

        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    except Exception:
        return False


def save_analysis_to_db(settings, email_data, analysis):
    try:
        email_key = sanitize_header_value(email_data.get("message_id") or email_data.get("uid"))

        if email_already_saved(settings, email_key):
            return

        attachments = email_data.get("attachments", [])
        attachment_count = len(attachments) if isinstance(attachments, list) else 0

        conn = sqlite3.connect(settings.DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO email_analysis (
                email_id,
                received_at,
                sender,
                sender_email,
                subject,
                attachment_count,
                attachment_summary,
                target_domain,
                domain_confidence,
                is_scam,
                scam_confidence,
                importance,
                reply_needed,
                reply_urgency,
                summary,
                action_item,
                deadline,
                provider_used,
                model_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email_key,
            datetime.now().isoformat(),
            sanitize_header_value(email_data.get("sender_raw")),
            sanitize_email_address(email_data.get("sender_email")),
            sanitize_header_value(email_data.get("subject")),
            attachment_count,
            email_data.get("attachment_display_summary", ""),
            analysis.get("target_domain"),
            int(analysis.get("domain_confidence", 0)),
            1 if analysis.get("is_scam") else 0,
            int(analysis.get("scam_confidence", 0)),
            analysis.get("importance"),
            1 if analysis.get("reply_needed") else 0,
            analysis.get("reply_urgency"),
            analysis.get("summary"),
            analysis.get("action_item"),
            analysis.get("deadline"),
            analysis.get("provider_used"),
            analysis.get("model_used")
        ))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"DB save error: {e}")


def get_analysis_rows(settings, period="today", student_only=True):
    now = datetime.now()

    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    conn = sqlite3.connect(settings.DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT * FROM email_analysis
        WHERE received_at >= ?
    """

    params = [start.isoformat()]

    if student_only:
        query += " AND target_domain = ?"
        params.append("student")

    query += " ORDER BY received_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return rows