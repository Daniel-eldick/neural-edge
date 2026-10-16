"""Recorded-response integration; no paid network calls in tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
import requests
import responses

from src.agents import jev as jev_module
from src.agents.budget import CAP_NANO_USD, Budget, BudgetError
from src.agents.jev import ENDPOINT, RESERVE_NANO_USD, JevClient, JevError

if TYPE_CHECKING:
    from pathlib import Path


NOW = datetime(2026, 9, 30, tzinfo=UTC)
OPTIONS = {"paper": "Simulation only", "live": "Real orders"}


def response() -> dict[str, Any]:
    return {
        "model": "jev-1.13.0", "usage": {"input_tokens": 100, "output_tokens": 3},
        "answers": {"decision": {"type": "choice", "choice": "paper", "confidence": 0.9,
                                  "probabilities": {"paper": 0.95, "live": 0.05}}},
    }


def client(tmp_path: Path) -> tuple[JevClient, Budget]:
    path = tmp_path / "budget.sqlite"
    Budget.initialize(path)
    budget = Budget(path)
    return JevClient("PRIVATE-TEST-KEY", budget, clock=lambda: NOW), budget


@responses.activate
def test_pinned_model_valid_choice_and_exact_spending(tmp_path: Path) -> None:
    jev, budget = client(tmp_path)
    responses.post(ENDPOINT, json=response())
    result = jev.choose("Paper mode", "Which mode?", OPTIONS)
    assert result.choice == "paper"
    assert result.cost_nano_usd == 4200
    assert budget.snapshot(now=NOW)["used_nano_usd"] == 4200
    sent = json.loads(responses.calls[0].request.body)  # type: ignore[arg-type]
    assert sent["model"] == "jev-1.13.0"
    assert "PRIVATE-TEST-KEY" not in json.dumps(sent)


@responses.activate
def test_timeout_is_sanitized_and_reservation_is_not_refunded(tmp_path: Path) -> None:
    jev, budget = client(tmp_path)
    responses.post(ENDPOINT, body=requests.Timeout("PRIVATE-TEST-KEY"))
    with pytest.raises(JevError) as exc:
        jev.choose("Paper mode", "Which mode?", OPTIONS)
    assert "PRIVATE-TEST-KEY" not in str(exc.value)
    assert len(responses.calls) == 1
    assert budget.snapshot(now=NOW)["used_nano_usd"] == RESERVE_NANO_USD


@responses.activate
@pytest.mark.parametrize("defect", ["choice", "probability", "confidence", "model", "usage"])
def test_malformed_response_never_becomes_a_decision(tmp_path: Path, defect: str) -> None:
    jev, budget = client(tmp_path)
    data = response()
    if defect == "choice":
        data["answers"]["decision"]["choice"] = "BUY_WITHOUT_LIMITS"
    elif defect == "probability":
        data["answers"]["decision"]["probabilities"]["paper"] = float("nan")
    elif defect == "confidence":
        data["answers"]["decision"]["confidence"] = 2
    elif defect == "model":
        data["model"] = "unreviewed-model"
    else:
        data["usage"]["input_tokens"] = -1
    responses.post(ENDPOINT, json=data)
    with pytest.raises(JevError):
        jev.choose("Paper mode", "Which mode?", OPTIONS)
    assert budget.snapshot(now=NOW)["used_nano_usd"] == RESERVE_NANO_USD


@responses.activate
def test_cap_blocks_network_calls(tmp_path: Path) -> None:
    jev, budget = client(tmp_path)
    budget.reserve("all-ai", CAP_NANO_USD, now=NOW)
    with pytest.raises(BudgetError):
        jev.choose("Paper mode", "Which mode?", OPTIONS)
    assert len(responses.calls) == 0


@responses.activate
def test_expired_pricing_blocks_network_calls(tmp_path: Path) -> None:
    _, budget = client(tmp_path)
    jev = JevClient("PRIVATE-TEST-KEY", budget,
                    clock=lambda: datetime(2026, 11, 1, tzinfo=UTC))
    with pytest.raises(JevError, match="pricing"):
        jev.choose("Paper mode", "Which mode?", OPTIONS)
    assert len(responses.calls) == 0


@responses.activate
def test_redirect_does_not_forward_token(tmp_path: Path) -> None:
    jev, _ = client(tmp_path)
    responses.post(ENDPOINT, status=307, headers={"Location": "https://example.com"})
    with pytest.raises(JevError, match="307"):
        jev.choose("Paper mode", "Which mode?", OPTIONS)
    assert len(responses.calls) == 1


@responses.activate
def test_budget_audit_cli_needs_no_credentials_or_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "budget.sqlite"
    Budget.initialize(path)
    reservation = Budget(path).reserve("typesafe", RESERVE_NANO_USD, now=NOW)
    before = path.read_bytes()
    monkeypatch.setattr(jev_module, "LEDGER", path)
    monkeypatch.setattr("sys.argv", ["jev", "--audit-budget"])
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)

    def forbid_credentials(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Audit must not load credentials")

    monkeypatch.setattr(jev_module, "dotenv_values", forbid_credentials)
    jev_module.main()
    report = json.loads(capsys.readouterr().out)
    assert report["unresolved_reservations"][0]["reservation_id"] == reservation
    assert "not confirmed charges" in report["note"]
    assert len(responses.calls) == 0
    assert path.read_bytes() == before


def test_budget_audit_cli_missing_ledger_is_not_reinitialized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "missing.sqlite"
    monkeypatch.setattr(jev_module, "LEDGER", path)
    monkeypatch.setattr("sys.argv", ["jev", "--audit-budget"])
    with pytest.raises(SystemExit) as error:
        jev_module.main()
    assert error.value.code == 1
    assert "cannot be audited" in capsys.readouterr().err
    assert not path.exists()
