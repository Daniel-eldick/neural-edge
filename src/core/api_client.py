"""Shared HTTP client for sensory modules.

Centralised HTTP wrapper with a TTL cache and a per-provider token-bucket
rate limiter. All sensory modules MUST route through this client so we
can reason about the bot's external traffic in one place.

Design decisions (resolved during Phase 2 Task 1 planning):

1. **Single entry point**: :meth:`APIClient.get` — keyword-only
   arguments mirror how ``requests.get`` feels, with no surprise kwargs.
   All four sensory modules call the same method.

2. **Raise on rate limit, don't sleep**: hitting the bucket ceiling
   raises :class:`RateLimitError` instead of blocking. A sleeping
   client stalls the trading loop during a burst, and an invisible
   multi-second sleep is the kind of "silent degradation" the Fail
   Loudly mandate exists to prevent. Callers catch the typed exception
   and decide — return an empty signal list, skip this candle, log
   and retry later.

3. **Re-raise HTTP errors**: the client calls ``raise_for_status()``
   and lets ``requests.RequestException`` propagate. Sensory modules
   catch at *their* layer and return empty signal lists — the
   "swallowing" is a sensory-layer policy, not a transport-layer one.

   Matching raise-first philosophy, the rate-limit exception is named
   :class:`RateLimitError` (not ``RateLimitExceeded``) to satisfy
   ``ruff N818`` and match the Python ecosystem convention
   (``HTTPError``, ``RateLimitError`` in openai, etc.).

4. **Injected clock**: tests pass a fake monotonic clock so TTL and
   rate-limit windows advance deterministically, no real sleeps.

5. **Thread-safe state, lock released across I/O**: cache lookups
   and token-bucket accounting run under a single lock. The HTTP call
   itself happens *outside* the lock so one slow request cannot stall
   concurrent callers. Two concurrent identical requests may both hit
   the wire in a race — that is acceptable (the cache is an
   optimisation, not a correctness contract).

Known limitations (tracked in ``docs/TECHNICAL_DEBT.md``):

- **LOW-01**: the cache is unbounded and never physically evicts
  expired entries. Safe at current scale; revisit before multi-week
  paper-trading runs or a 10x provider expansion.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

logger = logging.getLogger(__name__)

# JSON payloads are genuinely untyped at the wire layer. We annotate as
# ``Any`` at the boundary and let the sensory-layer parsers impose
# shape on their side. This is the honest type.
JSONPayload = Any

# Per-provider rate-limit budgets: ``(max_calls, window_seconds)``.
# These are the *hard* vendor limits. Callers should keep their own
# headroom rather than rely on margin here.
#
# CryptoQuant free-tier limits vary by plan; 10/min is a conservative
# default that must be overridden if we upgrade.
RATE_LIMITS: Mapping[str, tuple[int, float]] = {
    "coingecko": (30, 60.0),
    "alpaca": (200, 60.0),
    "cryptoquant": (10, 60.0),
}

DEFAULT_TIMEOUT = 10.0  # seconds — per-request HTTP timeout

# Identifies the bot in vendor access logs so rate-limit investigations
# can attribute traffic back to us. Callers may override per-request
# via the ``headers`` kwarg (e.g. an operator running a debug build).
DEFAULT_USER_AGENT = "neural-edge/0.1"


class APIClientError(Exception):
    """Base class for api_client errors other than transport failures.

    Transport failures (connection errors, timeouts, HTTP status >= 400)
    propagate as ``requests.RequestException`` — callers catch that
    separately so the client stays a thin wrapper over ``requests``.
    """


class RateLimitError(APIClientError):
    """Raised when the per-provider token bucket is empty.

    Callers should catch this at the sensory-module layer and degrade
    gracefully (return empty signal list, log at WARNING, optionally
    reschedule). Never catch it at ``src/core/`` level — the bucket
    ceiling is a real signal that the bot is over-calling a provider,
    and swallowing it hides the bug.
    """

    def __init__(self, provider: str, retry_after: float) -> None:
        super().__init__(
            f"Rate limit exceeded for provider '{provider}'. "
            f"Retry after ~{retry_after:.1f}s."
        )
        self.provider = provider
        self.retry_after = retry_after


@dataclass
class _CacheEntry:
    payload: JSONPayload
    expires_at: float


@dataclass
class _TokenBucket:
    """Sliding-window token bucket.

    Stores the timestamp of every consumed token in a deque. Each
    ``try_consume`` call evicts expired timestamps and either appends
    a new one (success) or returns the retry-after delay (failure).
    """

    max_calls: int
    window_seconds: float
    timestamps: deque[float] = field(default_factory=deque)

    def try_consume(self, now: float) -> float | None:
        """Attempt to consume a token at time ``now``.

        Returns:
            ``None`` on success (token consumed), or the number of
            seconds the caller must wait before the oldest timestamp
            rolls out of the window.
        """
        cutoff = now - self.window_seconds
        while self.timestamps and self.timestamps[0] <= cutoff:
            self.timestamps.popleft()

        if len(self.timestamps) >= self.max_calls:
            oldest = self.timestamps[0]
            retry_after = (oldest + self.window_seconds) - now
            return max(retry_after, 0.0)

        self.timestamps.append(now)
        return None


class APIClient:
    """HTTP client with TTL cache and per-provider rate limiting.

    All sensory modules must share a single instance per process so the
    cache and rate-limit state are global. Construct it once at startup
    (typically in the strategy's ``__init__``) and inject into each
    sensory module.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        session: requests.Session | None = None,
        rate_limits: Mapping[str, tuple[int, float]] = RATE_LIMITS,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._clock = clock
        self._session = session or requests.Session()
        self._timeout = timeout
        self._lock = threading.Lock()
        self._cache: dict[
            tuple[str, str, tuple[tuple[str, str], ...]], _CacheEntry
        ] = {}
        self._buckets: dict[str, _TokenBucket] = {
            provider: _TokenBucket(max_calls=max_calls, window_seconds=window)
            for provider, (max_calls, window) in rate_limits.items()
        }

    def get(
        self,
        *,
        provider: str,
        url: str,
        params: Mapping[str, Any] | None = None,
        ttl_seconds: int = 60,
        headers: Mapping[str, str] | None = None,
    ) -> JSONPayload:
        """Perform a cached, rate-limited GET request.

        Args:
            provider: One of the keys in :data:`RATE_LIMITS`. Used to
                pick the right token bucket.
            url: Absolute HTTP(S) URL.
            params: Query-string parameters. The cache key is
                order-independent — ``{"a": 1, "b": 2}`` and
                ``{"b": 2, "a": 1}`` hit the same cache row.
            ttl_seconds: Cache lifetime in seconds. Pass ``0`` to
                bypass the cache entirely (useful for endpoints whose
                freshness matters more than the vendor bill).
            headers: Optional per-request headers (e.g. ``Authorization``).
                Merged over a default ``User-Agent: neural-edge/0.1`` so
                vendor access logs can attribute traffic back to us;
                pass a ``User-Agent`` key to override. Not part of the
                cache key — do not use headers to disambiguate
                otherwise-identical requests.

        Returns:
            Parsed JSON payload as returned by ``response.json()``.

        Raises:
            APIClientError: ``provider`` is not a known key.
            RateLimitError: the provider's bucket is empty.
            requests.RequestException: any transport-layer failure
                (connection error, timeout, HTTP status >= 400).
        """
        if provider not in self._buckets:
            known = sorted(self._buckets)
            msg = f"Unknown provider '{provider}'. Known: {known}"
            raise APIClientError(msg)

        cache_key = self._cache_key(provider, url, params)
        now = self._clock()

        with self._lock:
            if ttl_seconds > 0:
                entry = self._cache.get(cache_key)
                if entry is not None and entry.expires_at > now:
                    logger.debug(
                        "api_client cache hit: provider=%s url=%s", provider, url
                    )
                    return entry.payload

            bucket = self._buckets[provider]
            retry_after = bucket.try_consume(now)
            if retry_after is not None:
                logger.warning(
                    "api_client rate limit hit: provider=%s retry_after=%.1fs",
                    provider,
                    retry_after,
                )
                raise RateLimitError(provider, retry_after)

        # HTTP I/O happens outside the lock — one slow request must not
        # stall concurrent callers. The trade-off is a small race where
        # two concurrent identical requests both hit the wire; the cache
        # is an optimisation, not a single-flight guarantee.
        merged_headers: dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
        if headers:
            merged_headers.update(headers)

        logger.debug("api_client HTTP GET: provider=%s url=%s", provider, url)
        response = self._session.get(
            url,
            params=dict(params) if params else None,
            headers=merged_headers,
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload: JSONPayload = response.json()

        if ttl_seconds > 0:
            with self._lock:
                self._cache[cache_key] = _CacheEntry(
                    payload=payload,
                    expires_at=now + ttl_seconds,
                )

        return payload

    @staticmethod
    def _cache_key(
        provider: str,
        url: str,
        params: Mapping[str, Any] | None,
    ) -> tuple[str, str, tuple[tuple[str, str], ...]]:
        """Build an order-independent cache key.

        Params are coerced to ``(str, str)`` pairs so e.g. ``{"x": 1}``
        and ``{"x": "1"}`` key to the same entry — matching how the
        wire encodes them.
        """
        if params is None:
            frozen: tuple[tuple[str, str], ...] = ()
        else:
            frozen = tuple(sorted((str(k), str(v)) for k, v in params.items()))
        return (provider, url, frozen)
