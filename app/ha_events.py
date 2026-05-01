import json
import logging

import requests


class HomeAssistantEventClient:
    def __init__(self, event_type: str, supervisor_token: str, logger: logging.Logger) -> None:
        self.event_type = event_type
        self.supervisor_token = supervisor_token
        self.logger = logger

    def enabled(self) -> bool:
        return bool(self.event_type)

    def post(self, event_data: dict) -> requests.Response:
        if not self.enabled():
            raise RuntimeError("Event client is disabled")

        url = f"http://supervisor/core/api/events/{self.event_type}"
        headers = {
            "Authorization": f"Bearer {self.supervisor_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url,
                data=json.dumps(event_data, ensure_ascii=False),
                headers=headers,
                timeout=10,
            )
            if not response.ok:
                body = (response.text or "")[:2000]
                self.logger.error(
                    "HA event HTTP error: event=%s status=%s body=%r",
                    self.event_type,
                    response.status_code,
                    body,
                )
                response.raise_for_status()
            return response
        except requests.RequestException as exc:
            resp = getattr(exc, "response", None)
            if resp is not None:
                body = (resp.text or "")[:2000]
                self.logger.error(
                    "HA event request failed: event=%s status=%s body=%r",
                    self.event_type,
                    resp.status_code,
                    body,
                )
            self.logger.exception("HA event POST exception: %s", exc)
            raise
