"""Base parser interface."""
from abc import ABC, abstractmethod
from typing import Optional

from models import Transaction


class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Return True if this parser handles the message."""
        ...

    @abstractmethod
    def parse(self, text: str, source: str = "unknown") -> Optional[Transaction]:
        """Parse the text into a Transaction or None."""
        ...
