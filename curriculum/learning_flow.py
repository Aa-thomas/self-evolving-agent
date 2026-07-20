"""Validate and query the evidence-first Project 1A learning-flow manifest."""

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
PUBLICATION_STATUSES = {"draft", "locked", "published"}
LESSON_TYPES = {
    "briefing",
    "implementation_lab",
    "diagnostic_lab",
    "reconstruction_lab",
    "specification",
}
PRACTICE_KINDS = {"case_set", "trace_diagnosis", "code_change", "reconstruction"}
PRODUCTIVE_ACTIONS = {"implement", "diagnose", "test", "reconstruct", "debug"}
RECONSTRUCTION_MODES = {"annotated", "skeleton", "blank", "none"}
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


def resolve_repository_file(lesson_id: str, path: object, label: str) -> Path:
    if not isinstance(path, str) or not path:
        raise ManifestError(f"{lesson_id}: {label} must be a repository-relative file path")
    candidate = (ROOT / path).resolve()
    if ROOT not in candidate.parents or not candidate.is_file():
        raise ManifestError(f"{lesson_id}: {label} does not exist: {path}")
    return candidate


def string_list(lesson_id: str, value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ManifestError(f"{lesson_id}: {label} must be a list of non-empty strings")
    return value


def validate_manifest(manifest: object) -> None:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 2:
        raise ManifestError("learning-flow manifest must use schema_version 2")
    lessons = manifest.get("lessons")
    if not isinstance(lessons, dict) or not lessons:
        raise ManifestError("learning-flow manifest must contain lessons")

    known = set(lessons)
    for lesson_id, lesson in lessons.items():
        if not isinstance(lesson, dict):
            raise ManifestError(f"{lesson_id}: lesson entry must be an object")
        validate_references(lesson_id, lesson, known)
        validate_publication(lesson_id, lesson)
        validate_learning_records(lesson_id, lesson)
        validate_artifact_contracts(lesson_id, lesson)
        validate_failure_contract(lesson_id, lesson)
        validate_practice_contract(lesson_id, lesson)
        validate_reconstruction_contract(lesson_id, lesson)
        validate_completion_contract(lesson_id, lesson)
        validate_micro_world(lesson_id, lesson.get("micro_world"))

    validate_graph(lessons)


def validate_references(lesson_id: str, lesson: dict[str, Any], known: set[str]) -> None:
    for key in ("requires", "unlocks"):
        references = string_list(lesson_id, lesson.get(key), key)
        missing = set(references) - known
        if missing:
            raise ManifestError(f"{lesson_id}: unknown {key} references: {sorted(missing)}")
    if not str(lesson.get("learning_goal", "")).strip():
        raise ManifestError(f"{lesson_id}: learning_goal is required")
    if not str(lesson.get("learner_decision", "")).strip():
        raise ManifestError(f"{lesson_id}: learner_decision is required")


def validate_publication(lesson_id: str, lesson: dict[str, Any]) -> None:
    publication = lesson.get("publication")
    if not isinstance(publication, dict) or publication.get("status") not in PUBLICATION_STATUSES:
        raise ManifestError(f"{lesson_id}: publication.status must be draft, locked, or published")
    status = publication["status"]
    reason = publication.get("reason")
    if status in {"draft", "locked"} and not isinstance(reason, str):
        raise ManifestError(f"{lesson_id}: unpublished lessons require a publication reason")
    lesson_type = lesson.get("lesson_type")
    if lesson_type not in LESSON_TYPES:
        raise ManifestError(f"{lesson_id}: invalid lesson_type")
    if status == "locked":
        if lesson_type != "specification":
            raise ManifestError(f"{lesson_id}: locked lessons must be specifications")
        if lesson["unlocks"]:
            raise ManifestError(f"{lesson_id}: locked lessons cannot unlock dependent learning")
    if lesson_type == "specification" and status != "locked":
        raise ManifestError(f"{lesson_id}: specifications must remain locked")
    if status == "published" and lesson_type in {"briefing", "specification"}:
        raise ManifestError(f"{lesson_id}: published Project 1A lessons need productive work")


def validate_learning_records(lesson_id: str, lesson: dict[str, Any]) -> None:
    records = string_list(lesson_id, lesson.get("established_by", []), "established_by")
    for record in records:
        resolve_repository_file(lesson_id, record, "established learning record")


def validate_artifact_contracts(lesson_id: str, lesson: dict[str, Any]) -> None:
    status = lesson["publication"]["status"]
    starting = lesson.get("starting_artifacts")
    target = lesson.get("target_artifacts")
    proof = lesson.get("proof_artifacts")
    if not isinstance(starting, dict) or not isinstance(target, dict) or not isinstance(proof, dict):
        raise ManifestError(f"{lesson_id}: starting_artifacts, target_artifacts, and proof_artifacts are required")

    for name, contract in (("starting_artifacts", starting), ("target_artifacts", target)):
        for key in ("source_files", "tests"):
            paths = string_list(lesson_id, contract.get(key), f"{name}.{key}")
            if name == "starting_artifacts" or status == "published":
                for path in paths:
                    resolve_repository_file(lesson_id, path, f"{name}.{key}")
        if name == "starting_artifacts":
            string_list(lesson_id, contract.get("symbols"), f"{name}.symbols")
            scenario_sources = string_list(lesson_id, contract.get("scenario_sources"), f"{name}.scenario_sources")
            for source in scenario_sources:
                resolve_repository_file(lesson_id, source, f"{name}.scenario_sources")
    if not isinstance(target.get("expected_artifact"), str):
        raise ManifestError(f"{lesson_id}: target_artifacts.expected_artifact must be text")

    command = string_list(lesson_id, proof.get("proof_command"), "proof_artifacts.proof_command")
    string_list(lesson_id, proof.get("assertions"), "proof_artifacts.assertions")
    output_paths = string_list(lesson_id, proof.get("traces_or_output"), "proof_artifacts.traces_or_output")
    if status == "published":
        if not target["source_files"] and not target["tests"]:
            raise ManifestError(f"{lesson_id}: published lesson requires implementation targets")
        if not command:
            raise ManifestError(f"{lesson_id}: published lesson requires proof_artifacts.proof_command")
        for output in output_paths:
            resolve_repository_file(lesson_id, output, "proof_artifacts.traces_or_output")
        validate_command_paths(lesson_id, command)
    elif status == "locked" and command:
        raise ManifestError(f"{lesson_id}: locked specification cannot claim an executable proof")


def validate_command_paths(lesson_id: str, command: list[str]) -> None:
    for argument in command:
        if argument.endswith((".py", ".json", ".txt", ".yaml", ".yml")) or "/" in argument:
            resolve_repository_file(lesson_id, argument, "configured proof artifact")


def validate_failure_contract(lesson_id: str, lesson: dict[str, Any]) -> None:
    failure = lesson.get("failure_contract")
    if not isinstance(failure, dict):
        raise ManifestError(f"{lesson_id}: failure_contract is required")
    for key in ("source", "symptom", "responsible_boundary", "regression_target"):
        if not isinstance(failure.get(key), str) or not failure[key].strip():
            raise ManifestError(f"{lesson_id}: failure_contract.{key} is required")
    resolve_repository_file(lesson_id, failure["source"], "failure_contract.source")


def validate_practice_contract(lesson_id: str, lesson: dict[str, Any]) -> None:
    practice = lesson.get("practice_contract")
    if not isinstance(practice, dict) or practice.get("kind") not in PRACTICE_KINDS:
        raise ManifestError(f"{lesson_id}: invalid practice_contract.kind")
    minimum = practice.get("minimum_cases")
    if not isinstance(minimum, int) or minimum < 1:
        raise ManifestError(f"{lesson_id}: practice_contract.minimum_cases must be a positive integer")
    if lesson["publication"]["status"] == "published" and minimum < 5:
        raise ManifestError(f"{lesson_id}: published practice requires at least 5 cases")
    threshold = practice.get("passing_threshold")
    if not isinstance(threshold, (int, float)) or not 0 < threshold <= 1:
        raise ManifestError(f"{lesson_id}: practice_contract.passing_threshold must be between 0 and 1")
    if practice.get("rationale_required") is not True:
        raise ManifestError(f"{lesson_id}: practice_contract requires a rationale")
    if practice.get("productive_action") not in PRODUCTIVE_ACTIONS:
        raise ManifestError(f"{lesson_id}: practice_contract needs a productive learner action")


def validate_reconstruction_contract(lesson_id: str, lesson: dict[str, Any]) -> None:
    reconstruction = lesson.get("reconstruction_contract")
    if not isinstance(reconstruction, dict) or reconstruction.get("mode") not in RECONSTRUCTION_MODES:
        raise ManifestError(f"{lesson_id}: invalid reconstruction_contract.mode")
    target = reconstruction.get("target")
    command = string_list(lesson_id, reconstruction.get("proof_command"), "reconstruction_contract.proof_command")
    if reconstruction["mode"] == "none":
        if target or command:
            raise ManifestError(f"{lesson_id}: reconstruction mode none cannot specify a target or proof")
    else:
        if not isinstance(target, str) or not target:
            raise ManifestError(f"{lesson_id}: required reconstruction needs a target")
        if lesson["publication"]["status"] == "published":
            resolve_repository_file(lesson_id, target, "reconstruction_contract.target")
            if not command:
                raise ManifestError(f"{lesson_id}: required reconstruction needs a proof command")
            validate_command_paths(lesson_id, command)


def validate_completion_contract(lesson_id: str, lesson: dict[str, Any]) -> None:
    completion = lesson.get("completion_contract")
    if not isinstance(completion, dict):
        raise ManifestError(f"{lesson_id}: completion_contract is required")
    milestones = string_list(lesson_id, completion.get("required_milestones"), "completion_contract.required_milestones")
    if lesson["publication"]["status"] == "published" and not milestones:
        raise ManifestError(f"{lesson_id}: published lesson needs completion milestones")


def validate_micro_world(lesson_id: str, micro_world: object) -> None:
    if not isinstance(micro_world, dict):
        raise ManifestError(f"{lesson_id}: micro_world decision is required")
    decision = micro_world.get("decision")
    score = micro_world.get("score")
    if decision not in MICRO_WORLD_DECISIONS:
        raise ManifestError(f"{lesson_id}: invalid micro_world decision")
    if not isinstance(score, int) or not -6 <= score <= 9:
        raise ManifestError(f"{lesson_id}: micro_world score must be between -6 and 9")
    for key in ("rationale", "fallback", "learner_action"):
        if not str(micro_world.get(key, "")).strip():
            raise ManifestError(f"{lesson_id}: micro_world {key} is required")
    if decision == "required" and score < 6:
        raise ManifestError(f"{lesson_id}: required micro-world score must be at least 6")
    if decision == "none" and score > 2:
        raise ManifestError(f"{lesson_id}: none micro-world score must be at most 2")
    if decision == "required" and not micro_world.get("component"):
        raise ManifestError(f"{lesson_id}: required micro-world needs a component")
    source = micro_world.get("scenario_source")
    if source is not None:
        resolve_repository_file(lesson_id, source, "micro_world.scenario_source")


def validate_graph(lessons: dict[str, Any]) -> None:
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


def lesson_config(lesson_id: str, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    lessons = (manifest or load_manifest())["lessons"]
    try:
        return lessons[lesson_id]
    except KeyError as error:
        raise ManifestError(f"Unknown lesson ID: {lesson_id}") from error


def publication_status(lesson_id: str, manifest: dict[str, Any] | None = None) -> str:
    return lesson_config(lesson_id, manifest)["publication"]["status"]


def active_lessons(manifest: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    lessons = (manifest or load_manifest())["lessons"]
    return {lesson_id: lesson for lesson_id, lesson in lessons.items() if lesson["publication"]["status"] == "published"}


def prerequisites_met(
    lesson_id: str,
    phases: dict[str, str],
    manifest: dict[str, Any] | None = None,
) -> bool:
    lesson = lesson_config(lesson_id, manifest)
    if lesson["publication"]["status"] != "published":
        return False
    return all(
        lesson_config(required, manifest)["publication"]["status"] == "published"
        and phases.get(required) == "learned"
        for required in lesson["requires"]
    )
