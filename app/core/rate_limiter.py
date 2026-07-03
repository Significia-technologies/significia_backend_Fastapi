import logging

import redis
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger("app.rate_limiter")


def _resolve_storage_uri() -> str:
    """
    Prefer Redis (required for correct multi-process rate limiting in
    production), but fall back to in-memory storage if Redis isn't reachable
    (e.g. local dev without Docker) so auth endpoints don't hard-fail.
    """
    try:
        client = redis.from_url(settings.RATE_LIMIT_REDIS_URL, socket_connect_timeout=1)
        client.ping()
        return settings.RATE_LIMIT_REDIS_URL
    except Exception as e:
        logger.warning(
            f"Rate limiter could not reach Redis ({e}); falling back to in-memory "
            "storage. This is fine for local dev but must not happen in production "
            "(limits won't be shared across worker processes)."
        )
        return "memory://"


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_resolve_storage_uri(),
    default_limits=["200/minute"],
)
