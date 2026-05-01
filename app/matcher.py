import re
from typing import Tuple


class MessageMatcher:
    def __init__(self, keywords: list[str], match_regex: str, skip_regex: str) -> None:
        self.keywords = keywords
        self.pattern = self._compile_pattern(match_regex, "match_regex")
        self.skip_pattern = self._compile_pattern(skip_regex, "skip_regex")

        if not self.pattern and not self.keywords:
            raise RuntimeError("No keywords configured. Set keywords or match_regex in the add-on configuration.")

    @staticmethod
    def _compile_pattern(pattern_value: str, field_name: str):
        if not pattern_value:
            return None
        try:
            return re.compile(pattern_value, re.IGNORECASE)
        except re.error as exc:
            raise RuntimeError(f"Invalid {field_name}: {exc}") from exc

    def should_skip(self, text: str) -> bool:
        return bool(self.skip_pattern and self.skip_pattern.search(text))

    def match_text(self, text: str) -> Tuple[bool, str]:
        # Keep legacy behavior: regex mode has precedence over keyword mode.
        if self.pattern:
            matched = bool(self.pattern.search(text))
            return (matched, "regex" if matched else "")

        text_l = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text_l:
                return (True, f"kw:{keyword}")

        return (False, "")
