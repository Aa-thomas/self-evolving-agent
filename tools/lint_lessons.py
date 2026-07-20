#!/usr/bin/env python3
"""Lint published Project 1A lessons against their evidence and practice contracts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "curriculum"
sys.path.insert(0, str(CURRICULUM))

from learning_flow import load_manifest, resolve_repository_file  # noqa: E402


LOCAL_HREF = re.compile(r'''(?:href|src)=["']([^"']+)["']''')
TEST_IDENTIFIER = re.compile(r"\b(test_[A-Za-z0-9_]+)\b")
ERROR_CODE = re.compile(r"\b(?:[A-Z][A-Z0-9]*_){1,}[A-Z0-9]+\b")
CASE_ID = re.compile(r"\bdata-case-id=[\"'][^\"']+[\"']")
CHOICE_GROUP = re.compile(r"<fieldset[^>]*data-case-id=[\"'][^\"']+[\"'][^>]*>(.*?)</fieldset>", re.DOTALL)
OPTION = re.compile(r"<input[^>]*\bvalue=[\"']([^\"']+)[\"'][^>]*>", re.DOTALL)
ANSWER = re.compile(r"\bdata-answer=[\"']([^\"']+)[\"']")


def bound_files(lesson: dict[str, Any]) -> list[Path]:
    paths: list[str] = []
    for contract_name in ("starting_artifacts", "target_artifacts"):
        contract = lesson[contract_name]
        paths.extend(contract["source_files"])
        paths.extend(contract["tests"])
        paths.extend(contract.get("scenario_sources", []))
    paths.append(lesson["failure_contract"]["source"])
    paths.extend(lesson["proof_artifacts"]["traces_or_output"])
    paths.extend(
        argument
        for argument in lesson["proof_artifacts"]["proof_command"]
        if argument.endswith((".py", ".json", ".txt", ".yaml", ".yml")) or "/" in argument
    )
    return [resolve_repository_file("lesson", path, "bound artifact") for path in dict.fromkeys(paths)]


def lint_lesson(lesson_id: str, lesson: dict[str, Any], source: Path) -> list[str]:
    """Return all publishing errors for one lesson source."""
    errors: list[str] = []
    html = source.read_text(encoding="utf-8")
    files = bound_files(lesson)
    bound_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files)
    starting_files = [
        resolve_repository_file(lesson_id, path, "starting artifact")
        for path in lesson["starting_artifacts"]["source_files"]
    ]
    starting_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in starting_files)

    for href in LOCAL_HREF.findall(html):
        if href.startswith(("https://", "http://", "#", "mailto:")):
            continue
        candidate = (source.parent / href).resolve()
        if ROOT not in candidate.parents or not candidate.is_file():
            errors.append(f"{lesson_id}: linked repository artifact does not exist: {href}")

    command = lesson["proof_artifacts"]["proof_command"]
    if not command:
        errors.append(f"{lesson_id}: published lesson has no runnable proof")

    for test_name in set(TEST_IDENTIFIER.findall(html)) | set(lesson["proof_artifacts"]["assertions"]):
        if test_name not in bound_text:
            errors.append(f"{lesson_id}: referenced test identifier drifted: {test_name}")

    for symbol in lesson["starting_artifacts"]["symbols"]:
        if not re.search(rf"\b{re.escape(symbol)}\b", starting_text):
            errors.append(f"{lesson_id}: declared starting symbol does not exist: {symbol}")

    for code in set(ERROR_CODE.findall(html)):
        if code not in bound_text:
            errors.append(f"{lesson_id}: error code is not present in bound artifacts: {code}")

    if re.search(r"\bdoes not yet (?:provide|exist|support|implement)\b", html, re.IGNORECASE):
        errors.append(f"{lesson_id}: published lesson claims an unavailable capability")

    if "data-prediction-submit" not in html or "data-prediction-answer" not in html:
        errors.append(f"{lesson_id}: prediction commitment and deferred answer are required")
    elif html.index("data-prediction-answer") < html.index("data-prediction-submit"):
        errors.append(f"{lesson_id}: prediction answer appears before commitment")

    minimum_cases = lesson["practice_contract"]["minimum_cases"]
    case_count = len(CASE_ID.findall(html))
    if case_count < minimum_cases:
        errors.append(f"{lesson_id}: practice has {case_count} cases; contract requires {minimum_cases}")
    if "data-rationale" not in html:
        errors.append(f"{lesson_id}: practice must collect a written rationale")
    if "data-feedback" not in html:
        errors.append(f"{lesson_id}: practice needs boundary feedback")

    positions: list[int] = []
    for group in CHOICE_GROUP.findall(html):
        answer_match = ANSWER.search(group)
        choices = OPTION.findall(group)
        if not answer_match or answer_match.group(1) not in choices:
            errors.append(f"{lesson_id}: case is missing a valid answer choice")
            continue
        positions.append(choices.index(answer_match.group(1)))
    if positions and len(set(positions)) == 1:
        errors.append(f"{lesson_id}: correct answer positions are degenerate")
    if case_count and len(positions) != case_count:
        errors.append(f"{lesson_id}: every practice case must use a case-set choice group")

    return errors


def lint(manifest: dict[str, Any], lessons_dir: Path = CURRICULUM / "lessons") -> list[str]:
    errors: list[str] = []
    for lesson_id, lesson in manifest["lessons"].items():
        if lesson["publication"]["status"] != "published":
            continue
        source = lessons_dir / f"{lesson_id}.html"
        if not source.is_file():
            errors.append(f"{lesson_id}: published lesson source is missing")
            continue
        errors.extend(lint_lesson(lesson_id, lesson, source))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=CURRICULUM / "learning-flow.json")
    parser.add_argument("--lessons-dir", type=Path, default=CURRICULUM / "lessons")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    errors = lint(manifest, args.lessons_dir)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("Lesson lint passed.")


if __name__ == "__main__":
    main()
