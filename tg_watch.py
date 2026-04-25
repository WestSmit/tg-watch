import os
import re
import json
import time
import hashlib
import logging
import requests
from typing import Optional, Tuple
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ---------------- Logging ----------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [tgwatch] %(message)s",
)
logger = logging.getLogger("tgwatch")

# ---------------- Config ----------------
API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
STRING_SESSION = os.getenv("TG_STRING_SESSION", "").strip()

HA_WEBHOOK_URL = os.environ["HA_WEBHOOK_URL"]  # http://homeassistant.local:8123/api/webhook/tg_watch

CHANNELS = json.loads(os.getenv("TG_CHANNELS_JSON", "[]"))
KEYWORDS = json.loads(os.getenv("TG_KEYWORDS_JSON", "[]"))
KEYWORDS_REGEX = (os.getenv("TG_KEYWORDS_REGEX", "") or "").strip()

CHANNELS = [c.strip() for c in CHANNELS if c and c.strip()]
KEYWORDS = [k.strip() for k in KEYWORDS if k and k.strip()]

DEDUP_WINDOW_SEC = int(os.getenv("DEDUP_WINDOW_SEC", "300"))
DEDUP_MAX_ENTRIES = int(os.getenv("DEDUP_MAX_ENTRIES", "2000"))

def _normalize_text_for_dedup(text: str) -> str:
    # убираем лишние пробелы/переводы строк, чтобы одинаковые сообщения считались одинаковыми
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _hash_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()

# dedup_cache[key] = last_sent_epoch_seconds
dedup_cache: dict[str, float] = {}

def _dedup_cleanup(now: float) -> None:
    # чистим старые записи
    if not dedup_cache:
        return
    cutoff = now - DEDUP_WINDOW_SEC
    old_keys = [k for k, ts in dedup_cache.items() if ts < cutoff]
    for k in old_keys:
        dedup_cache.pop(k, None)

    # защита от разрастания (на всякий случай)
    if len(dedup_cache) > DEDUP_MAX_ENTRIES:
        # удалим самые старые
        for k, _ts in sorted(dedup_cache.items(), key=lambda kv: kv[1])[: len(dedup_cache) - DEDUP_MAX_ENTRIES]:
            dedup_cache.pop(k, None)

def should_send(dedup_key: str) -> bool:
    now = time.time()
    _dedup_cleanup(now)

    last = dedup_cache.get(dedup_key)
    if last is not None and (now - last) < DEDUP_WINDOW_SEC:
        return False

    dedup_cache[dedup_key] = now
    return True

def post_to_ha(payload: dict):
    try:
        r = requests.post(
            HA_WEBHOOK_URL,
            data=json.dumps(payload, ensure_ascii=False),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if not r.ok:
            body = (r.text or "")[:2000]
            logger.error("Webhook HTTP error: status=%s body=%r", r.status_code, body)
            r.raise_for_status()
        return r
    except requests.RequestException as e:
        # Если это HTTPError, попробуем достать response
        resp = getattr(e, "response", None)
        if resp is not None:
            body = (resp.text or "")[:2000]
            logger.error("Webhook request failed: status=%s body=%r", resp.status_code, body)
        logger.exception("Webhook POST exception: %s", e)
        raise

if not STRING_SESSION:
    raise RuntimeError("TG_STRING_SESSION is empty. Set string_session in the add-on configuration.")

pattern = None
if KEYWORDS_REGEX:
    try:
        pattern = re.compile(KEYWORDS_REGEX, re.IGNORECASE)
    except re.error as e:
        raise RuntimeError(f"Invalid keywords_regex: {e}") from e

if not pattern and not KEYWORDS:
    raise RuntimeError("No keywords configured. Set keywords or keywords_regex in the add-on configuration.")

logger.info(
    "Starting. channels=%d keywords=%d regex=%s webhook=%s log_level=%s dedup_window=%ss",
    len(CHANNELS),
    len(KEYWORDS),
    "on" if pattern else "off",
    HA_WEBHOOK_URL,
    LOG_LEVEL,
    DEDUP_WINDOW_SEC,
)

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

chats_filter = CHANNELS if CHANNELS else None
if chats_filter:
    logger.info("Chat filter enabled for %d channels: %s", len(CHANNELS), ", ".join(CHANNELS))
else:
    logger.warning("No channels configured: listening to ALL chats this account can see.")

def match_text(text: str) -> Tuple[bool, str]:
    """
    Returns: (matched, match_tag)
    match_tag used for dedup + logging.
    """
    if pattern:
        m = pattern.search(text)
        return (m is not None, "regex" if m else "")
    text_l = text.lower()
    for k in KEYWORDS:
        if k.lower() in text_l:
            return (True, f"kw:{k}")
    return (False, "")

@client.on(events.NewMessage(chats=chats_filter))
async def handler(event):
    text = event.raw_text or ""
    if not text:
        logger.debug("Empty message ignored")
        return

    chat = await event.get_chat()
    username = getattr(chat, "username", None)
    title = getattr(chat, "title", None)
    chat_id = getattr(chat, "id", None)
    channel_ref = f"@{username}" if username else (title or str(chat_id) or "unknown")

    logger.debug("New message from %s: %s", channel_ref, text[:200].replace("\n", " "))

    matched, tag = match_text(text)
    if not matched:
        return

    normalized = _normalize_text_for_dedup(text)
    dedup_key = f"{channel_ref}|{tag}|{_hash_text(normalized)}"

    if not should_send(dedup_key):
        logger.info("Dedup hit (%ss). Skipping duplicate match in %s (tag=%s).", DEDUP_WINDOW_SEC, channel_ref, tag)
        return

    link = ""
    if username and getattr(event, "message", None) and getattr(event.message, "id", None):
        link = f"https://t.me/{username}/{event.message.id}"

    payload = {
        "channel": channel_ref,
        "text": text[:1500],
        "link": link,
        "match": tag,
    }

    logger.info("MATCH in %s (tag=%s); sending webhook. link=%s", channel_ref, tag, link or "(no link)")
    resp = post_to_ha(payload)
    logger.info("Webhook sent successfully. status=%s", getattr(resp, "status_code", "?"))

def main():
    logger.info("Connecting to Telegram...")
    client.start()
    logger.info("Connected. Waiting for messages...")
    client.run_until_disconnected()
    logger.warning("Disconnected.")

if __name__ == "__main__":
    main()