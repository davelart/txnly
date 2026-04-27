"""PostgreSQL database wrapper with deduplication."""
import logging
from datetime import datetime
from typing import List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Config
from models import Transaction

logger = logging.getLogger(__name__)


def _get_connection():
    return psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    hash_id VARCHAR(64) UNIQUE NOT NULL,
                    amount NUMERIC(12, 2) NOT NULL,
                    type VARCHAR(10) NOT NULL,
                    source VARCHAR(20) NOT NULL,
                    sender VARCHAR(100),
                    recipient VARCHAR(100),
                    category VARCHAR(50),
                    reference VARCHAR(100),
                    date TIMESTAMP,
                    raw_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_tx_hash ON transactions(hash_id)"
            )
        conn.commit()
        logger.info("Database initialized")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc)
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_transaction(tx: Transaction) -> bool:
    """Insert a transaction if its hash does not already exist. Returns True if inserted."""
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (hash_id, amount, type, source, sender, recipient, category, reference, date, raw_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hash_id) DO NOTHING
                RETURNING id
                """,
                (
                    tx.hash_id,
                    tx.amount,
                    tx.type,
                    tx.source,
                    tx.sender,
                    tx.recipient,
                    tx.category,
                    tx.reference,
                    tx.date,
                    tx.raw_text,
                ),
            )
            row = cur.fetchone()
        conn.commit()
        if row:
            logger.info("Inserted transaction hash=%s amount=%.2f", tx.hash_id[:8], tx.amount)
            return True
        logger.debug("Duplicate transaction skipped hash=%s", tx.hash_id[:8])
        return False
    except Exception as exc:
        logger.error("Failed to insert transaction: %s", exc)
        conn.rollback()
        return False
    finally:
        conn.close()


def fetch_transactions(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    source: Optional[str] = None,
) -> List[dict]:
    conn = _get_connection()
    try:
        query = "SELECT * FROM transactions WHERE 1=1"
        params: List = []
        if start:
            query += " AND date >= %s"
            params.append(start)
        if end:
            query += " AND date <= %s"
            params.append(end)
        if source:
            query += " AND source = %s"
            params.append(source)
        query += " ORDER BY date DESC"
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        return rows
    except Exception as exc:
        logger.error("Failed to fetch transactions: %s", exc)
        return []
    finally:
        conn.close()


def get_summary(start: Optional[datetime] = None, end: Optional[datetime] = None) -> dict:
    rows = fetch_transactions(start, end)
    total_income = sum(float(r["amount"]) for r in rows if r["type"] == "credit")
    total_expense = sum(float(r["amount"]) for r in rows if r["type"] == "debit")
    net = total_income - total_expense
    categories: dict = {}
    for r in rows:
        if r["type"] == "debit" and r["category"]:
            categories[r["category"]] = categories.get(r["category"], 0.0) + float(r["amount"])
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Include recent transactions (last 10)
    recent_transactions = rows[:10] if len(rows) > 10 else rows
    
    return {
        "period": f"{start.date() if start else 'all'} to {end.date() if end else 'all'}",
        "count": len(rows),
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_balance": round(net, 2),
        "top_spending_categories": top_categories,
        "recent_transactions": recent_transactions,
    }
