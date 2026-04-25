"""Generic bank email/SMS parser."""
import logging
import re
from typing import Optional

from models import Transaction
from parsers.base_parser import BaseParser
from utils import extract_date

logger = logging.getLogger(__name__)

BANK_DEBIT_PATTERN = re.compile(
    r"(?:debit alert|debit)\s*[:\-]?\s*.*?GHS\s*([\d,]+\.?\d*).*?(?:to|at|from)\s+(.+?)(?:Ref|Reference|Txn ID|Transaction ID)[\s:]*(.+?)(?:\.|$)",
    re.IGNORECASE | re.DOTALL,
)

BANK_CREDIT_PATTERN = re.compile(
    r"(?:credit alert|credit|deposit)\s*[:\-]?\s*.*?GHS\s*([\d,]+\.?\d*).*?(?:from|by)\s+(.+?)(?:Ref|Reference|Txn ID|Transaction ID)[\s:]*(.+?)(?:\.|$)",
    re.IGNORECASE | re.DOTALL,
)

BANK_GENERIC_PATTERN = re.compile(
    r"(?:amount|amt)[\s:]*GHS\s*([\d,]+\.?\d*).*?(?:to|from|at|by)\s+(.+?)(?:Ref|Reference|Txn)[\s:]*(.+?)(?:\.|$)",
    re.IGNORECASE | re.DOTALL,
)

BANK_KEYWORDS = [
    "debit alert",
    "credit alert",
    "transaction alert",
    "bank",
    "account",
    "stanbic",
    "ecobank",
    "gtbank",
    "fidelity",
    "absa",
    "calbank",
    "societe generale",
    "uba",
    "zenith",
    "ghs",
    "cedi",
]


def _clean_amount(amount_str: str) -> float:
    return float(amount_str.replace(",", ""))


def _clean_name(name: str) -> Optional[str]:
    name = name.strip().replace("\n", " ").replace("\r", "")
    if len(name) > 100:
        name = name[:100]
    return name if name else None


class BankParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        lowered = text.lower()
        return any(kw in lowered for kw in BANK_KEYWORDS)

    def parse(self, text: str, source: str = "bank") -> Optional[Transaction]:
        tx = self._try_patterns(text, source)
        if tx is None:
            logger.warning("Bank parser could not parse message: %s...", text[:80])
        return tx

    def _try_patterns(self, text: str, source: str) -> Optional[Transaction]:
        lowered = text.lower()

        # Debit
        if "debit" in lowered or "withdraw" in lowered or "payment" in lowered:
            m = BANK_DEBIT_PATTERN.search(text)
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

        # Credit
        if "credit" in lowered or "deposit" in lowered or "received" in lowered:
            m = BANK_CREDIT_PATTERN.search(text)
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

        # Generic fallback
        m = BANK_GENERIC_PATTERN.search(text)
        if m:
            return Transaction(
                amount=_clean_amount(m.group(1)),
                type="debit" if "debit" in lowered or "withdraw" in lowered else "credit",
                source=source,
                sender="You" if "debit" in lowered or "withdraw" in lowered else _clean_name(m.group(2)),
                recipient=_clean_name(m.group(2)) if "debit" in lowered or "withdraw" in lowered else "You",
                reference=_clean_name(m.group(3)),
                date=extract_date(text),
                raw_text=text,
            )

        return None
