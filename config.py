"""Configuration loader using environment variables."""
import os
from pathlib import Path


def _load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()


class Config:
    # Email / IMAP
    IMAP_SERVER = os.getenv("IMAP_SERVER") or "imap.gmail.com"
    IMAP_PORT = int((os.getenv("IMAP_PORT") or "993"))
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS") or ""
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") or ""

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or ""
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or ""

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL") or ""

    # App
    LOG_LEVEL = os.getenv("LOG_LEVEL") or "INFO"
    REPORT_DAILY = (os.getenv("REPORT_DAILY") or "true").lower() == "true"
    REPORT_WEEKLY = (os.getenv("REPORT_WEEKLY") or "true").lower() == "true"

    # Keywords for filtering emails
    SUBJECT_KEYWORDS = [
        kw.strip()
        for kw in (os.getenv("SUBJECT_KEYWORDS") or "MoMo,Debit Alert,Credit Alert").split(",")
    ]

    # SMS Configuration
    SMS_SOURCE = os.getenv("SMS_SOURCE") or "file"  # 'twilio' or 'file'
    SMS_FILE_PATH = os.getenv("SMS_FILE_PATH") or "data/sms.txt"
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID") or ""
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN") or ""
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER") or ""

    @classmethod
    def validate(cls):
        missing = []
        for attr in ["EMAIL_ADDRESS", "EMAIL_PASSWORD", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "DATABASE_URL"]:
            if not getattr(cls, attr):
                missing.append(attr)
        if missing:
            raise ValueError(f"Missing config values: {', '.join(missing)}")
