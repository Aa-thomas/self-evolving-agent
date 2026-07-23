"""Validate and query the evidence-first Project 1A learning-flow manifest."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path(__file__).with_name("learning-flow.json")
RESOURCE_CATALOG = Path(__file__).with_name("RESOURCES.md")
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
EPISODE_PATTERNS = {"foundation_build", "integration_build", "diagnostic_clinic", "experiment_lab", "operational_drill"}
FOUNDATION_BUILD_PRIMITIVES = {
    "0001-model-call-primitive",
    "0002-message-state-primitive",
    "0003-manual-tool-protocol",
    "0004-schema-validation",
    "0005-sandboxed-file-tools",
}
INTEGRATION_BUILD_LESSONS = {"0006-agent-loop-primitive"}
INTEGRATION_MODES = {"assemble", "extend", "repair", "reconstruct"}
DIAGNOSTIC_CLINIC_LESSONS = {"0007-trace-logger"}
DIAGNOSTIC_INTERVENTION_MODES = {"repair", "add_evidence", "add_regression"}
EXPERIMENT_LAB_LESSONS = {"0008-eval-runner"}
EXPERIMENT_MODES = {"construct", "compare", "ablate", "calibrate"}
OPERATIONAL_MODES = {"verify", "replay", "recover", "deploy", "rollback", "audit"}
STUDY_CONTRACT_VERSION = 1
STUDY_CONTEXT_CARDS = {"starting_artifacts", "target_artifacts", "proof_artifacts", "failure_contract"}
STUDY_PROMPT_KINDS = {"retrieval", "explanation", "judgment", "evidence", "uncertainty"}
STUDY_PLAN_FIELDS = {"target_function", "smallest_slice", "must_do", "must_not_do", "first_proof", "open_question"}
LECTURE_REFLECTION_FIELDS = {
    "feynman",
    "feynman_limit",
    "prediction_vs_evidence",
    "mental_model",
}
STUDY_PROMPT_IDS_BY_PATTERN = {
    "diagnostic_clinic": {"incident_facts", "next_evidence", "rejected_hypothesis"},
    "experiment_lab": {"behavioral_claim", "controlled_conditions", "failure_evidence"},
    "operational_drill": {"operational_context", "next_safe_action", "safe_stop_evidence"},
}


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
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 3:
        raise ManifestError("learning-flow manifest must use schema_version 3")
    lessons = manifest.get("lessons")
    if not isinstance(lessons, dict) or not lessons:
        raise ManifestError("learning-flow manifest must contain lessons")

    known = set(lessons)
    resource_urls = load_resource_catalog_urls()
    identity_numbers: set[int] = set()
    for position, (lesson_id, lesson) in enumerate(lessons.items(), start=1):
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
        validate_episode_contract(lesson_id, lesson)
        validate_study_contract(lesson_id, lesson)
        validate_identity_contract(lesson_id, lesson, position, identity_numbers)
        validate_lecture_contract(lesson_id, lesson)
        validate_reading_contract(lesson_id, lesson, resource_urls)

    validate_graph(lessons)


def load_resource_catalog_urls() -> set[str]:
    """Return exact Markdown link targets from the curated resource catalog."""
    try:
        source = RESOURCE_CATALOG.read_text(encoding="utf-8")
    except OSError as error:
        raise ManifestError(f"Could not read curriculum resource catalog: {error}") from error
    return {
        target.strip()
        for target in re.findall(r"\]\(([^)]+)\)", source)
        if target.strip()
    }


def validate_identity_contract(
    lesson_id: str,
    lesson: dict[str, Any],
    expected_number: int,
    seen_numbers: set[int],
) -> None:
    identity = lesson.get("identity")
    if not isinstance(identity, dict):
        raise ManifestError(f"{lesson_id}: identity must be an object")
    number = identity.get("number")
    if type(number) is not int:
        raise ManifestError(f"{lesson_id}: identity.number must be an integer")
    if number in seen_numbers:
        raise ManifestError(f"{lesson_id}: identity.number must be unique")
    if number != expected_number:
        raise ManifestError(
            f"{lesson_id}: identity.number must match curriculum order {expected_number}"
        )
    lesson_prefix = re.match(r"^(\d{4})-", lesson_id)
    if lesson_prefix is None or int(lesson_prefix.group(1)) != number:
        raise ManifestError(
            f"{lesson_id}: identity.number must match the lesson id prefix"
        )
    seen_numbers.add(number)
    for key in ("technical_name", "memorable_phrase"):
        require_text(lesson_id, identity, key, "identity")


def validate_lecture_contract(lesson_id: str, lesson: dict[str, Any]) -> None:
    contract = lesson.get("lecture_contract")
    if not isinstance(contract, dict):
        raise ManifestError(f"{lesson_id}: lecture_contract must be an object")
    require_text(lesson_id, contract, "central_thesis", "lecture_contract")

    obligations = contract.get("explanatory_obligations")
    if (
        not isinstance(obligations, list)
        or len(obligations) < 3
        or not all(isinstance(obligation, dict) for obligation in obligations)
    ):
        raise ManifestError(
            f"{lesson_id}: lecture_contract.explanatory_obligations needs at least 3 entries"
        )
    obligation_ids: set[str] = set()
    for obligation in obligations:
        for key in ("id", "claim"):
            require_text(
                lesson_id,
                obligation,
                key,
                "lecture_contract.explanatory_obligations",
            )
        obligation_ids.add(obligation["id"])
    if len(obligation_ids) != len(obligations):
        raise ManifestError(
            f"{lesson_id}: lecture_contract explanatory obligation ids must be unique"
        )

    worked_example = contract.get("worked_example")
    if not isinstance(worked_example, dict):
        raise ManifestError(f"{lesson_id}: lecture_contract.worked_example must be an object")
    resolve_repository_file(
        lesson_id,
        worked_example.get("artifact"),
        "lecture_contract.worked_example.artifact",
    )
    require_text_list(
        lesson_id,
        worked_example,
        "arc",
        "lecture_contract.worked_example",
        3,
    )

    coverage = contract.get("study_prompt_coverage")
    if not isinstance(coverage, dict):
        raise ManifestError(
            f"{lesson_id}: lecture_contract.study_prompt_coverage must be an object"
        )
    study = lesson["study_contract"]
    expected_coverage = {
        *(f"think.{prompt['id']}" for prompt in study["think"]["prompts"]),
        *(f"plan.{field}" for field in STUDY_PLAN_FIELDS),
        *(f"reflect.{field}" for field in LECTURE_REFLECTION_FIELDS),
    }
    if set(coverage) != expected_coverage:
        missing = sorted(expected_coverage - set(coverage))
        extra = sorted(set(coverage) - expected_coverage)
        raise ManifestError(
            f"{lesson_id}: lecture_contract.study_prompt_coverage must exactly cover "
            f"study prompts (missing={missing}, extra={extra})"
        )
    for prompt_id, references in coverage.items():
        reference_ids = string_list(
            lesson_id,
            references,
            f"lecture_contract.study_prompt_coverage.{prompt_id}",
        )
        if not reference_ids:
            raise ManifestError(
                f"{lesson_id}: lecture_contract.study_prompt_coverage.{prompt_id} "
                "must reference at least one explanatory obligation"
            )
        if len(set(reference_ids)) != len(reference_ids):
            raise ManifestError(
                f"{lesson_id}: lecture_contract.study_prompt_coverage.{prompt_id} "
                "must not repeat explanatory obligation ids"
            )
        unknown = set(reference_ids) - obligation_ids
        if unknown:
            raise ManifestError(
                f"{lesson_id}: lecture_contract.study_prompt_coverage.{prompt_id} "
                f"references unknown explanatory obligations: {sorted(unknown)}"
            )


def validate_reading_contract(
    lesson_id: str,
    lesson: dict[str, Any],
    resource_urls: set[str],
) -> None:
    contract = lesson.get("reading_contract")
    if not isinstance(contract, dict):
        raise ManifestError(f"{lesson_id}: reading_contract must be an object")
    primary = contract.get("primary")
    if not isinstance(primary, dict):
        raise ManifestError(f"{lesson_id}: reading_contract.primary must be an object")
    further = contract.get("further")
    if (
        not isinstance(further, list)
        or not 1 <= len(further) <= 3
        or not all(isinstance(entry, dict) for entry in further)
    ):
        raise ManifestError(
            f"{lesson_id}: reading_contract.further needs between 1 and 3 entries"
        )

    readings = [primary, *further]
    urls: list[str] = []
    for reading in readings:
        for key in ("title", "url", "why"):
            require_text(lesson_id, reading, key, "reading_contract entry")
        urls.append(reading["url"])
    if len(set(urls)) != len(urls):
        raise ManifestError(f"{lesson_id}: reading_contract URLs must be unique")
    unknown = set(urls) - resource_urls
    if unknown:
        raise ManifestError(
            f"{lesson_id}: reading_contract URLs must exactly match links in "
            f"curriculum/RESOURCES.md: {sorted(unknown)}"
        )


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


def require_text(lesson_id: str, contract: dict[str, Any], key: str, label: str) -> None:
    if not isinstance(contract.get(key), str) or not contract[key].strip():
        raise ManifestError(f"{lesson_id}: {label}.{key} must be non-empty text")


def require_text_list(
    lesson_id: str,
    contract: dict[str, Any],
    key: str,
    label: str,
    minimum: int,
) -> None:
    value = contract.get(key)
    if (
        not isinstance(value, list)
        or len(value) < minimum
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise ManifestError(f"{lesson_id}: {label}.{key} needs at least {minimum} non-empty entries")


def validate_episode_contract(lesson_id: str, lesson: dict[str, Any]) -> None:
    """Validate the pedagogical contract selected for a lesson episode.

    Episode patterns describe the teaching arc. They intentionally do not own
    publication, evidence, or study-state transitions, which remain the
    responsibility of the existing artifact and completion contracts.
    """
    pattern = lesson.get("episode_pattern")
    if lesson_id in FOUNDATION_BUILD_PRIMITIVES and pattern != "foundation_build":
        raise ManifestError(f"{lesson_id}: Project 1A primitive requires episode_pattern foundation_build")
    if lesson_id in INTEGRATION_BUILD_LESSONS and pattern != "integration_build":
        raise ManifestError(f"{lesson_id}: Project 1A integration lesson requires episode_pattern integration_build")
    if lesson_id in DIAGNOSTIC_CLINIC_LESSONS and pattern != "diagnostic_clinic":
        raise ManifestError(f"{lesson_id}: Project 1A diagnostic lesson requires episode_pattern diagnostic_clinic")
    if lesson_id in EXPERIMENT_LAB_LESSONS and pattern != "experiment_lab":
        raise ManifestError(f"{lesson_id}: Project 1A evaluation lesson requires episode_pattern experiment_lab")
    if pattern is None:
        return
    if pattern not in EPISODE_PATTERNS:
        raise ManifestError(f"{lesson_id}: unsupported episode_pattern {pattern!r}")

    contract = lesson.get("teaching_contract")
    if not isinstance(contract, dict):
        raise ManifestError(f"{lesson_id}: {pattern} requires a teaching_contract")
    if pattern == "foundation_build":
        validate_foundation_build_contract(lesson_id, lesson, contract)
    elif pattern == "integration_build":
        validate_integration_build_contract(lesson_id, lesson, contract)
    elif pattern == "diagnostic_clinic":
        validate_diagnostic_clinic_contract(lesson_id, contract)
    elif pattern == "experiment_lab":
        validate_experiment_lab_contract(lesson_id, contract)
    elif pattern == "operational_drill":
        validate_operational_drill_contract(lesson_id, contract)


def validate_foundation_build_contract(
    lesson_id: str,
    lesson: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    """Validate the beginner-first contract for an isolated Project 1A primitive."""
    starting = lesson["starting_artifacts"]
    if not any(starting[key] for key in ("source_files", "symbols", "tests", "scenario_sources")):
        raise ManifestError(f"{lesson_id}: foundation_build requires an inspectable starting artifact")
    for key in ("concrete_problem", "first_principle", "prediction_prompt", "artifact_inspection_prompt", "transfer_prompt"):
        require_text(lesson_id, contract, key, "teaching_contract")
    require_text_list(lesson_id, contract, "worked_walkthrough", "teaching_contract", 2)

    boundary = contract.get("boundary_and_invariant")
    if not isinstance(boundary, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.boundary_and_invariant must be an object")
    for key in ("boundary", "invariant"):
        require_text(lesson_id, boundary, key, "teaching_contract.boundary_and_invariant")

    tension = contract.get("design_tension")
    if not isinstance(tension, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.design_tension must be an object")
    require_text_list(lesson_id, tension, "options", "teaching_contract.design_tension", 2)
    require_text(lesson_id, tension, "decision_rule", "teaching_contract.design_tension")

    scope = contract.get("implementation_scope")
    if not isinstance(scope, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.implementation_scope must be an object")
    require_text_list(lesson_id, scope, "build", "teaching_contract.implementation_scope", 1)
    require_text_list(lesson_id, scope, "leave_unchanged", "teaching_contract.implementation_scope", 1)

    proof = contract.get("proof_interpretation")
    if not isinstance(proof, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.proof_interpretation must be an object")
    for key in ("establishes", "does_not_establish"):
        require_text(lesson_id, proof, key, "teaching_contract.proof_interpretation")


def require_component_entries(
    lesson_id: str,
    value: object,
    label: str,
    required_keys: tuple[str, ...],
) -> None:
    if not isinstance(value, list) or len(value) < 2 or not all(isinstance(entry, dict) for entry in value):
        raise ManifestError(f"{lesson_id}: {label} needs at least two component entries")
    for entry in value:
        for key in required_keys:
            require_text(lesson_id, entry, key, label)


def validate_integration_build_contract(
    lesson_id: str,
    lesson: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    """Validate a reusable contract for composing multiple real components."""
    for key in (
        "system_problem",
        "integration_responsibility",
        "prediction_prompt",
        "artifact_inspection_prompt",
        "causal_explanation_prompt",
        "transfer_prompt",
    ):
        require_text(lesson_id, contract, key, "teaching_contract")

    bridge = contract.get("prerequisite_bridge")
    if not isinstance(bridge, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.prerequisite_bridge must be an object")
    require_component_entries(
        lesson_id,
        bridge.get("existing_components"),
        "teaching_contract.prerequisite_bridge.existing_components",
        ("component", "already_guarantees", "does_not_guarantee"),
    )

    model = contract.get("system_model")
    if not isinstance(model, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.system_model must be an object")
    require_component_entries(
        lesson_id,
        model.get("components"),
        "teaching_contract.system_model.components",
        ("component", "input", "output_or_transition", "responsibility"),
    )
    require_text(lesson_id, model, "system_invariant", "teaching_contract.system_model")

    trajectories = contract.get("worked_trajectories")
    if not isinstance(trajectories, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.worked_trajectories must be an object")
    for key in ("success_path", "failure_or_edge_path"):
        require_text_list(lesson_id, trajectories, key, "teaching_contract.worked_trajectories", 2)
    require_text(lesson_id, trajectories, "comparison_question", "teaching_contract.worked_trajectories")

    tension = contract.get("design_tension")
    if not isinstance(tension, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.design_tension must be an object")
    require_text_list(lesson_id, tension, "options", "teaching_contract.design_tension", 2)
    require_text(lesson_id, tension, "decision_rule", "teaching_contract.design_tension")

    strategy = contract.get("intervention_strategy")
    if not isinstance(strategy, dict) or strategy.get("mode") not in INTEGRATION_MODES:
        raise ManifestError(f"{lesson_id}: teaching_contract.intervention_strategy.mode is invalid")
    for key, minimum in (("build_order", 2), ("learner_owns", 1), ("leave_unchanged", 1), ("forbidden_shortcuts", 1)):
        require_text_list(lesson_id, strategy, key, "teaching_contract.intervention_strategy", minimum)
    mode = strategy["mode"]
    if mode == "reconstruct":
        require_text(lesson_id, strategy, "scaffold", "teaching_contract.intervention_strategy")
        if lesson["lesson_type"] != "reconstruction_lab":
            raise ManifestError(f"{lesson_id}: integration reconstruct mode requires lesson_type reconstruction_lab")
        if lesson["reconstruction_contract"]["mode"] == "none":
            raise ManifestError(f"{lesson_id}: integration reconstruct mode requires a reconstruction contract")
    elif "scaffold" in strategy and strategy["scaffold"] is not None:
        raise ManifestError(f"{lesson_id}: only integration reconstruct mode may specify a scaffold")

    proof = contract.get("integration_proof")
    if not isinstance(proof, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.integration_proof must be an object")
    require_text_list(lesson_id, proof, "required_evidence", "teaching_contract.integration_proof", 2)
    for key in ("establishes", "does_not_establish"):
        require_text(lesson_id, proof, key, "teaching_contract.integration_proof")


def validate_diagnostic_clinic_contract(lesson_id: str, contract: dict[str, Any]) -> None:
    """Validate a reusable evidence-first diagnosis and targeted-repair episode."""
    incident = contract.get("incident")
    if not isinstance(incident, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.incident must be an object")
    for key in ("symptom", "impact"):
        require_text(lesson_id, incident, key, "teaching_contract.incident")
    require_text_list(lesson_id, incident, "available_evidence", "teaching_contract.incident", 2)

    model = contract.get("diagnostic_model")
    if not isinstance(model, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.diagnostic_model must be an object")
    for key in ("first_principle", "ownership_rule"):
        require_text(lesson_id, model, key, "teaching_contract.diagnostic_model")
    require_component_entries(
        lesson_id,
        model.get("candidate_causes"),
        "teaching_contract.diagnostic_model.candidate_causes",
        ("cause", "would_explain", "distinguishing_evidence"),
    )

    investigation = contract.get("worked_investigation")
    if not isinstance(investigation, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.worked_investigation must be an object")
    for key in ("observations", "elimination_steps"):
        require_text_list(lesson_id, investigation, key, "teaching_contract.worked_investigation", 2)
    for key in ("current_conclusion", "confidence_limit"):
        require_text(lesson_id, investigation, key, "teaching_contract.worked_investigation")

    for key in ("prediction_prompt", "artifact_inspection_sequence", "diagnosis_commitment", "intervention_strategy", "diagnostic_proof", "causal_explanation_prompt", "transfer_prompt"):
        if key not in contract:
            raise ManifestError(f"{lesson_id}: teaching_contract.{key} is required")
    require_text(lesson_id, contract, "prediction_prompt", "teaching_contract")
    require_text(lesson_id, contract, "causal_explanation_prompt", "teaching_contract")
    require_text(lesson_id, contract, "transfer_prompt", "teaching_contract")

    inspection = contract["artifact_inspection_sequence"]
    if not isinstance(inspection, list) or len(inspection) < 2 or not all(isinstance(entry, dict) for entry in inspection):
        raise ManifestError(f"{lesson_id}: teaching_contract.artifact_inspection_sequence needs at least two entries")
    for entry in inspection:
        for key in ("artifact", "question", "fact_established"):
            require_text(lesson_id, entry, key, "teaching_contract.artifact_inspection_sequence")

    commitment = contract["diagnosis_commitment"]
    if not isinstance(commitment, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.diagnosis_commitment must be an object")
    require_text_list(lesson_id, commitment, "required_claims", "teaching_contract.diagnosis_commitment", 4)
    require_text(lesson_id, commitment, "ambiguity_rule", "teaching_contract.diagnosis_commitment")

    strategy = contract["intervention_strategy"]
    if not isinstance(strategy, dict) or strategy.get("mode") not in DIAGNOSTIC_INTERVENTION_MODES:
        raise ManifestError(f"{lesson_id}: teaching_contract.intervention_strategy.mode is invalid")
    for key in ("smallest_safe_intervention", "regression_target"):
        require_text(lesson_id, strategy, key, "teaching_contract.intervention_strategy")
    require_text_list(lesson_id, strategy, "leave_unchanged", "teaching_contract.intervention_strategy", 1)
    require_text_list(lesson_id, strategy, "forbidden_shortcuts", "teaching_contract.intervention_strategy", 2)

    proof = contract["diagnostic_proof"]
    if not isinstance(proof, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.diagnostic_proof must be an object")
    require_text_list(lesson_id, proof, "required_evidence", "teaching_contract.diagnostic_proof", 3)
    for key in ("establishes", "does_not_establish"):
        require_text(lesson_id, proof, key, "teaching_contract.diagnostic_proof")


def validate_experiment_lab_contract(lesson_id: str, contract: dict[str, Any]) -> None:
    """Validate a repeatable behavioral measurement and interpretation episode."""
    require_text(lesson_id, contract, "decision_question", "teaching_contract")

    claim = contract.get("behavioral_claim")
    if not isinstance(claim, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.behavioral_claim must be an object")
    for key in ("hypothesis", "scope"):
        require_text(lesson_id, claim, key, "teaching_contract.behavioral_claim")
    require_text_list(lesson_id, claim, "expected_failure_modes", "teaching_contract.behavioral_claim", 1)

    baseline = contract.get("baseline")
    if not isinstance(baseline, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.baseline must be an object")
    require_text_list(lesson_id, baseline, "existing_evidence", "teaching_contract.baseline", 2)
    for key in ("what_baseline_establishes", "what_baseline_does_not_establish"):
        require_text(lesson_id, baseline, key, "teaching_contract.baseline")

    measurement = contract.get("measurement_model")
    if not isinstance(measurement, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.measurement_model must be an object")
    require_text(lesson_id, measurement, "unit_of_evaluation", "teaching_contract.measurement_model")
    cases = measurement.get("cases")
    if not isinstance(cases, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.measurement_model.cases must be an object")
    for key in ("source", "inclusion_rule"):
        require_text(lesson_id, cases, key, "teaching_contract.measurement_model.cases")
    require_text_list(lesson_id, cases, "minimum_coverage", "teaching_contract.measurement_model.cases", 2)
    outcome = measurement.get("outcome_contract")
    if not isinstance(outcome, list) or len(outcome) < 2 or not all(isinstance(entry, dict) for entry in outcome):
        raise ManifestError(f"{lesson_id}: teaching_contract.measurement_model.outcome_contract needs at least two outcomes")
    for entry in outcome:
        for key in ("outcome", "pass_condition", "failure_evidence"):
            require_text(lesson_id, entry, key, "teaching_contract.measurement_model.outcome_contract")
    require_text_list(lesson_id, measurement, "controlled_conditions", "teaching_contract.measurement_model", 2)
    require_text_list(lesson_id, measurement, "confounders", "teaching_contract.measurement_model", 1)

    comparison = contract.get("worked_comparison")
    if not isinstance(comparison, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.worked_comparison must be an object")
    for key in ("baseline_run", "measured_run"):
        require_text_list(lesson_id, comparison, key, "teaching_contract.worked_comparison", 2)
    require_text(lesson_id, comparison, "interpretation", "teaching_contract.worked_comparison")

    for key in ("prediction_prompt", "artifact_inspection_prompt", "interpretation_prompt", "transfer_prompt"):
        require_text(lesson_id, contract, key, "teaching_contract")

    strategy = contract.get("experiment_strategy")
    if not isinstance(strategy, dict) or strategy.get("mode") not in EXPERIMENT_MODES:
        raise ManifestError(f"{lesson_id}: teaching_contract.experiment_strategy.mode is invalid")
    require_text(lesson_id, strategy, "intervention_or_measurement_change", "teaching_contract.experiment_strategy")
    for key, minimum in (("keep_constant", 1), ("learner_owns", 1), ("leave_unchanged", 1), ("forbidden_shortcuts", 3)):
        require_text_list(lesson_id, strategy, key, "teaching_contract.experiment_strategy", minimum)

    proof = contract.get("measurement_proof")
    if not isinstance(proof, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.measurement_proof must be an object")
    require_text_list(lesson_id, proof, "required_evidence", "teaching_contract.measurement_proof", 4)
    for key in ("establishes", "does_not_establish"):
        require_text(lesson_id, proof, key, "teaching_contract.measurement_proof")


def validate_operational_drill_contract(lesson_id: str, contract: dict[str, Any]) -> None:
    """Validate a constrained, evidence-backed operating procedure episode."""
    context = contract.get("operational_context")
    if not isinstance(context, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.operational_context must be an object")
    for key in ("objective", "trigger", "impact_if_wrong"):
        require_text(lesson_id, context, key, "teaching_contract.operational_context")
    require_text_list(lesson_id, context, "constraints", "teaching_contract.operational_context", 1)

    model = contract.get("operating_model")
    if not isinstance(model, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.operating_model must be an object")
    require_text(lesson_id, model, "first_principle", "teaching_contract.operating_model")
    boundaries = model.get("system_boundaries")
    if not isinstance(boundaries, list) or len(boundaries) < 2 or not all(isinstance(entry, dict) for entry in boundaries):
        raise ManifestError(f"{lesson_id}: teaching_contract.operating_model.system_boundaries needs at least two entries")
    for entry in boundaries:
        for key in ("boundary", "authority", "signal", "unsafe_assumption"):
            require_text(lesson_id, entry, key, "teaching_contract.operating_model.system_boundaries")

    readiness = contract.get("readiness_check")
    if not isinstance(readiness, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.readiness_check must be an object")
    require_text_list(lesson_id, readiness, "required_starting_artifacts", "teaching_contract.readiness_check", 1)
    require_text_list(lesson_id, readiness, "preflight_checks", "teaching_contract.readiness_check", 2)
    require_text_list(lesson_id, readiness, "no_go_conditions", "teaching_contract.readiness_check", 1)

    worked_run = contract.get("worked_run")
    if not isinstance(worked_run, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.worked_run must be an object")
    for key in ("normal_path", "degraded_or_failure_path"):
        require_text_list(lesson_id, worked_run, key, "teaching_contract.worked_run", 2)
    require_text(lesson_id, worked_run, "decision_point", "teaching_contract.worked_run")

    require_text(lesson_id, contract, "prediction_prompt", "teaching_contract")
    execution = contract.get("execution_contract")
    if not isinstance(execution, dict) or execution.get("mode") not in OPERATIONAL_MODES:
        raise ManifestError(f"{lesson_id}: teaching_contract.execution_contract.mode is invalid")
    procedure = execution.get("procedure")
    if not isinstance(procedure, list) or len(procedure) < 2 or not all(isinstance(entry, dict) for entry in procedure):
        raise ManifestError(f"{lesson_id}: teaching_contract.execution_contract.procedure needs at least two steps")
    for entry in procedure:
        for key in ("action", "expected_signal", "record"):
            require_text(lesson_id, entry, key, "teaching_contract.execution_contract.procedure")
    require_text(lesson_id, execution, "authority_boundary", "teaching_contract.execution_contract")
    require_text_list(lesson_id, execution, "guardrails", "teaching_contract.execution_contract", 1)
    require_text_list(lesson_id, execution, "forbidden_shortcuts", "teaching_contract.execution_contract", 2)

    proof = contract.get("operational_proof")
    if not isinstance(proof, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.operational_proof must be an object")
    require_text_list(lesson_id, proof, "required_evidence", "teaching_contract.operational_proof", 4)
    for key in ("establishes", "does_not_establish"):
        require_text(lesson_id, proof, key, "teaching_contract.operational_proof")

    handoff = contract.get("handoff_or_postmortem")
    if not isinstance(handoff, dict):
        raise ManifestError(f"{lesson_id}: teaching_contract.handoff_or_postmortem must be an object")
    require_text_list(lesson_id, handoff, "required_record", "teaching_contract.handoff_or_postmortem", 1)
    require_text(lesson_id, handoff, "explanation_prompt", "teaching_contract.handoff_or_postmortem")
    require_text(lesson_id, contract, "transfer_prompt", "teaching_contract")


def validate_study_contract(lesson_id: str, lesson: dict[str, Any]) -> None:
    """Validate workspace prompts without turning notes into completion evidence."""
    contract = lesson.get("study_contract")
    if lesson.get("episode_pattern") in EPISODE_PATTERNS and not isinstance(contract, dict):
        raise ManifestError(f"{lesson_id}: selected episode pattern requires a study_contract")
    if contract is None:
        return
    if not isinstance(contract, dict) or contract.get("version") != STUDY_CONTRACT_VERSION:
        raise ManifestError(f"{lesson_id}: study_contract.version must be {STUDY_CONTRACT_VERSION}")
    require_text(lesson_id, contract, "objective", "study_contract")
    cards = string_list(lesson_id, contract.get("context_cards"), "study_contract.context_cards")
    if not cards or not set(cards) <= STUDY_CONTEXT_CARDS:
        raise ManifestError(f"{lesson_id}: study_contract.context_cards must use known artifact contracts")

    think = contract.get("think")
    if not isinstance(think, dict):
        raise ManifestError(f"{lesson_id}: study_contract.think must be an object")
    jot = think.get("jot_notes")
    if not isinstance(jot, dict):
        raise ManifestError(f"{lesson_id}: study_contract.think.jot_notes must be an object")
    for key in ("label", "placeholder"):
        require_text(lesson_id, jot, key, "study_contract.think.jot_notes")
    prompts = think.get("prompts")
    if not isinstance(prompts, list) or len(prompts) != 3 or not all(isinstance(prompt, dict) for prompt in prompts):
        raise ManifestError(f"{lesson_id}: study_contract.think.prompts needs exactly three prompts")
    prompt_ids: set[str] = set()
    for prompt in prompts:
        for key in ("id", "label", "prompt"):
            require_text(lesson_id, prompt, key, "study_contract.think.prompts")
        if prompt["kind"] not in STUDY_PROMPT_KINDS:
            raise ManifestError(f"{lesson_id}: study_contract.think prompt kind is invalid")
        prompt_ids.add(prompt["id"])
    if len(prompt_ids) != len(prompts):
        raise ManifestError(f"{lesson_id}: study_contract.think prompt ids must be unique")
    required_prompt_ids = STUDY_PROMPT_IDS_BY_PATTERN.get(lesson.get("episode_pattern"))
    if required_prompt_ids and prompt_ids != required_prompt_ids:
        raise ManifestError(f"{lesson_id}: study_contract.think prompts must match the {lesson['episode_pattern']} workspace")

    plan = contract.get("plan")
    if not isinstance(plan, dict):
        raise ManifestError(f"{lesson_id}: study_contract.plan must be an object")
    require_text(lesson_id, plan, "intro", "study_contract.plan")
    fields = plan.get("fields")
    if not isinstance(fields, dict) or set(fields) != STUDY_PLAN_FIELDS:
        raise ManifestError(f"{lesson_id}: study_contract.plan.fields must configure the existing handoff fields")
    for field in fields.values():
        if not isinstance(field, dict):
            raise ManifestError(f"{lesson_id}: study_contract.plan fields must be objects")
        for key in ("label", "placeholder"):
            require_text(lesson_id, field, key, "study_contract.plan.fields")

    reflect = contract.get("reflect")
    if not isinstance(reflect, dict):
        raise ManifestError(f"{lesson_id}: study_contract.reflect must be an object")
    for section, keys in {
        "feynman": ("label", "subject", "placeholder"),
        "feynman_limit": ("label", "prompt"),
        "prediction_vs_evidence": ("label", "prompt"),
        "mental_model": ("label", "prompt"),
        "next_step": ("label", "prompt"),
    }.items():
        value = reflect.get(section)
        if not isinstance(value, dict):
            raise ManifestError(f"{lesson_id}: study_contract.reflect.{section} must be an object")
        for key in keys:
            require_text(lesson_id, value, key, f"study_contract.reflect.{section}")


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
