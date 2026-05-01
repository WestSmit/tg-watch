# TG Watch — Home Assistant Add-on

**TG Watch** is a lightweight Home Assistant add-on that monitors selected Telegram channels and triggers a Home Assistant webhook when a message matches your keywords (or a regex rule).

It is designed for “always-on” monitoring with simple configuration from the add-on UI and includes:
- **Telegram channel monitoring** via [Telethon](https://github.com/LonamiWebs/Telethon)
- **Keyword matching** (substring list) *or* **regex matching**
- **Optional skip regex** to ignore noisy messages before matching
- **Webhook delivery** to Home Assistant (payload includes channel, text, link, and match tag)
- **Optional Home Assistant custom event firing** for matched messages
- **Anti-spam / rate limiting** (deduplicates repeated matches within a configurable time window)
- **Detailed logging**, including **HTTP status + response body** when the webhook fails

## How it works
1. You provide Telegram API credentials and a **StringSession** (one-time login generated on your PC).
2. The add-on connects to Telegram, listens to configured channels, and checks new posts.
3. When a match is found, it sends a JSON payload to your Home Assistant webhook endpoint.

## Payload example
```json
{
  "channel": "@controlpoltava",
  "text": "…matched message text…",
  "link": "https://t.me/controlpoltava/12345",
  "match": "kw:мирго��од"
}
```

## Configuration (high level)
Configure in the add-on UI:

- `api_id`, `api_hash`
- `string_session` (Telethon StringSession)
- `channels` (list of channel usernames/links)
- `keywords` (list of words/phrases) or `match_regex` (single regex)
- `skip_regex` (optional regex; if matched, message is ignored)
- `ha_event_type` (optional; fire a HA event with this event type for each match)
- `webhook_url`
- optional rate limit settings (e.g. `DEDUP_WINDOW_SEC`)
  
## Notes

This add-on does not support interactive login inside the add-on container (Home Assistant add-ons run without an interactive TTY). Use StringSession.
If webhook delivery fails, logs will include HTTP status and response body (truncated) to simplify troubleshooting.
If `ha_event_type` is set, the add-on also fires events to Home Assistant via the Supervisor API endpoint `/api/events/<event_type>`.

## Disclaimer
This project is not affiliated with Telegram or Home Assistant. Use at your own risk and follow Telegram’s terms of service.

## Project structure

The add-on is split into small modules under `app/`:

- `app/config.py` - environment loading and validation
- `app/logging_setup.py` - logger setup
- `app/matcher.py` - keyword/regex/skip matching rules
- `app/dedup.py` - anti-spam dedup cache
- `app/webhook.py` - webhook HTTP client
- `app/ha_events.py` - Home Assistant custom events client
- `app/service.py` - Telegram event handling and runtime flow
- `app/main.py` - composition root and startup

`tg_watch.py` is kept as a compatibility wrapper entrypoint.
