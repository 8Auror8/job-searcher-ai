"""Per-IP rate limiting (in memory; enough for a single instance, see ADR-0004)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
