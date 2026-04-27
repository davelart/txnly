"""Reporting engine for periodic summaries."""
import logging
from datetime import datetime
from typing import Optional

from db import get_summary
from services.telegram_service import send_message
from utils import period_dates

logger = logging.getLogger(__name__)


def format_summary(summary: dict) -> str:
    lines = [
        f"<b>Finance Summary</b>",
        f"Period: {summary['period']}",
        f"Transactions: {summary['count']}",
        "",
        f"<b>Income:</b> GHS {summary['total_income']:.2f}",
        f"<b>Expenses:</b> GHS {summary['total_expense']:.2f}",
        f"<b>Net Balance:</b> GHS {summary['net_balance']:.2f}",
    ]
    if summary.get("top_spending_categories"):
        lines.append("")
        lines.append("<b>Top Spending:</b>")
        for cat, amt in summary["top_spending_categories"]:
            lines.append(f"  {cat}: GHS {amt:.2f}")
    
    # Add recent transactions
    if summary.get("recent_transactions"):
        lines.append("")
        lines.append("<b>Recent Transactions:</b>")
        for tx in summary["recent_transactions"]:
            tx_type = "📥" if tx["type"] == "credit" else "📤"
            amount = f"GHS {float(tx['amount']):.2f}"
            date_str = tx["date"].strftime("%Y-%m-%d %H:%M") if tx["date"] else "N/A"
            lines.append(f"{tx_type} {amount} - {tx.get('sender', tx.get('recipient', 'Unknown'))} | {date_str}")
    
    return "\n".join(lines)


def generate_report(period: str, start: Optional[datetime] = None, end: Optional[datetime] = None) -> dict:
    if start is None or end is None:
        start, end = period_dates(period)
    summary = get_summary(start, end)
    summary["period_label"] = period
    logger.info("Generated %s report: %s", period, summary)
    return summary


def run_scheduled_reports(report_daily: bool = True, report_weekly: bool = True):
    now = datetime.now()

    if report_daily:
        daily = generate_report("daily")
        text = format_summary(daily)
        send_message(text)

    if report_weekly and now.weekday() == 6:  # Sunday
        weekly = generate_report("weekly")
        text = format_summary(weekly)
        send_message(text)

    if now.day == 1:
        monthly = generate_report("monthly")
        text = format_summary(monthly)
        send_message(text)
