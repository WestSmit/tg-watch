import hashlib
import re
import time


class DedupCache:
    def __init__(self, window_sec: int, max_entries: int) -> None:
        self.window_sec = window_sec
        self.max_entries = max_entries
        self._cache: dict[str, float] = {}

    @staticmethod
    def normalize_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def hash_text(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()

    def _cleanup(self, now: float) -> None:
        if not self._cache:
            return

        cutoff = now - self.window_sec
        old_keys = [k for k, ts in self._cache.items() if ts < cutoff]
        for key in old_keys:
            self._cache.pop(key, None)

        if len(self._cache) > self.max_entries:
            overflow = len(self._cache) - self.max_entries
            oldest = sorted(self._cache.items(), key=lambda kv: kv[1])[:overflow]
            for key, _ in oldest:
                self._cache.pop(key, None)

    def should_send(self, dedup_key: str) -> bool:
        now = time.time()
        self._cleanup(now)

        last = self._cache.get(dedup_key)
        if last is not None and (now - last) < self.window_sec:
            return False

        self._cache[dedup_key] = now
        return True
