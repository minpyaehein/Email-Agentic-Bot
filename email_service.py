import imaplib
import email
import re
import smtplib

from email.header import decode_header
from email.utils import parseaddr
from email.message import EmailMessage

from bs4 import BeautifulSoup

from config import email_configured
from database import email_already_saved
from text_utils import (
    sanitize_header_value,
    sanitize_email_address,
    clean_text_for_nlp,
    smart_truncate,
)


def decode_mime_header(value):
    if not value:
        return ""

    decoded_parts = decode_header(value)
    result = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="ignore")
        else:
            result += str(part)

    return sanitize_header_value(result)


def clean_email_body(raw_body):
    if not raw_body:
        return ""

    soup = BeautifulSoup(raw_body, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    clean_text = soup.get_text(separator="\n")
    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    return "\n".join(lines)


def extract_email_body(msg):
    raw_body = ""

    if msg.is_multipart():
        plain_body = ""
        html_body = ""

        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition.lower():
                continue

            payload = part.get_payload(decode=True)

            if not payload:
                continue

            try:
                decoded_payload = payload.decode(errors="ignore")
            except Exception:
                decoded_payload = ""

            if content_type == "text/plain":
                plain_body = decoded_payload
                break

            if content_type == "text/html":
                html_body = decoded_payload

        raw_body = plain_body if plain_body else html_body

    else:
        payload = msg.get_payload(decode=True)

        if payload:
            raw_body = payload.decode(errors="ignore")

    return clean_email_body(raw_body)


def truncate_email_body(settings, body):
    if not body:
        return ""

    if len(body) <= settings.MAX_EMAIL_CHARS:
        return body

    return body[:settings.MAX_EMAIL_CHARS] + "\n\n[Email body truncated]"


def decode_attachment_filename(filename):
    if not filename:
        return "unknown_file"

    try:
        decoded_parts = decode_header(filename)
        result = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result += part.decode(encoding or "utf-8", errors="ignore")
            else:
                result += str(part)

        result = result.replace("\r", " ").replace("\n", " ")
        result = re.sub(r"\s+", " ", result).strip()

        return result or "unknown_file"

    except Exception:
        return str(filename).replace("\r", " ").replace("\n", " ").strip() or "unknown_file"


def get_file_extension(filename):
    filename = filename or ""

    if "." not in filename:
        return "unknown"

    return filename.rsplit(".", 1)[-1].lower().strip() or "unknown"


def extract_attachments_metadata_only(msg):
    attachments = []

    if not msg.is_multipart():
        return attachments

    for part in msg.walk():
        content_disp = str(part.get("Content-Disposition", "")).lower()

        if "attachment" not in content_disp:
            continue

        filename = decode_attachment_filename(part.get_filename())

        attachments.append({
            "filename": filename,
            "extension": get_file_extension(filename),
            "content_type": part.get_content_type()
        })

    return attachments


def build_attachment_summary_for_ai(settings, attachments):
    if not attachments:
        return "Attachment မရှိပါ။"

    lines = [f"Attachment count: {len(attachments)}", "Files:"]

    for idx, item in enumerate(attachments[:settings.MAX_ATTACHMENT_FILENAME_DISPLAY], start=1):
        lines.append(
            f"{idx}. {item.get('filename', 'unknown_file')} | "
            f"extension: {item.get('extension', 'unknown')}"
        )

    if len(attachments) > settings.MAX_ATTACHMENT_FILENAME_DISPLAY:
        lines.append(f"... more files: {len(attachments) - settings.MAX_ATTACHMENT_FILENAME_DISPLAY}")

    lines.append("Attachment content was NOT read. Only filenames and metadata are available.")
    return "\n".join(lines)


def build_attachment_summary_for_display(settings, attachments):
    if not attachments:
        return "Attachment file 0 ခု\nFile မရှိပါ။"

    lines = [
        f"Attachment file {len(attachments)} ခု ပါရှိသည်။",
        "File name များ:"
    ]

    for idx, item in enumerate(attachments[:settings.MAX_ATTACHMENT_FILENAME_DISPLAY], start=1):
        lines.append(f"{idx}. {item.get('filename', 'unknown_file')}")

    if len(attachments) > settings.MAX_ATTACHMENT_FILENAME_DISPLAY:
        lines.append(f"နောက်ထပ် file {len(attachments) - settings.MAX_ATTACHMENT_FILENAME_DISPLAY} ခု ရှိပါသည်။")

    return "\n".join(lines)


def search_gmail_primary_unread(settings, mail):
    try:
        status, messages = mail.search(
            None,
            "X-GM-RAW",
            '"category:primary is:unread"',
            "SINCE",
            settings.SCRIPT_START_DATE
        )

        if status == "OK":
            return status, messages

    except Exception as e:
        print(f"Primary unread search failed: {e}")

    try:
        search_query = f'(UNSEEN SINCE {settings.SCRIPT_START_DATE})'
        return mail.search(None, search_query)

    except Exception as e:
        print(f"Fallback unread search failed: {e}")
        return "NO", [b""]


def fetch_new_primary_unread_emails(settings, processed_email_uids):
    if not email_configured(settings):
        print("⚠️ Email config မပြည့်စုံသေးပါ။")
        return []

    mail = None
    new_emails = []

    try:
        mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER)
        mail.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        mail.select("inbox")

        status, messages = search_gmail_primary_unread(settings, mail)

        if status != "OK":
            print(f"⚠️ Email search failed: {status}")
            return []

        email_ids = messages[0].split()

        if not email_ids:
            return []

        for email_id in email_ids:
            if email_id in processed_email_uids:
                continue

            status, data = mail.fetch(email_id, "(RFC822)")

            if status != "OK":
                print(f"⚠️ Email fetch failed: {status}")
                continue

            for response_part in data:
                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                subject = sanitize_header_value(decode_mime_header(msg.get("Subject")))
                sender_raw = sanitize_header_value(decode_mime_header(msg.get("From")))

                sender_name, sender_email = parseaddr(sender_raw)
                sender_name = sanitize_header_value(sender_name)
                sender_email = sanitize_email_address(sender_email)

                body = extract_email_body(msg)
                body = truncate_email_body(settings, body)
                body_cleaned = clean_text_for_nlp(body)

                attachments = extract_attachments_metadata_only(msg)
                attachment_summary_ai = build_attachment_summary_for_ai(settings, attachments)
                attachment_display_summary = build_attachment_summary_for_display(settings, attachments)

                full_content = smart_truncate(
                    "EMAIL CONTENT:\n\n"
                    + body_cleaned
                    + "\n\nATTACHMENT METADATA ONLY:\n\n"
                    + attachment_summary_ai,
                    6000
                )

                message_id = sanitize_header_value(msg.get("Message-ID", ""))
                references = sanitize_header_value(msg.get("References", ""))
                in_reply_to = sanitize_header_value(msg.get("In-Reply-To", ""))

                email_key = message_id or sanitize_header_value(email_id.decode(errors="ignore"))

                if email_already_saved(settings, email_key):
                    processed_email_uids.add(email_id)
                    continue

                processed_email_uids.add(email_id)

                email_data = {
                    "uid": sanitize_header_value(email_id.decode(errors="ignore")),
                    "sender_raw": sender_raw,
                    "sender_name": sender_name,
                    "sender_email": sender_email,
                    "subject": subject,
                    "body": full_content,
                    "plain_body": body_cleaned,
                    "attachments": attachments,
                    "attachment_summary": attachment_summary_ai,
                    "attachment_display_summary": attachment_display_summary,
                    "message_id": message_id,
                    "references": references,
                    "in_reply_to": in_reply_to,
                }

                new_emails.append(email_data)

    except imaplib.IMAP4.error as e:
        print(f"IMAP login/search error: {e}")

    except Exception as e:
        print(f"Error fetching unread emails: {e}")

    finally:
        try:
            if mail:
                mail.logout()
        except Exception:
            pass

    return new_emails


def send_email_reply(settings, original_email, reply_text):
    if not email_configured(settings):
        print("❌ Email config မပြည့်စုံပါ။")
        return False

    sender_email = sanitize_email_address(original_email.get("sender_email"))

    if not sender_email:
        print("❌ Sender email မတွေ့ပါ။")
        return False

    original_subject = sanitize_header_value(original_email.get("subject", ""))
    subject = original_subject

    if not subject.lower().startswith("re:"):
        subject = "Re: " + subject

    msg = EmailMessage()
    msg["From"] = sanitize_email_address(settings.EMAIL_USER)
    msg["To"] = sender_email
    msg["Subject"] = sanitize_header_value(subject)

    original_message_id = sanitize_header_value(original_email.get("message_id", ""))

    if original_message_id:
        msg["In-Reply-To"] = original_message_id

    references = sanitize_header_value(original_email.get("references", ""))

    if references or original_message_id:
        combined = sanitize_header_value((references + " " + original_message_id).strip())

        if combined:
            msg["References"] = combined

    msg.set_content(reply_text)

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(settings.EMAIL_USER, settings.EMAIL_PASS)
            smtp.send_message(msg)

        return True

    except Exception as e:
        print(f"❌ Email reply send error: {e}")
        return False