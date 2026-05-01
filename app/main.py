from app.config import load_config_from_env
from app.dedup import DedupCache
from app.ha_events import HomeAssistantEventClient
from app.logging_setup import configure_logging
from app.matcher import MessageMatcher
from app.service import TelegramWatchService
from app.webhook import WebhookClient


def main() -> None:
    config = load_config_from_env()
    logger = configure_logging(config.log_level)

    matcher = MessageMatcher(
        keywords=config.keywords,
        match_regex=config.match_regex,
        skip_regex=config.skip_regex,
    )
    dedup = DedupCache(config.dedup_window_sec, config.dedup_max_entries)
    webhook = WebhookClient(config.webhook_url, logger)
    ha_event_client = None
    if config.ha_event_type:
        ha_event_client = HomeAssistantEventClient(
            event_type=config.ha_event_type,
            supervisor_token=config.supervisor_token,
            logger=logger,
        )

    logger.info(
        "Starting. channels=%d keywords=%d regex=%s skip_regex=%s ha_event=%s webhook=%s log_level=%s dedup_window=%ss",
        len(config.channels),
        len(config.keywords),
        "on" if matcher.pattern else "off",
        "on" if matcher.skip_pattern else "off",
        config.ha_event_type or "off",
        config.webhook_url,
        config.log_level,
        config.dedup_window_sec,
    )

    service = TelegramWatchService(
        config=config,
        logger=logger,
        matcher=matcher,
        webhook=webhook,
        ha_event_client=ha_event_client,
        dedup=dedup,
    )
    service.run()


if __name__ == "__main__":
    main()
