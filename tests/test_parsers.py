"""Unit tests for transaction parsers."""
import pytest

from parsers.bank_parser import BankParser
from parsers.momo_parser import MoMoParser


class TestMoMoParser:
    def setup_method(self):
        self.parser = MoMoParser()

    def test_can_parse_momo_keywords(self):
        assert self.parser.can_parse("You have received GHS 100 via MoMo")
        assert self.parser.can_parse("MTN Mobile Money alert")
        assert not self.parser.can_parse("Random unrelated text")

    def test_parse_received(self):
        text = (
            "You have received GHS 250.00 from John Doe "
            "with reference: INV-2025-04. Current balance is GHS 1,200.00"
        )
        tx = self.parser.parse(text)
        assert tx is not None
        assert tx.amount == 250.0
        assert tx.type == "credit"
        assert tx.sender == "John Doe"
        assert tx.recipient == "You"
        assert tx.reference == "INV-2025-04"

    def test_parse_sent(self):
        text = (
            "You have sent GHS 50.00 to Jane Smith. "
            "Transaction ID: TXN-998877. Thank you for using MoMo."
        )
        tx = self.parser.parse(text)
        assert tx is not None
        assert tx.amount == 50.0
        assert tx.type == "debit"
        assert tx.sender == "You"
        assert tx.recipient == "Jane Smith"
        assert "TXN-998877" in (tx.reference or "")

    def test_parse_airtime(self):
        text = (
            "You have bought airtime worth GHS 10.00 from MTN. "
            "Transaction ID: AIR-112233."
        )
        tx = self.parser.parse(text)
        assert tx is not None
        assert tx.amount == 10.0
        assert tx.type == "debit"
        assert tx.category == "Utilities"

    def test_parse_malformed_returns_none(self):
        text = "MoMo something something no money here"
        tx = self.parser.parse(text)
        assert tx is None


class TestBankParser:
    def setup_method(self):
        self.parser = BankParser()

    def test_can_parse_bank_keywords(self):
        assert self.parser.can_parse("Debit Alert: GHS 500 from your account")
        assert self.parser.can_parse("Credit Alert: GHS 1,000 deposited")
        assert not self.parser.can_parse("Hello this is spam")

    def test_parse_debit(self):
        text = (
            "Debit Alert: A debit of GHS 300.00 has been made to Supermarket Ltd. "
            "Reference: DEB-001. Thank you for banking with us."
        )
        tx = self.parser.parse(text)
        assert tx is not None
        assert tx.amount == 300.0
        assert tx.type == "debit"

    def test_parse_credit(self):
        text = (
            "Credit Alert: A credit of GHS 5,000.00 from Employer Inc. "
            "Ref: CR-2025-04."
        )
        tx = self.parser.parse(text)
        assert tx is not None
        assert tx.amount == 5000.0
        assert tx.type == "credit"

    def test_parse_malformed_returns_none(self):
        text = "Bank statement without amount"
        tx = self.parser.parse(text)
        assert tx is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
