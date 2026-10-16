"""Paid attempts must survive candle rollback and never be retried ambiguously."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from src.agents.jev import MODEL, Choice, JevError
from src.agents.responses import ResponseError, ResponseStore

if TYPE_CHECKING:
    from pathlib import Path

OPTIONS = {"enter": "Accept candidate", "wait": "Abstain"}


class Provider:
    def __init__(self, failure: BaseException | None = None) -> None:
        self.calls = 0
        self.failure = failure

    def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice:
        self.calls += 1
        if self.failure:
            raise self.failure
        return Choice("enter", 0.8, {"enter": 0.8, "wait": 0.2}, MODEL, 100, 4200)


def test_reopen_reuses_saved_response_even_at_attempt_limit(tmp_path: Path) -> None:
    path = tmp_path / "responses.sqlite"
    provider = Provider()
    store = ResponseStore(path)
    identity = store.identity
    answer = store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 1)
    store.close()
    store = ResponseStore(path, resume=True)
    try:
        assert store.identity == identity
        assert store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 1) == answer
        with pytest.raises(ResponseError, match="limit"):
            store.choose("BTC:600", "next bars", "Choose", OPTIONS, provider, 1)
        assert provider.calls == 1
    finally:
        store.close()


@pytest.mark.parametrize("failure", [SystemExit("crash"), JevError("Provider unavailable"),
                                    RuntimeError("PRIVATE-KEY")])
def test_failed_or_interrupted_attempt_is_never_resubmitted(
    tmp_path: Path, failure: BaseException,
) -> None:
    path = tmp_path / "responses.sqlite"
    store = ResponseStore(path)
    provider = Provider(failure)
    with pytest.raises((ResponseError, SystemExit)) as exc:
        store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 20)
    assert "PRIVATE-KEY" not in str(exc.value)
    store.close()
    store = ResponseStore(path, resume=True)
    try:
        with pytest.raises(ResponseError):
            store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 20)
        assert provider.calls == 1
    finally:
        store.close()


def test_mismatch_and_corrupt_response_fail_before_network(tmp_path: Path) -> None:
    path = tmp_path / "responses.sqlite"
    provider = Provider()
    store = ResponseStore(path)
    store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 20)
    with pytest.raises(ResponseError, match="differs"):
        store.choose("BTC:300", "changed bars", "Choose", OPTIONS, provider, 20)
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE attempts SET checksum='bad'")
    with pytest.raises(ResponseError, match="corrupt"):
        store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 20)
    assert provider.calls == 1
    store.close()


def test_missing_resume_store_never_creates_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.sqlite"
    with pytest.raises(ResponseError):
        ResponseStore(path, resume=True)
    assert not path.exists()


def test_success_followed_by_disk_write_failure_remains_uncertain(tmp_path: Path) -> None:
    path = tmp_path / "responses.sqlite"
    store = ResponseStore(path)
    provider = Provider()
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TRIGGER fail_save BEFORE UPDATE ON attempts
            BEGIN SELECT RAISE(ABORT, 'injected disk failure'); END
        """)
    with pytest.raises(ResponseError, match="persistence"):
        store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 20)
    with pytest.raises(ResponseError, match="new requests blocked"):
        store.choose("ETH:600", "different candidate", "Choose", OPTIONS, provider, 20)
    store.close()
    store = ResponseStore(path, resume=True)
    try:
        with pytest.raises(ResponseError, match="uncertain"):
            store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 20)
        with pytest.raises(ResponseError, match="new requests blocked"):
            store.choose("ETH:600", "different candidate", "Choose", OPTIONS, provider, 20)
        assert provider.calls == 1
    finally:
        store.close()


def test_concurrent_claim_cannot_call_provider_twice(tmp_path: Path) -> None:
    path = tmp_path / "responses.sqlite"
    store = ResponseStore(path)
    other = ResponseStore(path, resume=True)

    class ContendingProvider(Provider):
        def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice:
            with pytest.raises(ResponseError, match="uncertain"):
                other.choose("BTC:300", state, instructions, options, self, 20)
            return super().choose(state, instructions, options)

    provider = ContendingProvider()
    try:
        store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 20)
        assert provider.calls == 1
    finally:
        store.close()
        other.close()


@pytest.mark.parametrize("failure", [JevError("Provider unavailable"), SystemExit("crash")])
def test_failure_blocks_new_keys_across_reopen_but_allows_cached_answers(
    tmp_path: Path, failure: BaseException,
) -> None:
    path = tmp_path / "responses.sqlite"
    provider = Provider()
    store = ResponseStore(path)
    answer = store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 20)
    provider.failure = failure
    with pytest.raises((ResponseError, SystemExit)):
        store.choose("BTC:600", "next bars", "Choose", OPTIONS, provider, 20)
    provider.failure = None
    try:
        for reopened in (False, True):
            if reopened:
                store.close()
                store = ResponseStore(path, resume=True)
            assert store.choose("BTC:300", "closed bars", "Choose", OPTIONS, provider, 20) == answer
            with pytest.raises(ResponseError, match="new requests blocked"):
                store.choose("ETH:900", "different candidate", "Choose", OPTIONS, provider, 20)
            assert provider.calls == 2
            assert store.connection.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 2
    finally:
        store.close()


def test_pending_claim_blocks_concurrent_distinct_candidate(tmp_path: Path) -> None:
    path = tmp_path / "responses.sqlite"
    store = ResponseStore(path)
    other = ResponseStore(path, resume=True)
    healthy = Provider()

    class ConcurrentProvider(Provider):
        def choose(self, state: str, instructions: str, options: dict[str, str]) -> Choice:
            with pytest.raises(ResponseError, match="new requests blocked"):
                other.choose("ETH:300", state, instructions, options, healthy, 20)
            return super().choose(state, instructions, options)

    try:
        store.choose("BTC:300", "closed bars", "Choose", OPTIONS, ConcurrentProvider(), 20)
        assert healthy.calls == 0
        # A pending successful request is released normally after settlement.
        other.choose("ETH:300", "closed bars", "Choose", OPTIONS, healthy, 20)
        assert healthy.calls == 1
    finally:
        store.close()
        other.close()
