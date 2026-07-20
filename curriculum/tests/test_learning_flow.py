import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from learning_flow import ManifestError, load_manifest, prerequisites_met, validate_manifest
from lint_lessons import lint_lesson


def published_agent_loop():
    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0006-agent-loop-primitive"]
    lesson["publication"] = {"status": "published", "reason": None}
    return manifest, lesson


def test_project_manifest_uses_evidence_first_schema_and_locks_unbuilt_work():
    manifest = load_manifest()

    assert manifest["schema_version"] == 2
    assert manifest["lessons"]["0006-agent-loop-primitive"]["starting_artifacts"]["source_files"]
    assert manifest["lessons"]["0006-agent-loop-primitive"]["target_artifacts"]["source_files"]
    assert manifest["lessons"]["0007-trace-logger"]["publication"]["status"] == "locked"
    assert manifest["lessons"]["0008-eval-runner"]["unlocks"] == []


def test_published_lesson_requires_target():
    manifest, lesson = published_agent_loop()
    lesson["target_artifacts"]["source_files"] = []
    lesson["target_artifacts"]["tests"] = []

    with pytest.raises(ManifestError, match="implementation targets"):
        validate_manifest(manifest)


def test_published_lesson_requires_proof():
    manifest, lesson = published_agent_loop()
    lesson["proof_artifacts"]["proof_command"] = []

    with pytest.raises(ManifestError, match="proof_artifacts.proof_command"):
        validate_manifest(manifest)


def test_locked_lesson_cannot_unlock_dependent():
    manifest = deepcopy(load_manifest())
    manifest["lessons"]["0007-trace-logger"]["unlocks"] = ["0008-eval-runner"]

    with pytest.raises(ManifestError, match="cannot unlock"):
        validate_manifest(manifest)


def test_prerequisites_require_demonstrated_learning_and_publication():
    manifest = load_manifest()
    phases = {
        "0003-manual-tool-protocol": "learned",
        "0004-schema-validation": "learned",
        "0005-sandboxed-file-tools": "learned",
    }
    assert not prerequisites_met("0006-agent-loop-primitive", phases, manifest)


def test_scenario_sources_resolve_and_include_causal_artifacts():
    scenarios = json.loads(
        (Path(__file__).resolve().parents[1] / "traces" / "agent-loop-scenarios.json").read_text()
    )["scenarios"]
    required = {
        "initial_messages", "assistant_output", "parse_result", "validation_result",
        "protocol_registry", "runtime_handlers", "harness_decision", "tool_result",
        "next_messages", "exit_reason", "source_test", "source_trace", "questions",
    }
    root = Path(__file__).resolve().parents[2]
    for scenario in scenarios:
        assert required <= scenario.keys()
        assert (root / scenario["source_test"].split("::", 1)[0]).is_file()
        assert (root / scenario["source_trace"]).is_file()


def test_answer_positions_are_not_degenerate():
    scenarios = json.loads(
        (Path(__file__).resolve().parents[1] / "traces" / "agent-loop-scenarios.json").read_text()
    )["scenarios"]
    positions = [question["choices"].index(question["answer"]) for scenario in scenarios for question in scenario["questions"]]
    assert len(set(positions)) > 1


def test_case_set_meets_minimum_size():
    manifest, lesson = published_agent_loop()
    lesson["practice_contract"]["minimum_cases"] = 4

    with pytest.raises(ManifestError, match="at least 5 cases"):
        validate_manifest(manifest)


def test_required_reconstruction_has_proof():
    manifest, lesson = published_agent_loop()
    lesson["reconstruction_contract"]["proof_command"] = []

    with pytest.raises(ManifestError, match="reconstruction needs a proof"):
        validate_manifest(manifest)


def test_lesson_identifiers_match_bound_source_and_error_codes_do_not_drift():
    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0005-sandboxed-file-tools"]
    lesson["publication"] = {"status": "published", "reason": None}
    source = Path(__file__).resolve().parents[1] / "lessons" / "0005-sandboxed-file-tools.html"

    errors = lint_lesson("0005-sandboxed-file-tools", lesson, source)

    assert any("PATH_OUTSIDE_SANDBOX" in error for error in errors)


def test_prediction_answer_is_not_pre_revealed(tmp_path):
    _, lesson = published_agent_loop()
    source = tmp_path / "0006-agent-loop-primitive.html"
    source.write_text('<button data-prediction-answer>answer</button><button data-prediction-submit>commit</button>', encoding="utf-8")

    errors = lint_lesson("0006-agent-loop-primitive", lesson, source)

    assert any("prediction answer appears before commitment" in error for error in errors)


def test_linter_requires_declared_starting_symbols_to_exist(tmp_path):
    _, lesson = published_agent_loop()
    lesson["starting_artifacts"]["symbols"] = ["NotARealStartingSymbol"]
    source = tmp_path / "0006-agent-loop-primitive.html"
    source.write_text("<main></main>", encoding="utf-8")

    errors = lint_lesson("0006-agent-loop-primitive", lesson, source)

    assert any("NotARealStartingSymbol" in error for error in errors)
