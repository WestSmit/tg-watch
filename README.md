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

## Installation

### 1. Add the repository to Home Assistant

[![Add repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https://github.com/WestSmit/ha-apps)

Or manually:

1. In Home Assistant go to **Settings → Apps(Add-ons) → Install app(Add-on Store)**.
2. Click the **⋮** menu (top right) and choose **Repositories**.
3. Add the repository URL:
   ```
   https://github.com/WestSmit/ha-apps
   ```
4. Click **Add**, then close the dialog.
5. Refresh the page — **TG Watch** will appear in the store.
6. Click **Install**.


### 2. Get a Telegram StringSession (one-time, on your PC)

The add-on cannot ask for a phone/code interactively, so you must generate a session string once on your own machine:

```bash
pip install telethon
python - <<'EOF'
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id   = 123456                          # your api_id from my.telegram.org
api_hash = "0123456789abcdef..."           # your api_hash

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print(client.session.save())
EOF
```

Copy the printed string — this is your `string_session`.

### 3. Get Telegram API credentials

1. Go to [https://my.telegram.org](https://my.telegram.org) and log in.
2. Open **API development tools**.
3. Create an application (any name/platform).
4. Copy `api_id` (number) and `api_hash` (hex string).

### 4. Configure the add-on

Open the add-on **Configuration** tab and fill in:

| Field | Description |
|---|---|
| `api_id` | From my.telegram.org |
| `api_hash` | From my.telegram.org |
| `string_session` | Generated in step 2 |
| `channels` | List of channel usernames (without @) |
| `keywords` | Words to match (plain substring match) |
| `match_regex` | Regex to match (overrides keywords if set) |
| `skip_regex` | Regex — messages matching this are ignored |
| `webhook_url` | Your HA webhook URL |
| `ha_event_type` | Optional custom event name (e.g. `tg_watch_event`) |
| `log_level` | `INFO` recommended |

### 5. Start the add-on

Click **Start**. Check the **Log** tab — you should see:

```
Connected. Waiting for messages...
```

## How it works
1. You provide Telegram API credentials and a **StringSession** (one-time login generated on your PC).
2. The add-on connects to Telegram, listens to configured channels, and checks new posts.
3. When a match is found, it sends a JSON payload to your Home Assistant webhook endpoint.

## Payload example
```json
{
  "channel": "@sometgchannel",
  "text": "…matched message text…",
  "link": "https://t.me/sometgchannel/12345",
  "match": "kw:mykeyword"
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

## Simple examples (sample data)

### Add-on options example

```yaml
api_id: 123456
api_hash: 0123456789abcdef0123456789abcdef
string_session: YOUR_STRING_SESSION_HERE
channels:
  - sample_channel_one
  - sample_channel_two
keywords:
  - discount
  - launch
match_regex: '\\b(?:urgent|breaking|announcement)\\b'
skip_regex: '(?i)subscribe|promo|sponsored'
ha_event_type: tg_watch_event
webhook_url: http://homeassistant.local:8123/api/webhook/tg_watch
log_level: INFO
```

### Home Assistant automation (event trigger)

```yaml
alias: TG Watch Notify
description: Sample automation for TG Watch custom event
triggers:
  - trigger: event
    event_type: tg_watch_event
conditions: []
actions:
  - action: persistent_notification.create
    data:
      title: Telegram match
      message: |-
        {{ trigger.event.data.text }}

        {{ trigger.event.data.link }}
mode: parallel
```

### Home Assistant automation (webhook trigger)

```yaml
alias: TG Watch Webhook Notify
description: Sample automation for TG Watch webhook
triggers:
  - trigger: webhook
    webhook_id: tg_watch
    allowed_methods:
      - POST
    local_only: true
conditions: []
actions:
  - action: persistent_notification.create
    data:
      title: Telegram match
      message: |-
        {{ trigger.json.text }}

        {{ trigger.json.link }}
mode: parallel
```
  
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
