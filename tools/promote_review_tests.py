"""Safely promote reviewed generated tests into the main test suites."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = PROJECT_ROOT / "tests" / "review"
MANIFEST_PATH = REVIEW_ROOT / "manifest.json"
TEST_KINDS = ("ui", "api", "e2e")
BLOCKER_PATTERNS = {
    "review skip marker": re.compile(r"^\s*@pytest\.mark\.skip", re.MULTILINE),
    "empty test body (pass)": re.compile(r"^\s*pass\s*(?:#.*)?$", re.MULTILINE),
    "TODO marker": re.compile(r"\bTODO\b", re.IGNORECASE),
    "placeholder marker": re.compile(r"\bplaceholder\b", re.IGNORECASE),
}
REVIEW_MARKER = re.compile(r"^\s*@pytest\.mark\.review\s*\r?\n", re.MULTILINE)


@dataclass(frozen=True)
class Candidate:
    source: Path
    destination: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and promote reviewed tests from tests/review/<JIRA>."
    )
    parser.add_argument("jira_key", help="Review task key, for example KAN-2")
    parser.add_argument(
        "--kind",
        choices=TEST_KINDS,
        help="Promote only one suite type: ui, api, or e2e",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Move validated files into tests/<kind>"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run pytest for selected review tests before promotion",
    )
    return parser.parse_args()


def collect_candidates(jira_key: str, kind: str | None) -> list[Candidate]:
    task_root = REVIEW_ROOT / jira_key
    kinds = (kind,) if kind else TEST_KINDS
    candidates: list[Candidate] = []
    for suite_kind in kinds:
        source_root = task_root / suite_kind
        if not source_root.exists():
            continue
        for source in sorted(source_root.rglob("test_*.py")):
            relative_path = source.relative_to(source_root)
            candidates.append(
                Candidate(source, PROJECT_ROOT / "tests" / suite_kind / relative_path)
            )
    return candidates


def blockers(candidate: Candidate) -> list[str]:
    content = candidate.source.read_text(encoding="utf-8")
    found = [
        description
        for description, pattern in BLOCKER_PATTERNS.items()
        if pattern.search(content)
    ]
    if candidate.destination.exists():
        found.append(f"destination already exists: {candidate.destination.relative_to(PROJECT_ROOT)}")
    return found


def verify(candidates: list[Candidate]) -> int:
    paths = [str(candidate.source) for candidate in candidates]
    return subprocess.run([sys.executable, "-m", "pytest", *paths, "-v"], cwd=PROJECT_ROOT).returncode


def update_manifest(candidates: list[Candidate], jira_key: str) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    promoted = {
        str(candidate.source.relative_to(PROJECT_ROOT)).replace("/", "\\"): candidate
        for candidate in candidates
    }
    for item in manifest.get("files", []):
        normalized_path = str(item.get("path", "")).replace("/", "\\")
        candidate = promoted.get(normalized_path)
        if candidate and item.get("jira_key") == jira_key:
            item["path"] = str(candidate.destination.relative_to(PROJECT_ROOT)).replace("/", "\\")
            item["status"] = "promoted"
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def promote(candidates: list[Candidate], jira_key: str) -> None:
    for candidate in candidates:
        content = candidate.source.read_text(encoding="utf-8")
        approved_content = REVIEW_MARKER.sub("", content)
        candidate.source.write_text(approved_content, encoding="utf-8")
        candidate.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(candidate.source), str(candidate.destination))

    update_manifest(candidates, jira_key)
    sync_qase_coverage([candidate.destination for candidate in candidates])
    for source_dir in sorted(
        {candidate.source.parent for candidate in candidates}, key=lambda path: len(path.parts), reverse=True
    ):
        if source_dir.exists() and not any(source_dir.iterdir()):
            source_dir.rmdir()


def sync_qase_coverage(paths: list[Path]) -> None:
    """Update Qase only after pytest verification and successful file promotion."""
    from sync_qase_coverage import sync

    synced = sync(paths, apply=True)
    if synced:
        print(f"Qase manual-case coverage updated: {len(synced)} case(s).")


def main() -> int:
    args = parse_args()
    candidates = collect_candidates(args.jira_key, args.kind)
    if not candidates:
        print(f"No review tests found for {args.jira_key}.")
        return 1

    validation_errors = {
        candidate: blockers(candidate) for candidate in candidates if blockers(candidate)
    }
    if validation_errors:
        print("Promotion blocked. Complete these files first:")
        for candidate, issues in validation_errors.items():
            print(f"- {candidate.source.relative_to(PROJECT_ROOT)}: {', '.join(issues)}")
        return 2

    print("Validated files:")
    for candidate in candidates:
        print(f"- {candidate.source.relative_to(PROJECT_ROOT)} -> {candidate.destination.relative_to(PROJECT_ROOT)}")

    if args.verify:
        result = verify(candidates)
        if result:
            return result

    if not args.apply:
        print("Dry run only. Re-run with --apply to move these files.")
        return 0

    promote(candidates, args.jira_key)
    print("Promotion complete. The review marker was removed and manifest entries are marked promoted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
