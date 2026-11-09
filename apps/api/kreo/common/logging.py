import contextvars
import json
import logging
import re
from datetime import UTC, datetime

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<![\w.-])(?:\+\d{1,3}|0)\d(?:[ -]?\d){7,13}(?![\w.-])")


def scrub(text: str) -> str:
    """Masque e-mails et numéros de téléphone : aucune donnée personnelle dans les journaux."""
    text = EMAIL_RE.sub("[email]", text)
    return PHONE_RE.sub("[phone]", text)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": scrub(record.getMessage()),
            "request_id": request_id_var.get(),
        }
        if record.exc_info:
            payload["exc"] = scrub(self.formatException(record.exc_info))
        for key in ("event", "target_type", "target_id", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)
