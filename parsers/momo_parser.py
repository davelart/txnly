"""MoMo (Mobile Money) transaction parser."""
import logging
import re
from typing import Optional

from models import Transaction
from parsers.base_parser import BaseParser
from utils import extract_date

logger = logging.getLogger(__name__)

# Ghana MoMo patterns (English)
MOMO_RECEIVE_PATTERN = re.compile(
    r"You have received\s+GHS\s*([\d,]+\.?\d*)\s+from\s+(.+?)\s+(?:with reference|Reference|ref)[\s:]*(.+?)(?:\. Current balance|$)",
    re.IGNORECASE | re.DOTALL,
)

MOMO_SEND_PATTERN = re.compile(
    r"You have sent\s+GHS\s*([\d,]+\.?\d*)\s+to\s+(.+?)(?:\.\s+Transaction ID|Reference|ref)[\s:]*(.+?)(?:\.|$)",
    re.IGNORECASE | re.DOTALL,
)

MOMO_DEBIT_ALERT_PATTERN = re.compile(
    r"(?:A\s+)?(?:debit|payment|transfer)\s+of\s+GHS\s*([\d,]+\.?\d*)\s+(?:has been made|to|from)\s+(.+?)(?:Reference|ref|ID)[\s:]*(.+?)(?:\.|$)",
    re.IGNORECASE | re.DOTALL,
)

MOMO_AIRTIME_DATA_PATTERN = re.compile(
    r"You have bought\s+(?:airtime|data|bundle)\s+worth\s+GHS\s*([\d,]+\.?\d*)\s*(?:from)?\s*(.+?)?(?:Transaction ID|ref)[\s:]*(.+?)(?:\.|$)",
    re.IGNORECASE | re.DOTALL,
)

MOMO_DEPOSIT_PATTERN = re.compile(
    r"You have deposited\s+GHS\s*([\d,]+\.?\d*)\s+(?:into|to)?\s*(?:your account)?\s*(?:from)?\s*(.+?)?(?:Reference|ref)?[\s:]*(.+?)(?:\. Current balance|$)",
    re.IGNORECASE | re.DOTALL,
)

MOMO_CASHOUT_PATTERN = re.compile(
    r"You have cashed out\s+GHS\s*([\d,]+\.?\d*)\s+(?:from|at)\s+(.+?)(?:Transaction ID|ref)[\s:]*(.+?)(?:\. Current balance|$)",
    re.IGNORECASE | re.DOTALL,
)

ALL_MOMO_KEYWORDS = [
    "momo",
    "mobile money",
    "mtn",
    "vodafone cash",
    "airtel",
    "tigo cash",
    "you have received",
    "you have sent",
    "you have bought",
    "you have deposited",
    "you have cashed out",
    "ghs",
]


def _clean_amount(amount_str: str) -> float:
    return float(amount_str.replace(",", ""))


def _clean_name(name: str) -> Optional[str]:
    name = name.strip().replace("\n", " ").replace("\r", "")
    if len(name) > 100:
        name = name[:100]
    return name if name else None


class MoMoParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        lowered = text.lower()
        return any(kw in lowered for kw in ALL_MOMO_KEYWORDS)

    def parse(self, text: str, source: str = "momo") -> Optional[Transaction]:
        tx = self._try_patterns(text, source)
        if tx is None:
            logger.warning("MoMo parser could not parse message: %s...", text[:80])
        return tx

    def _try_patterns(self, text: str, source: str) -> Optional[Transaction]:
        # Pattern 1: Received
        m = MOMO_RECEIVE_PATTERN.search(text)
        if m:
            return Transaction(
                amount=_clean_amount(m.group(1)),
                type="credit",
                source=source,
                sender=_clean_name(m.group(2)),
                recipient="You",
                reference=_clean_name(m.group(3)),
                date=extract_date(text),
                raw_text=text,
            )

        # Pattern 2: Sent
        m = MOMO_SEND_PATTERN.search(text)
        if m:
            return Transaction(
                amount=_clean_amount(m.group(1)),
                type="debit",
                source=source,
                sender="You",
                recipient=_clean_name(m.group(2)),
                reference=_clean_name(m.group(3)),
                date=extract_date(text),
                raw_text=text,
            )

        # Pattern 3: Debit / Payment
        m = MOMO_DEBIT_ALERT_PATTERN.search(text)
        if m:
            return Transaction(
                amount=_clean_amount(m.group(1)),
                type="debit",
                source=source,
                sender="You",
                recipient=_clean_name(m.group(2)),
                reference=_clean_name(m.group(3)),
                date=extract_date(text),
                raw_text=text,
            )

        # Pattern 4: Airtime / Data
        m = MOMO_AIRTIME_DATA_PATTERN.search(text)
        if m:
            return Transaction(
                amount=_clean_amount(m.group(1)),
                type="debit",
                source=source,
                sender="You",
                recipient=_clean_name(m.group(2) or "Service Provider"),
                reference=_clean_name(m.group(3)),
                date=extract_date(text),
                raw_text=text,
            )

        # Pattern 5: Deposit
        m = MOMO_DEPOSIT_PATTERN.search(text)
        if m:
            return Transaction(
                amount=_clean_amount(m.group(1)),
                type="credit",
                source=source,
                sender=_clean_name(m.group(2) or "Agent"),
                recipient="You",
                reference=_clean_name(m.group(3) or ""),
                date=extract_date(text),
                raw_text=text,
            )

        # Pattern 6: Cash Out
        m = MOMO_CASHOUT_PATTERN.search(text)
        if m:
            return Transaction(
                amount=_clean_amount(m.group(1)),
                type="debit",
                source=source,
                sender="You",
                recipient=_clean_name(m.group(2)),
                reference=_clean_name(m.group(3)),
                date=extract_date(text),
                raw_text=text,
            )

        return None
