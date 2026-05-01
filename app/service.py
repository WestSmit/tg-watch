import logging

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from app.config import AppConfig
from app.dedup import DedupCache
from app.ha_events import HomeAssistantEventClient
from app.matcher import MessageMatcher
from app.webhook import WebhookClient


class TelegramWatchService:
    def __init__(
        self,
        config: AppConfig,
        logger: logging.Logger,
        matcher: MessageMatcher,
        webhook: WebhookClient,
        ha_event_client: HomeAssistantEventClient | None,
        dedup: DedupCache,
    ) -> None:
        self.config = config
        self.logger = logger
        self.matcher = matcher
        self.webhook = webhook
        self.ha_event_client = ha_event_client
        self.dedup = dedup

        self.client = TelegramClient(
            StringSession(self.config.string_session),
            self.config.api_id,
            self.config.api_hash,
        )
        self.chats_filter = self.config.channels if self.config.channels else None

    def register_handlers(self) -> None:
        @self.client.on(events.NewMessage(chats=self.chats_filter))
        async def _handler(event):
            text = event.raw_text or ""
            if not text:
                self.logger.debug("Empty message ignored")
                return

            if self.matcher.should_skip(text):
                self.logger.debug("Message skipped by skip_regex")
                return

            chat = await event.get_chat()
            username = getattr(chat, "username", None)
            title = getattr(chat, "title", None)
            chat_id = getattr(chat, "id", None)
            channel_ref = f"@{username}" if username else (title or str(chat_id) or "unknown")

            self.logger.debug("New message from %s: %s", channel_ref, text[:200].replace("\n", " "))

            matched, tag = self.matcher.match_text(text)
            if not matched:
                return

            normalized = self.dedup.normalize_text(text)
            dedup_key = f"{channel_ref}|{tag}|{self.dedup.hash_text(normalized)}"

            if not self.dedup.should_send(dedup_key):
                self.logger.info(
                    "Dedup hit (%ss). Skipping duplicate match in %s (tag=%s).",
                    self.config.dedup_window_sec,
                    channel_ref,
                    tag,
                )
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

            self.logger.info("MATCH in %s (tag=%s); sending webhook. link=%s", channel_ref, tag, link or "(no link)")
            response = self.webhook.post(payload)
            self.logger.info("Webhook sent successfully. status=%s", getattr(response, "status_code", "?"))

            if self.ha_event_client and self.ha_event_client.enabled():
                event_data = dict(payload)
                event_data["source"] = "tgwatch"
                event_data["chat_id"] = chat_id
                event_response = self.ha_event_client.post(event_data)
                self.logger.info(
                    "HA event fired successfully. event=%s status=%s",
                    self.ha_event_client.event_type,
                    getattr(event_response, "status_code", "?"),
                )

    def run(self) -> None:
        if self.chats_filter:
            self.logger.info(
                "Chat filter enabled for %d channels: %s",
                len(self.config.channels),
                ", ".join(self.config.channels),
            )
        else:
            self.logger.warning("No channels configured: listening to ALL chats this account can see.")

        self.register_handlers()
        self.logger.info("Connecting to Telegram...")
        self.client.start()
        self.logger.info("Connected. Waiting for messages...")
        self.client.run_until_disconnected()
        self.logger.warning("Disconnected.")
