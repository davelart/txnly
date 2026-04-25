"""Shared utilities and helpers."""
import logging
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_iso(value: str) -> datetime:
    """Parse ISO datetime string; fallback to date-only then to now."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def setup_logging(level: str = "INFO"):
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_dir / "finance_tracker.log")),
        ],
    )


def extract_date(text: str) -> datetime:
    """Try to find a date in the text; fallback to now."""
    patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{2}-\d{2}-\d{4})",
        r"(\d{2}\s+[A-Za-z]{3}\s+\d{4})",
        r"([A-Za-z]{3}\s+\d{2},?\s+\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            date_str = m.group(1)
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%b %d, %Y", "%b %d %Y"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
    return datetime.now(timezone.utc)


def period_dates(period: str) -> tuple:
    """Return (start, end) for daily, weekly, monthly summaries."""
    now = datetime.now(timezone.utc)
    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period == "weekly":
        start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)
    elif period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1)
    else:
        start = None
        end = None
    return start, end


def sanitize_text(text: str) -> str:
    return " ".join(text.split())
