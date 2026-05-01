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
MATCH_REGEX=$(python -c 'import json; c=json.load(open("'"$CONFIG_PATH"'")); print(c.get("match_regex", c.get("keywords_regex", "")))')
SKIP_REGEX=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'")).get("skip_regex",""))')
HA_EVENT_TYPE=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'")).get("ha_event_type",""))')
LOG_LEVEL=$(python -c 'import json; print(json.load(open("'"$CONFIG_PATH"'")).get("log_level",""))')

export TG_STRING_SESSION="$STRING_SESSION"
export TG_API_ID="$API_ID"
export TG_API_HASH="$API_HASH"
export TG_SESSION="$SESSION_NAME"
export HA_WEBHOOK_URL="$WEBHOOK_URL"
export TG_KEYWORDS_JSON="$KEYWORDS_JSON"
export TG_CHANNELS_JSON="$CHANNELS_JSON"
export TG_MATCH_REGEX="$MATCH_REGEX"
export TG_SKIP_REGEX="$SKIP_REGEX"
export TG_HA_EVENT_TYPE="$HA_EVENT_TYPE"
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN:-}"
export LOG_LEVEL="$LOG_LEVEL"
export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"

# Session file will be stored in /config/tgwatch via mapped config
mkdir -p /config/tgwatch
cd /config/tgwatch

python -m app.main