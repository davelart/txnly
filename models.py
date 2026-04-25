"""Pydantic-style data models for transactions."""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Transaction:
    amount: float
    type: str  # credit | debit
    source: str  # momo | bank | manual
    sender: Optional[str] = None
    recipient: Optional[str] = None
    category: Optional[str] = None
    reference: Optional[str] = None
    date: Optional[datetime] = None
    raw_text: Optional[str] = None
    hash_id: str = field(init=False, repr=False)

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now(timezone.utc)
        if self.category is None:
            self.category = self._auto_categorize()
        self.hash_id = self._compute_hash()

    def _compute_hash(self) -> str:
        content = f"{self.amount}|{self.type}|{self.source}|{self.sender}|{self.recipient}|{self.reference}|{self.date.isoformat() if self.date else ''}|{self.raw_text or ''}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _auto_categorize(self) -> str:
        """Basic rule-based auto-categorization."""
        text = (self.raw_text or "").lower()
        if self.type == "debit":
            if any(kw in text for kw in ["food", "restaurant", "eat", "chop", "lunch", "dinner"]):
                return "Food"
            if any(kw in text for kw in ["transport", "uber", "taxi", "tro tro", "fuel", "petrol"]):
                return "Transport"
            if any(kw in text for kw in ["airtime", "bundle", "data", "mtn", "vodafone", "tigo"]):
                return "Utilities"
            if any(kw in text for kw in ["rent", "house", "accommodation", "hostel"]):
                return "Housing"
            if any(kw in text for kw in ["health", "hospital", "pharmacy", "doctor", "clinic"]):
                return "Health"
            return "Other"
        return "Income"
