import logging
import re

# The magic link token is a credential, it must not end up in the access log
_GUEST_TOKEN = re.compile(r"(/guest/booking/)[^/\s?\"]+")


def mask_guest_token(text: str) -> str:
    return _GUEST_TOKEN.sub(r"\1***", text)


class MaskGuestTokenFilter(logging.Filter):
    """Masks guest access tokens in log records (e.g. the uvicorn access log)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_guest_token(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                mask_guest_token(a) if isinstance(a, str) else a for a in record.args
            )
        return True
