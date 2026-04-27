"""SMS ingestion service using SMS gateway APIs."""
import logging
from typing import List, Tuple, Optional

from config import Config

logger = logging.getLogger(__name__)


def fetch_sms_from_twilio() -> List[Tuple[str, str]]:
    """Fetch SMS messages from Twilio API.
    
    Requires TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in config.
    Returns list of (message_id, body) tuples.
    """
    try:
        from twilio.rest import Client
    except ImportError:
        logger.warning("Twilio library not installed. Install with: pip install twilio")
        return []

    account_sid = getattr(Config, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(Config, 'TWILIO_AUTH_TOKEN', None)
    phone_number = getattr(Config, 'TWILIO_PHONE_NUMBER', None)

    if not account_sid or not auth_token:
        logger.warning("Twilio credentials not configured")
        return []

    results: List[Tuple[str, str]] = []
    try:
        client = Client(account_sid, auth_token)
        
        # Fetch recent SMS messages
        messages = client.messages.list(
            to=phone_number,
            limit=50
        )
        
        for msg in messages:
            if msg.direction == 'inbound' and msg.body:
                results.append((msg.sid, msg.body))
        
        logger.info("Fetched %d SMS messages from Twilio", len(results))
    except Exception as exc:
        logger.error("Failed to fetch SMS from Twilio: %s", exc)
    
    return results


def fetch_sms_from_file(file_path: str) -> List[Tuple[str, str]]:
    """Fetch SMS messages from a text file (one per line).
    
    Format: Each line should contain the SMS body text.
    Returns list of (line_number, body) tuples.
    """
    from pathlib import Path
    
    path = Path(file_path)
    if not path.exists():
        logger.warning("SMS file not found: %s", file_path)
        return []
    
    results: List[Tuple[str, str]] = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    results.append((str(line_num), line))
        logger.info("Loaded %d SMS messages from file: %s", len(results), file_path)
    except Exception as exc:
        logger.error("Failed to read SMS file: %s", exc)
    
    return results


def fetch_sms(source: str = 'twilio') -> List[Tuple[str, str]]:
    """Fetch SMS messages from specified source.
    
    Args:
        source: 'twilio' for Twilio API, 'file' for file-based import
    
    Returns:
        List of (message_id, body) tuples
    """
    if source == 'twilio':
        return fetch_sms_from_twilio()
    elif source == 'file':
        file_path = getattr(Config, 'SMS_FILE_PATH', 'data/sms.txt')
        return fetch_sms_from_file(file_path)
    else:
        logger.warning("Unknown SMS source: %s", source)
        return []
