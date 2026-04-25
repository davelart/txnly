# Finance Tracker

A headless, production-ready personal finance automation system that ingests financial transaction data from email/SMS forwarding, parses and normalizes transactions, stores them in PostgreSQL, and sends automated daily/weekly reports via Telegram.

---

## Features

- **Email Ingestion (IMAP)** — Reads unread emails, filters by subject keywords, extracts plain text, and marks messages as read after processing.
- **SMS via Email Forwarding** — Forwarded SMS alerts (e.g., Ghana MoMo) are treated as normal emails and parsed automatically.
- **Manual Transactions** — Load from `data/manual.json` or `data/manual.csv` and merge without duplication.
- **Modular Parsers** — Pluggable regex-based parsers for MoMo and bank alerts.
- **Deduplication** — SHA-256 hashing prevents duplicate entries across reruns.
- **Auto-Categorization** — Basic rule-based spending categories (Food, Transport, Utilities, Housing, Health, Income, Other).
- **Automated Reporting** — Daily, weekly, and monthly summaries with income, expenses, net balance, and top spending categories.
- **Telegram Notifications** — Clean HTML-formatted reports sent via Telegram Bot API.
- **GitHub Actions Cron** — Scheduled execution with artifact log uploads.
- **Reliable Logging** — INFO/ERROR logging to console and rotating log files.

---

## Project Structure

```
finance-tracker/
├── main.py                     # Entry point
├── config.py                   # Environment-based configuration loader
├── db.py                       # PostgreSQL wrapper (schema, insert, query, dedup)
├── models.py                   # Transaction dataclass with hash + categorization
├── utils.py                    # Logging, date extraction, period helpers
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
├── parsers/
│   ├── base_parser.py          # Abstract parser interface
│   ├── momo_parser.py          # Ghana MoMo regex patterns
│   └── bank_parser.py          # Generic bank debit/credit patterns
├── services/
│   ├── email_service.py        # IMAP unread fetch + plain-text extraction
│   ├── telegram_service.py     # Telegram Bot API sender
│   └── reporting_service.py   # Summary generation + scheduled dispatch
├── data/
│   ├── manual.json             # Sample manual transactions
│   └── manual.csv              # Sample manual transactions (CSV format)
├── tests/
│   └── test_parsers.py         # pytest unit tests for parsers
├── .github/
│   └── workflows/
│       └── cron.yml            # GitHub Actions daily + weekly cron
└── logs/
    └── finance_tracker.log     # Auto-created application logs
```

---

## Setup

### 1. Clone / Copy the Project

```bash
cd finance-tracker
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
# Email / IMAP
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_CHAT_ID=12345678

# Optional
LOG_LEVEL=INFO
SUBJECT_KEYWORDS=MoMo,Debit Alert,Credit Alert
```

> **Gmail users:** Use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

### 5. Add Manual Transactions (Optional)

Edit `data/manual.json` or create `data/manual.csv`. The script loads both on each run and deduplicates by hash.

### 6. Run Locally

```bash
python main.py
```

---

## GitHub Actions Deployment

1. Push the repo to GitHub.
2. Go to **Settings > Secrets and variables > Actions**.
3. Add repository secrets for:
   - `IMAP_SERVER`
   - `IMAP_PORT`
   - `EMAIL_ADDRESS`
   - `EMAIL_PASSWORD`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `LOG_LEVEL` (optional)
   - `REPORT_DAILY` / `REPORT_WEEKLY` (optional)
   - `SUBJECT_KEYWORDS` (optional)
   - `DATABASE_URL` (required; e.g. `postgresql://user:pass@localhost:5432/finance`)

The workflow in `.github/workflows/cron.yml` runs:
- **Daily** at `07:00 UTC`
- **Weekly** on **Sunday** at `08:00 UTC`

Logs are uploaded as artifacts on every run.

---

## Parser Coverage

### MoMo (Ghana)

Handles patterns such as:
- `You have received GHS 100.00 from ...`
- `You have sent GHS 50.00 to ...`
- `You have bought airtime worth GHS 10.00 ...`
- `You have deposited GHS 200.00 ...`
- `You have cashed out GHS 150.00 at ...`

### Bank

Handles generic debit/credit alerts containing keywords like:
- `debit alert`, `credit alert`, `GHS`, bank names, etc.

---

## Running Tests

```bash
pytest tests/test_parsers.py -v
```

---

## Idempotency & Safety

- The script is safe to rerun: duplicate transactions are skipped via `hash_id` unique constraint.
- Emails are marked `SEEN` after processing so they are not re-ingested.
- Single failures (malformed emails, bad rows) are logged and skipped without crashing the entire run.

---

## Extending

### Add a New Parser

1. Create `parsers/my_parser.py` inheriting from `BaseParser`.
2. Implement `can_parse(self, text: str) -> bool` and `parse(self, text, source) -> Transaction`.
3. Register it in `main.py`:
   ```python
   PARSERS = [MoMoParser(), BankParser(), MyParser()]
   ```

### Add New Categories

Edit `Transaction._auto_categorize()` in `models.py`.

---

## License

MIT
