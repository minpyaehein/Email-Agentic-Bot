import os
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv


ENV_FILE = ".env"


@dataclass
class Settings:
    EMAIL_USER: str | None
    EMAIL_PASS: str | None

    TELEGRAM_TOKEN: str | None
    TELEGRAM_CHAT_ID: str | None

    OPENROUTER_API_KEY: str | None
    USE_OPENROUTER: bool

    OPENROUTER_PRIMARY_MODEL: str
    OPENROUTER_FALLBACK_MODEL_1: str
    OPENROUTER_FALLBACK_MODEL_2: str
    OPENROUTER_FALLBACK_MODEL_3: str

    CONFIG_UI_ENABLED: bool
    CONFIG_UI_HOST: str
    CONFIG_UI_PORT: int
    CONFIG_UI_SECRET: str

    IMAP_SERVER: str
    SMTP_SERVER: str
    SMTP_PORT: int

    SCRIPT_START_DATE: str

    DB_FILE: str

    STRICT_STUDENT_ONLY: bool
    NOTIFY_NON_STUDENT: bool

    LOOP_SLEEP_SECONDS: int
    MAX_EMAIL_CHARS: int
    MAX_QUEUE_SIZE: int
    MAX_ATTACHMENT_FILENAME_DISPLAY: int


def load_settings() -> Settings:
    load_dotenv(override=True)

    return Settings(
        EMAIL_USER=os.getenv("EMAIL_USER"),
        EMAIL_PASS=os.getenv("EMAIL_PASS"),

        TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN"),
        TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID"),

        OPENROUTER_API_KEY=os.getenv("OPENROUTER_API_KEY"),
        USE_OPENROUTER=os.getenv("USE_OPENROUTER", "true").lower() == "true",

        OPENROUTER_PRIMARY_MODEL=os.getenv(
            "OPENROUTER_PRIMARY_MODEL",
            "openai/gpt-4o"
        ),
        OPENROUTER_FALLBACK_MODEL_1=os.getenv(
            "OPENROUTER_FALLBACK_MODEL_1",
            "anthropic/claude-3.5-sonnet"
        ),
        OPENROUTER_FALLBACK_MODEL_2=os.getenv(
            "OPENROUTER_FALLBACK_MODEL_2",
            "openai/gpt-4o-mini"
        ),
        OPENROUTER_FALLBACK_MODEL_3=os.getenv(
            "OPENROUTER_FALLBACK_MODEL_3",
            "meta-llama/llama-3.1-70b-instruct"
        ),

        CONFIG_UI_ENABLED=os.getenv("CONFIG_UI_ENABLED", "true").lower() == "true",
        CONFIG_UI_HOST=os.getenv("CONFIG_UI_HOST", "127.0.0.1"),
        CONFIG_UI_PORT=int(os.getenv("CONFIG_UI_PORT", "5000")),
        CONFIG_UI_SECRET=os.getenv("CONFIG_UI_SECRET", "student-email-agent-local-ui"),

        IMAP_SERVER="imap.gmail.com",
        SMTP_SERVER="smtp.gmail.com",
        SMTP_PORT=587,

        SCRIPT_START_DATE=datetime.now().strftime("%d-%b-%Y"),

        DB_FILE="student_email_analysis.db",

        STRICT_STUDENT_ONLY=True,
        NOTIFY_NON_STUDENT=False,

        LOOP_SLEEP_SECONDS=30,
        MAX_EMAIL_CHARS=5000,
        MAX_QUEUE_SIZE=100,
        MAX_ATTACHMENT_FILENAME_DISPLAY=12,
    )


def email_configured(settings: Settings) -> bool:
    return bool(settings.EMAIL_USER and settings.EMAIL_PASS)


def telegram_configured(settings: Settings) -> bool:
    return bool(settings.TELEGRAM_TOKEN and settings.TELEGRAM_CHAT_ID)


def get_missing_env(settings: Settings) -> list[str]:
    missing = []

    if not settings.EMAIL_USER:
        missing.append("EMAIL_USER")

    if not settings.EMAIL_PASS:
        missing.append("EMAIL_PASS")

    if not settings.TELEGRAM_TOKEN:
        missing.append("TELEGRAM_TOKEN")

    if not settings.TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")

    if settings.USE_OPENROUTER and not settings.OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")

    return missing


def validate_env(settings: Settings, verbose: bool = True) -> bool:
    missing = get_missing_env(settings)

    if missing:
        if verbose:
            print("❌ အောက်ပါ config value တွေ မရှိပါ:")

            for item in missing:
                print(f" - {item}")

            print(
                f"➡️ Browser မှာ http://{settings.CONFIG_UI_HOST}:{settings.CONFIG_UI_PORT} "
                "ကိုဖွင့်ပြီး ဖြည့်ပါ။"
            )

        return False

    return True


def get_openrouter_model_chain(settings: Settings) -> list[str]:
    models = [
        settings.OPENROUTER_PRIMARY_MODEL,
        settings.OPENROUTER_FALLBACK_MODEL_1,
        settings.OPENROUTER_FALLBACK_MODEL_2,
        settings.OPENROUTER_FALLBACK_MODEL_3,
    ]

    clean = []

    for model in models:
        if model and model not in clean:
            clean.append(model)

    return clean