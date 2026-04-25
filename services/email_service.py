"""IMAP email ingestion service."""
import email
import imaplib
import logging
from typing import List, Tuple

from config import Config

logger = logging.getLogger(__name__)


def _decode_payload(part) -> str:
    charset = part.get_content_charset() or "utf-8"
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    try:
        return payload.decode(charset, errors="replace")
    except Exception:
        return payload.decode("utf-8", errors="replace")


def _extract_plain_text(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                return _decode_payload(part)
        # Fallback to first text part
        for part in msg.walk():
            if part.get_content_type().startswith("text/"):
                return _decode_payload(part)
    else:
        if msg.get_content_type().startswith("text/"):
            return _decode_payload(msg)
    return ""


def fetch_unread_emails(
    keywords: List[str] = None,
) -> List[Tuple[str, str, str]]:
    """Fetch unread emails matching subject keywords. Returns list of (uid, subject, body)."""
    if keywords is None:
        keywords = Config.SUBJECT_KEYWORDS

    results: List[Tuple[str, str, str]] = []
    try:
        mail = imaplib.IMAP4_SSL(Config.IMAP_SERVER, Config.IMAP_PORT)
        mail.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
        mail.select("inbox")
    except Exception as exc:
        logger.error("IMAP connection/login failed: %s", exc)
        return results

    try:
        status, data = mail.search(None, "UNSEEN")
        if status != "OK" or not data[0]:
            logger.info("No unread emails found")
            mail.logout()
            return results

        uids = data[0].split()
        logger.info("Found %d unread emails", len(uids))

        for uid in uids:
            try:
                status, msg_data = mail.fetch(uid, "(RFC822)")
                if status != "OK":
                    continue
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                subject = msg.get("Subject", "")
                from_addr = msg.get("From", "")

                # Simple keyword filter on subject
                if keywords and not any(kw.lower() in subject.lower() for kw in keywords):
                    logger.debug("Skipping email uid=%s subject='%s' (no keyword match)", uid.decode(), subject)
                    continue

                body = _extract_plain_text(msg)
                if not body.strip():
                    logger.debug("Empty body for uid=%s", uid.decode())
                    continue

                results.append((uid.decode(), subject, body))

                # Mark as read so it is not reprocessed
                mail.store(uid, "+FLAGS", "\\Seen")
                logger.info("Processed email uid=%s subject='%s'", uid.decode(), subject)
            except Exception as exc:
                logger.error("Error processing email uid=%s: %s", uid.decode() if isinstance(uid, bytes) else uid, exc)
                continue
    except Exception as exc:
        logger.error("IMAP fetch error: %s", exc)
    finally:
        try:
            mail.close()
            mail.logout()
        except Exception:
            pass

    return results
