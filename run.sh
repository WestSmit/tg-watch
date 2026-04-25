#!/bin/sh
set -e

CONFIG_PATH=/data/options.json

API_ID=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'"))["api_id"])')
API_HASH=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'"))["api_hash"])')
SESSION_NAME=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'"))["session_name"])')
WEBHOOK_URL=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'"))["webhook_url"])')
STRING_SESSION=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'")).get("string_session",""))')
KEYWORDS_JSON=$(python -c 'import json; print(json.dumps(json.load(open("'"$CONFIG_PATH"'")).get("keywords", []), ensure_ascii=False))')
CHANNELS_JSON=$(python -c 'import json; print(json.dumps(json.load(open("'"$CONFIG_PATH"'")).get("channels", []), ensure_ascii=False))')
KEYWORDS_REGEX=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'")).get("keywords_regex",""))')
LOG_LEVEL=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'")).get("log_level",""))')

export TG_STRING_SESSION="$STRING_SESSION"
export TG_API_ID="$API_ID"
export TG_API_HASH="$API_HASH"
export TG_SESSION="$SESSION_NAME"
export HA_WEBHOOK_URL="$WEBHOOK_URL"
export TG_KEYWORDS_JSON="$KEYWORDS_JSON"
export TG_CHANNELS_JSON="$CHANNELS_JSON"
export TG_KEYWORDS_REGEX="$KEYWORDS_REGEX"
export LOG_LEVEL="$LOG_LEVEL"

# Session file will be stored in /config/tgwatch via mapped config
mkdir -p /config/tgwatch
cd /config/tgwatch

# first run will ask for phone/code in addon logs (not удобнейший UX, но работает)
python /app/tg_watch.py