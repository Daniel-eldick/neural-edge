"""Encrypted transport and at-most-once hosted execution of the unchanged frozen study."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import sqlite3
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

import requests
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

STUDY = "user_data/research/lesson-week-v2"
WORKSPACE = "user_data/research/jev-workspace-v1"
PROTOCOL_SHA = "be2d931972ccdc9fec680c174b19c370ecbb5056eee262dec1266d3a8837472b"
CODE_SHA = "dbc481a9d5a2d8731201d466efbb66166a9cd807142ece0e966a243f1e3938f3"
READY = int(datetime(2026, 10, 25, 6, 30, tzinfo=UTC).timestamp())
EXPIRY = int(datetime(2026, 11, 1, tzinfo=UTC).timestamp())
REPO = "Daniel-eldick/neural-edge"
CLAIM = "research/lesson-week-v2-cloud-claimed"
MAX_ARCHIVE = 32_000_000
MAX_EXPANDED = 128_000_000


def hash_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encrypt(raw: bytes, key: bytes, domain: str) -> bytes:
    nonce = os.urandom(12)
    return b"JEV1" + nonce + AESGCM(key).encrypt(nonce, raw, domain.encode())


def decrypt(raw: bytes, key: bytes, domain: str) -> bytes:
    if len(raw) > MAX_ARCHIVE or raw[:4] != b"JEV1" or len(raw) < 32:
        raise ValueError("Invalid encrypted envelope")
    try:
        return AESGCM(key).decrypt(raw[4:16], raw[16:], domain.encode())
    except InvalidTag:
        raise ValueError("Envelope authentication failed") from None


def archive(files: dict[str, bytes], metadata: dict[str, Any]) -> bytes:
    if len(files) > 255 or sum(map(len, files.values())) > MAX_EXPANDED:
        raise ValueError("Archive source count/size exceeds bound")
    output = io.BytesIO()
    manifest = {"metadata": metadata, "files": {n: hash_bytes(b) for n, b in files.items()}}
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, raw in sorted(files.items()):
            target.writestr(name, raw)
        target.writestr("bundle-manifest.json", json.dumps(manifest, sort_keys=True))
    data = output.getvalue()
    if len(data) > MAX_ARCHIVE - 64:
        raise ValueError("Archive exceeds fixed bound")
    return data


def unpack(raw: bytes, destination: Path, *, reuse: bool = False) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(raw)) as source:
        infos = source.infolist()
        if (
            len(infos) > 256
            or len({i.filename for i in infos}) != len(infos)
            or sum(i.file_size for i in infos) > MAX_EXPANDED
        ):
            raise ValueError("Archive count/expanded bound exceeded")
        for info in infos:
            name = PurePosixPath(info.filename)
            if (
                not name.parts
                or str(name) != info.filename
                or len(info.filename) > 256
                or name.is_absolute()
                or ".." in name.parts
                or "\\" in info.filename
                or info.is_dir()
                or (info.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise ValueError("Unsafe archive path")
        manifest = json.loads(source.read("bundle-manifest.json"))
        expected = manifest["files"]
        if set(expected) | {"bundle-manifest.json"} != {i.filename for i in infos}:
            raise ValueError("Archive allowlist differs")
        for name, digest in expected.items():
            if hash_bytes(source.read(name)) != digest:
                raise ValueError("Archive file checksum differs")
        if destination.is_symlink():
            raise ValueError("Restore destination cannot be a symlink")
        destination.mkdir(mode=0o700, parents=True, exist_ok=reuse)
        for name in expected:
            target = destination / name
            if any(p.is_symlink() for p in [target, *target.parents]):
                raise ValueError("Restore paths cannot follow symlinks")
            if reuse and target.exists():
                if hash_bytes(target.read_bytes()) != expected[name]:
                    raise ValueError("Existing restored bytes differ")
                continue
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open("xb") as handle:
                os.chmod(target, 0o600)
                handle.write(source.read(name))
        return dict(manifest["metadata"])


def git_api(
    method: str, endpoint: str, token: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    if not endpoint.startswith(f"/repos/{REPO}/"):
        raise ValueError("GitHub operation outside the study repository")
    try:
        response = requests.request(
            method,
            "https://api.github.com" + endpoint,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            json=payload,
            timeout=(5, 30),
            allow_redirects=False,
        )
        if response.status_code not in (200, 201, 204):
            raise RuntimeError(f"GitHub operation HTTP {response.status_code}; no retry")
        if len(response.content) > 2_000_000:
            raise ValueError("GitHub metadata response exceeds bound")
        return dict(response.json()) if response.content else {}
    except requests.RequestException:
        raise RuntimeError("GitHub operation uncertain; no automatic retry") from None


def claim(token: str, revision: str) -> None:
    """Creating a ref is atomic; an existing or ambiguous claim never permits paid work."""
    git_api(
        "POST", f"/repos/{REPO}/git/refs", token, {"ref": f"refs/heads/{CLAIM}", "sha": revision}
    )


def publish_result(token: str, revision: str, sealed: bytes) -> None:
    blob = git_api(
        "POST",
        f"/repos/{REPO}/git/blobs",
        token,
        {"content": base64.b64encode(sealed).decode(), "encoding": "base64"},
    )
    tree = git_api(
        "POST",
        f"/repos/{REPO}/git/trees",
        token,
        {"tree": [{"path": "result.enc", "mode": "100644", "type": "blob", "sha": blob["sha"]}]},
    )
    commit = git_api(
        "POST",
        f"/repos/{REPO}/git/commits",
        token,
        {
            "message": "Preserve encrypted frozen study outcome",
            "tree": tree["sha"],
            "parents": [revision],
        },
    )
    git_api(
        "PATCH",
        f"/repos/{REPO}/git/refs/heads/{CLAIM}",
        token,
        {"sha": commit["sha"], "force": False},
    )


def input_bytes(root: Path, path: Path) -> bytes:
    relative = path.relative_to(root)
    cursor = root
    if root.is_symlink():
        raise ValueError("Input root cannot be a symlink")
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("Input path cannot follow symlinks")
    if not path.is_file() or path.stat().st_size > 4_000_000:
        raise ValueError("Input file exceeds the fixed research transport bound")
    with path.open("rb") as handle:
        raw = handle.read(4_000_001)
    if len(raw) > 4_000_000:
        raise ValueError("Input changed beyond its byte bound")
    return raw


def prepare(root: Path, directory: Path, *, resume: bool = False) -> dict[str, Any]:
    from deploy.research.guard import export_escrow, resume_export
    from src.agents.budget import Budget
    from src.agents.jev import LEDGER
    from src.agents.lessons import LessonPack
    from src.evaluation.lesson_week import validate_protocol
    from src.research.analysis import sha

    protocol = validate_protocol(root / STUDY, LessonPack.load(root / WORKSPACE, "pilot-jev-1"))
    if sha(protocol) != PROTOCOL_SHA or (root / STUDY / "run-started.json").exists():
        raise ValueError("Original protocol/one-shot state differs")
    if resume:
        if directory.is_symlink() or {p.name for p in directory.iterdir()} != {
            "envelope.key",
            "execution-budget.sqlite",
        }:
            raise ValueError("Only an unsealed, unpublished preparation can recover")
        key = input_bytes(directory, directory / "envelope.key")
        if len(key) != 32:
            raise ValueError("Unsealed encryption key differs")
        metadata = resume_export(
            Budget(LEDGER), directory / "execution-budget.sqlite", now=datetime.now(UTC)
        )
    else:
        directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        key = os.urandom(32)
        key_path = directory / "envelope.key"
        with key_path.open("xb") as target:
            os.chmod(key_path, 0o600)
            target.write(key)
        metadata = export_escrow(
            Budget(LEDGER), directory / "execution-budget.sqlite", now=datetime.now(UTC)
        )
    files = {}
    source_paths = sorted((root / "src").rglob("*.py"))
    if len(source_paths) > 240:
        raise ValueError("Source tree exceeds the research snapshot count")
    for path in source_paths:
        files[str(path.relative_to(root))] = input_bytes(root, path)
    for relative in [
        "control/manifest.json",
        "evidence/evidence.json",
        "control/pilot-jev-1/contract.json",
        "control/pilot-jev-1/lesson.json",
        "control/pilot-jev-1/responses.sqlite",
        "outputs/pilot-jev-1/analysis.json",
        "lessons/pilot-jev-1.json",
    ]:
        path = root / WORKSPACE / relative
        files[f"{WORKSPACE}/{relative}"] = input_bytes(root, path)
    files[f"{STUDY}/protocol.json"] = input_bytes(root, root / STUDY / "protocol.json")
    files["user_data/ai/budget.sqlite"] = (directory / "execution-budget.sqlite").read_bytes()
    metadata.update(
        protocol_sha256=PROTOCOL_SHA,
        code_sha256=CODE_SHA,
        controller_sha256=hash_bytes(Path(__file__).read_bytes()),
        guard_sha256=hash_bytes(Path(__file__).with_name("guard.py").read_bytes()),
    )
    sealed = encrypt(archive(files, metadata), key, "input")
    (directory / "input.enc").write_bytes(sealed)
    (directory / "allocation.json").write_text(json.dumps(metadata, sort_keys=True))
    os.chmod(directory / "allocation.json", 0o600)
    public = {
        "schema": 1,
        "study": "lesson-week-v2",
        "input_sha256": hash_bytes(sealed),
        "protocol_sha256": PROTOCOL_SHA,
        "code_sha256": CODE_SHA,
        "ready_at": READY,
        "expires_at": EXPIRY,
    }
    (directory / "runner.json").write_text(json.dumps(public, sort_keys=True))
    return public


def restore(public: Path, sealed: Path, key: bytes, destination: Path) -> dict[str, Any]:
    config = json.loads(public.read_text())
    if config != {
        "schema": 1,
        "study": "lesson-week-v2",
        "input_sha256": hash_bytes(sealed.read_bytes()),
        "protocol_sha256": PROTOCOL_SHA,
        "code_sha256": CODE_SHA,
        "ready_at": READY,
        "expires_at": EXPIRY,
    }:
        raise ValueError("Public encrypted snapshot binding differs")
    metadata = unpack(decrypt(sealed.read_bytes(), key, "input"), destination)
    if (
        metadata["controller_sha256"] != hash_bytes(Path(__file__).read_bytes())
        or metadata["guard_sha256"] != hash_bytes(Path(__file__).with_name("guard.py").read_bytes())
        or metadata["protocol_sha256"] != PROTOCOL_SHA
        or metadata["code_sha256"] != CODE_SHA
    ):
        raise ValueError("Transport/controller differs from the allocated snapshot")
    return metadata


def hosted(mode: str, root: Path, metadata: dict[str, Any], key: bytes, *, now: datetime) -> str:
    sys.path.insert(0, str(root))
    from deploy.research.guard import FundedBudget
    from src.agents.jev import JevClient
    from src.agents.lessons import LessonPack
    from src.evaluation.lesson_week import execute_study, validate_protocol
    from src.research.analysis import sha

    lesson = LessonPack.load(root / WORKSPACE, "pilot-jev-1")
    protocol = validate_protocol(root / STUDY, lesson)
    if sha(protocol) != PROTOCOL_SHA:
        raise ValueError("Restored frozen protocol differs")
    budget = FundedBudget(root / "user_data/ai/budget.sqlite", metadata)
    budget.snapshot(now=now)
    if mode == "verify" or int(now.timestamp()) < READY:
        return "verified_waiting_for_data"
    if int(now.timestamp()) >= EXPIRY:
        raise ValueError("Frozen October authorization expired")
    github_token = os.environ["GH_TOKEN"]
    revision = os.environ["GITHUB_SHA"]
    claim(github_token, revision)
    terminal = False
    try:
        client = JevClient(os.environ["TYPESAFE_API_KEY"], budget)
        report = execute_study(root / STUDY, lesson, client, budget, now=now)
        terminal = True
    finally:
        files = {
            f"study/{p.name}": p.read_bytes()
            for p in (root / STUDY).iterdir()
            if p.is_file() and not p.name.endswith(("-wal", "-shm"))
        }
        with sqlite3.connect(budget.path.as_uri() + "?mode=ro", uri=True) as source:
            copied = root / "result-budget.sqlite"
            with sqlite3.connect(copied) as target:
                source.backup(target)
        files["execution-budget.sqlite"] = copied.read_bytes()
        receipt = {
            "terminal": terminal,
            "protocol_sha256": PROTOCOL_SHA,
            "allocation": metadata,
            "usage": budget.usage(),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "scope": "Execution snapshots are not current shared-ledger balances",
        }
        files["cloud-receipt.json"] = json.dumps(receipt, sort_keys=True).encode()
        publish_result(github_token, revision, encrypt(archive(files, receipt), key, "result"))
    return (
        "encrypted_terminal_outcome_saved"
        if report["status"] == "complete"
        else "encrypted_failed_outcome_saved"
    )


def collect(directory: Path, root: Path) -> dict[str, Any]:
    from deploy.research.guard import FundedBudget, reconcile
    from src.agents.budget import Budget
    from src.agents.jev import LEDGER
    from src.research.workspace import load_contract

    key = (directory / "envelope.key").read_bytes()
    allocation = json.loads((directory / "allocation.json").read_text())
    restored = directory / "collected"
    receipt = unpack(
        decrypt((directory / "result.enc").read_bytes(), key, "result"), restored, reuse=True
    )
    if (
        receipt != json.loads((restored / "cloud-receipt.json").read_text())
        or receipt["terminal"] is not True
        or receipt["allocation"] != allocation
        or receipt["protocol_sha256"] != PROTOCOL_SHA
    ):
        raise ValueError("No authenticated terminal outcome; keep the full host escrow")
    execution = FundedBudget(restored / "execution-budget.sqlite", allocation)
    usage = execution.usage()
    if usage != receipt["usage"]:
        raise ValueError("Result usage differs from execution ledger")
    study = root / STUDY
    files = sorted((restored / "study").iterdir())
    if (restored / "study/protocol.json").read_bytes() != (
        study / "protocol.json"
    ).read_bytes() or load_contract(restored / "study/result-contract.json") != json.loads(
        (restored / "study/result.json").read_text()
    ):
        raise ValueError("Result protocol or report differs")
    for path in files:
        target = study / path.name
        if target.exists() and target.read_bytes() != path.read_bytes():
            raise ValueError("Local study has a different preserved artifact")
    for path in files:
        target = study / path.name
        if not target.exists():
            with target.open("xb") as handle:
                os.chmod(target, 0o600)
                handle.write(path.read_bytes())
    outcome = (
        "full_hold_retained_uncertain_usage"
        if usage["pending_calls"]
        else reconcile(Budget(LEDGER), allocation, usage)
    )
    return {
        "status": outcome,
        "usage": usage,
        "october_budget": Budget(LEDGER).snapshot(now=datetime(2026, 10, 31, tzinfo=UTC)),
        "current_budget": Budget(LEDGER).snapshot(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "resume-prepare", "verify", "run", "collect"])
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.mode in {"prepare", "resume-prepare"}:
            result = prepare(Path.cwd(), args.directory, resume=args.mode == "resume-prepare")
        elif args.mode == "collect":
            result = collect(args.directory, Path.cwd())
        else:
            key = base64.b64decode(os.environ["JEV_RESEARCH_ENVELOPE_KEY"], validate=True)
            root = args.directory / "restored"
            metadata = restore(
                args.directory / "runner.json", args.directory / "input.enc", key, root
            )
            result = {"status": hosted(args.mode, root, metadata, key, now=datetime.now(UTC))}
        print(json.dumps(result, sort_keys=True))
        if result.get("status") == "encrypted_failed_outcome_saved":
            parser.exit(1)
    except (
        RuntimeError,
        ValueError,
        OSError,
        sqlite3.Error,
        KeyError,
        TypeError,
        zipfile.BadZipFile,
    ):
        parser.exit(1, "Cloud research stopped; preserve escrow and claim. No automatic retry.\n")


if __name__ == "__main__":
    main()
