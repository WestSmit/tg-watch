import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    api_id: int
    api_hash: str
    string_session: str
    webhook_url: str
    channels: list[str]
    keywords: list[str]
    match_regex: str
    skip_regex: str
    ha_event_type: str
    supervisor_token: str
    log_level: str
    dedup_window_sec: int
    dedup_max_entries: int


def _parse_json_list(env_name: str) -> list[str]:
    raw = os.getenv(env_name, "[]")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {env_name}: {exc}") from exc

    if not isinstance(parsed, list):
        raise RuntimeError(f"{env_name} must be a JSON array")

    return [str(item).strip() for item in parsed if str(item).strip()]


def load_config_from_env() -> AppConfig:
    api_id_raw = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH", "").strip()
    string_session = os.getenv("TG_STRING_SESSION", "").strip()
    webhook_url = os.getenv("HA_WEBHOOK_URL", "").strip()

    if not api_id_raw:
        raise RuntimeError("TG_API_ID is required")
    if not api_hash:
        raise RuntimeError("TG_API_HASH is required")
    if not string_session:
        raise RuntimeError("TG_STRING_SESSION is empty. Set string_session in the add-on configuration.")

    try:
        api_id = int(api_id_raw)
    except ValueError as exc:
        raise RuntimeError("TG_API_ID must be an integer") from exc

    keywords = _parse_json_list("TG_KEYWORDS_JSON")
    channels = _parse_json_list("TG_CHANNELS_JSON")

    match_regex = (os.getenv("TG_MATCH_REGEX", "") or "").strip()
    skip_regex = (os.getenv("TG_SKIP_REGEX", "") or "").strip()
    ha_event_type = (os.getenv("TG_HA_EVENT_TYPE", "") or "").strip()
    supervisor_token = (os.getenv("SUPERVISOR_TOKEN", "") or "").strip()
    log_level = (os.getenv("LOG_LEVEL", "INFO") or "INFO").upper().strip()

    if ha_event_type and not supervisor_token:
        raise RuntimeError(
            "SUPERVISOR_TOKEN is not available. Ensure homeassistant_api is enabled for the add-on."
        )

    try:
        dedup_window_sec = int(os.getenv("DEDUP_WINDOW_SEC", "300"))
        dedup_max_entries = int(os.getenv("DEDUP_MAX_ENTRIES", "2000"))
    except ValueError as exc:
        raise RuntimeError("DEDUP_WINDOW_SEC and DEDUP_MAX_ENTRIES must be integers") from exc

    return AppConfig(
        api_id=api_id,
        api_hash=api_hash,
        string_session=string_session,
        webhook_url=webhook_url,
        channels=channels,
        keywords=keywords,
        match_regex=match_regex,
        skip_regex=skip_regex,
        ha_event_type=ha_event_type,
        supervisor_token=supervisor_token,
        log_level=log_level,
        dedup_window_sec=dedup_window_sec,
        dedup_max_entries=dedup_max_entries,
    )
