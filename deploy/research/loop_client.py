"""Versioned recurring client: current official price proof, unchanged pinned requests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import requests

from deploy.research.cloud import hash_bytes
from src.agents.jev import ENDPOINT, MODEL, RESERVE_NANO_USD, Choice, JevError, parse_response

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.agents.budget import Budget

PRICE_URL = "https://docs.typesafe.ai/models.md"


def validate_price(document: str) -> None:
    rows = [
        [v.strip().replace("\\$", "$") for v in line.strip().strip("|").split("|")]
        for line in document.splitlines()
        if line.strip().startswith("|")
    ]
    table = {r[0]: r[1:] for r in rows if r}
    try:
        column = table["Model ID"].index("`jev-1.13.0`")
        if (
            table["Price (per Btok / per Mtok)"][column] != "$42 / $0.042"
            or table["Context length"][column] != "64k per-request / 32k per-question"
            or "You pay per input token. Output tokens are free." not in document
        ):
            raise ValueError("Official model terms changed")
    except (KeyError, IndexError, ValueError):
        raise ValueError("Official model/pricing terms unavailable or changed") from None


def price_proof(*, clock: Callable[[], datetime] | None = None) -> dict[str, Any]:
    with requests.get(PRICE_URL, timeout=(5, 20), allow_redirects=False, stream=True) as response:
        if response.status_code != 200:
            raise ValueError("Official pricing unavailable; no paid call")
        raw = bytearray()
        for chunk in response.iter_content(8192):
            raw.extend(chunk)
            if len(raw) > 128000:
                raise ValueError("Pricing document too large")
    validate_price(raw.decode("utf-8"))
    return {
        "model": MODEL,
        "input_nano_usd_per_token": 42,
        "output_nano_usd_per_token": 0,
        "checked_at": int((clock() if clock else datetime.now(UTC)).timestamp()),
        "document_sha256": hash_bytes(bytes(raw)),
        "url": PRICE_URL,
    }


class LoopClient:
    def __init__(
        self,
        api_key: str,
        budget: Budget,
        *,
        proof: dict[str, Any],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not api_key.strip():
            raise JevError("TypeSafe token is missing from the environment or .env.local")
        self._api_key = api_key.strip()
        self.proof = proof
        self.budget = budget
        self.clock = clock or (lambda: datetime.now(UTC))

    def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice:
        now = self.clock()
        if (
            now.tzinfo is None
            or not 0 <= now.timestamp() - self.proof["checked_at"] < 900
            or self.proof["model"] != MODEL
        ):
            raise JevError("Current official pricing proof required before recurring paid calls")
        if (
            not state.strip()
            or not instructions.strip()
            or not 2 <= len(options) <= 32
            or any(not k.strip() or not v.strip() for k, v in options.items())
        ):
            raise JevError("Provide state, instructions and 2–32 nonempty choices")
        payload = {
            "model": MODEL,
            "state": state,
            "questions": {
                "decision": {
                    "type": "choice",
                    "instructions": instructions,
                    "criteria": options,
                }
            },
        }
        wire = json.dumps(payload, ensure_ascii=True, allow_nan=False).encode("utf-8")
        if len(wire) > 24_000:
            raise JevError("Jev request exceeds the 24,000-byte local bound")
        call_id = self.budget.reserve("typesafe", RESERVE_NANO_USD, now=now)
        try:
            # requests does not retry POST by default. Never follow redirects with the key.
            with requests.post(
                ENDPOINT,
                data=wire,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=(5, 20),
                allow_redirects=False,
                stream=True,
            ) as response:
                if response.status_code != 200:
                    raise JevError(f"TypeSafe HTTP {response.status_code}; reservation retained")
                chunks = bytearray()
                for chunk in response.iter_content(8192):
                    chunks.extend(chunk)
                    if len(chunks) > 256_000:
                        raise JevError("Oversized Jev response; reservation retained")
                data = json.loads(chunks)
        except requests.RequestException:
            raise JevError("TypeSafe connection failed; full reservation retained") from None
        except (ValueError, UnicodeError):
            raise JevError("Invalid Jev response encoding; full reservation retained") from None
        result = parse_response(data, options)
        self.budget.settle(
            call_id, result.cost_nano_usd, model=result.model, input_tokens=result.input_tokens
        )
        return result
