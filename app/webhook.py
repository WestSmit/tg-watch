import json
import logging

import requests


class WebhookClient:
    def __init__(self, webhook_url: str, logger: logging.Logger) -> None:
        self.webhook_url = webhook_url
        self.logger = logger

    def post(self, payload: dict) -> requests.Response:
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload, ensure_ascii=False),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if not response.ok:
                body = (response.text or "")[:2000]
                self.logger.error("Webhook HTTP error: status=%s body=%r", response.status_code, body)
                response.raise_for_status()
            return response
        except requests.RequestException as exc:
            resp = getattr(exc, "response", None)
            if resp is not None:
                body = (resp.text or "")[:2000]
                self.logger.error("Webhook request failed: status=%s body=%r", resp.status_code, body)
            self.logger.exception("Webhook POST exception: %s", exc)
            raise
