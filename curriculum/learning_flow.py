"""Validate and query the Project 1A learning-flow manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(__file__).with_name("learning-flow.json")
LESSON_PHASES = {
    "not_started",
    "studying",
    "ready_to_implement",
    "implementing",
    "consolidating",
    "learned",
}
MICRO_WORLD_DECISIONS = {"none", "optional", "required"}


class ManifestError(ValueError):
    """Raised when the curriculum manifest cannot safely drive the system."""


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError(f"Could not read learning-flow manifest: {error}") from error
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: object) -> None:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ManifestError("learning-flow manifest must use schema_version 1")
    lessons = manifest.get("lessons")
    if not isinstance(lessons, dict) or not lessons:
        raise ManifestError("learning-flow manifest must contain lessons")

    known = set(lessons)
    for lesson_id, lesson in lessons.items():
        if not isinstance(lesson, dict):
            raise ManifestError(f"{lesson_id}: lesson entry must be an object")
        for key in ("requires", "unlocks"):
            references = lesson.get(key)
            if not isinstance(references, list) or not all(isinstance(item, str) for item in references):
                raise ManifestError(f"{lesson_id}: {key} must be a list of lesson IDs")
            missing = set(references) - known
            if missing:
                raise ManifestError(f"{lesson_id}: unknown {key} references: {sorted(missing)}")
        if not str(lesson.get("learning_goal", "")).strip():
            raise ManifestError(f"{lesson_id}: learning_goal is required")
        established_by = lesson.get("established_by", [])
        if not isinstance(established_by, list) or not all(isinstance(item, str) for item in established_by):
            raise ManifestError(f"{lesson_id}: established_by must be a list of learning records")
        for record in established_by:
            record_path = (ROOT / record).resolve()
            if ROOT not in record_path.parents or not record_path.is_file():
                raise ManifestError(f"{lesson_id}: established learning record does not exist: {record}")
        validate_implementation(lesson_id, lesson.get("implementation"))
        validate_micro_world(lesson_id, lesson.get("micro_world"))

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(lesson_id: str) -> None:
        if lesson_id in visiting:
            raise ManifestError(f"learning-flow prerequisite cycle includes {lesson_id}")
        if lesson_id in visited:
            return
        visiting.add(lesson_id)
        for required in lessons[lesson_id]["requires"]:
            visit(required)
        visiting.remove(lesson_id)
        visited.add(lesson_id)

    for lesson_id in lessons:
        visit(lesson_id)


def validate_implementation(lesson_id: str, implementation: object) -> None:
    if not isinstance(implementation, dict):
        raise ManifestError(f"{lesson_id}: implementation is required")
    targets = implementation.get("targets")
    if not isinstance(targets, list) or not all(isinstance(item, str) for item in targets):
        raise ManifestError(f"{lesson_id}: implementation.targets must be a list")
    for target in targets:
        target_path = (ROOT / target).resolve()
        if ROOT not in target_path.parents or not target_path.is_file():
            raise ManifestError(f"{lesson_id}: implementation target does not exist: {target}")
    command = implementation.get("proof_command")
    if command is not None and (
        not isinstance(command, list)
        or not command
        or not all(isinstance(item, str) and item for item in command)
    ):
        raise ManifestError(f"{lesson_id}: proof_command must be null or a non-empty argument array")
    if not str(implementation.get("first_proof", "")).strip():
        raise ManifestError(f"{lesson_id}: first_proof is required")


def validate_micro_world(lesson_id: str, micro_world: object) -> None:
    if not isinstance(micro_world, dict):
        raise ManifestError(f"{lesson_id}: micro_world decision is required")
    decision = micro_world.get("decision")
    score = micro_world.get("score")
    if decision not in MICRO_WORLD_DECISIONS:
        raise ManifestError(f"{lesson_id}: invalid micro_world decision")
    if not isinstance(score, int) or not -6 <= score <= 9:
        raise ManifestError(f"{lesson_id}: micro_world score must be between -6 and 9")
    if not str(micro_world.get("rationale", "")).strip():
        raise ManifestError(f"{lesson_id}: micro_world rationale is required")
    if not str(micro_world.get("fallback", "")).strip():
        raise ManifestError(f"{lesson_id}: micro_world fallback is required")
    if decision == "required" and score < 6:
        raise ManifestError(f"{lesson_id}: required micro-world score must be at least 6")
    if decision == "none" and score > 2:
        raise ManifestError(f"{lesson_id}: none micro-world score must be at most 2")
    if decision == "required" and not micro_world.get("component"):
        raise ManifestError(f"{lesson_id}: required micro-world needs a component")


def lesson_config(lesson_id: str, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    lessons = (manifest or load_manifest())["lessons"]
    try:
        return lessons[lesson_id]
    except KeyError as error:
        raise ManifestError(f"Unknown lesson ID: {lesson_id}") from error


def prerequisites_met(
    lesson_id: str,
    phases: dict[str, str],
    manifest: dict[str, Any] | None = None,
) -> bool:
    lesson = lesson_config(lesson_id, manifest)
    return all(phases.get(required) == "learned" for required in lesson["requires"])
