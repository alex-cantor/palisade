import secrets
import threading
import time

TOKEN_LIFETIME = 60  # seconds

_lock = threading.Lock()
_store: dict[str, dict] = {}


def create_token(vm_pk: int) -> str:
    token = secrets.token_urlsafe(32)
    with _lock:
        # Prune expired entries
        now = time.time()
        expired = [k for k, v in _store.items() if v["expires"] < now]
        for k in expired:
            del _store[k]
        _store[token] = {"vm_pk": vm_pk, "expires": now + TOKEN_LIFETIME}
    return token


def consume_token(token: str) -> int | None:
    """Return vm_pk and remove the token, or None if invalid/expired."""
    with _lock:
        entry = _store.pop(token, None)
    if entry and entry["expires"] > time.time():
        return entry["vm_pk"]
    return None
