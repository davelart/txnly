"""Entry point for the finance tracker automation."""
import json
import logging
import sys
from pathlib import Path

import db
from config import Config
from models import Transaction
from parsers.bank_parser import BankParser
from parsers.momo_parser import MoMoParser
from services.email_service import fetch_unread_emails
from services.reporting_service import run_scheduled_reports
from utils import setup_logging, parse_iso

logger = logging.getLogger(__name__)

PARSERS = [MoMoParser(), BankParser()]


def load_manual_transactions() -> list:
    """Load manual transactions from JSON or CSV."""
    txs: list = []
    data_dir = Path(__file__).parent / "data"
    json_path = data_dir / "manual.json"
    csv_path = data_dir / "manual.csv"

    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            try:
                tx = Transaction(
                    amount=float(item.get("amount", 0)),
                    type=item.get("type", "debit"),
                    source=item.get("source", "manual"),
                    sender=item.get("sender"),
                    recipient=item.get("recipient"),
                    category=item.get("category"),
                    reference=item.get("reference"),
                    date=parse_iso(item.get("date")) if item.get("date") else None,
                    raw_text=item.get("raw_text", str(item)),
                )
                txs.append(tx)
            except Exception as exc:
                logger.error("Failed to parse manual JSON entry: %s - %s", item, exc)

    if csv_path.exists():
        import csv
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    tx = Transaction(
                        amount=float(row.get("amount", 0)),
                        type=row.get("type", "debit"),
                        source=row.get("source", "manual"),
                        sender=row.get("sender") or None,
                        recipient=row.get("recipient") or None,
                        category=row.get("category") or None,
                        reference=row.get("reference") or None,
                        date=parse_iso(row.get("date")) if row.get("date") else None,
                        raw_text=str(row),
                    )
                    txs.append(tx)
                except Exception as exc:
                    logger.error("Failed to parse manual CSV row: %s - %s", row, exc)

    logger.info("Loaded %d manual transactions", len(txs))
    return txs


def parse_email_transactions():
    """Fetch unread emails and parse transactions."""
    emails = fetch_unread_emails()
    parsed = 0
    for uid, subject, body in emails:
        for parser in PARSERS:
            if parser.can_parse(body):
                try:
                    tx = parser.parse(body)
                    if tx:
                        inserted = db.insert_transaction(tx)
                        if inserted:
                            parsed += 1
                        break
                except Exception as exc:
                    logger.error("Parser %s failed on uid=%s: %s", type(parser).__name__, uid, exc)
                    continue
    logger.info("Parsed and inserted %d new transactions from emails", parsed)


def ingest_manual_transactions():
    """Load and store manual transactions."""
    txs = load_manual_transactions()
    inserted = 0
    for tx in txs:
        if db.insert_transaction(tx):
            inserted += 1
    logger.info("Inserted %d new manual transactions", inserted)


def main():
    setup_logging(Config.LOG_LEVEL)
    logger.info("Finance tracker starting")

    try:
        Config.validate()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        sys.exit(1)

    db.init_db()
    parse_email_transactions()
    ingest_manual_transactions()
    run_scheduled_reports(
        report_daily=Config.REPORT_DAILY,
        report_weekly=Config.REPORT_WEEKLY,
    )
    logger.info("Finance tracker finished successfully")


if __name__ == "__main__":
    main()
