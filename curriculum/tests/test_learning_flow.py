import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from learning_flow import (
    ManifestError,
    load_manifest,
    prerequisites_met,
    validate_identity_contract,
    validate_manifest,
    validate_operational_drill_contract,
    validate_study_contract,
)
from lint_lessons import lint_lesson


def published_agent_loop():
    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0006-agent-loop-primitive"]
    lesson["publication"] = {"status": "published", "reason": None}
    return manifest, lesson


def operational_drill_contract():
    return {
        "operational_context": {
            "objective": "Replay a saved trace and record its outcome.",
            "trigger": "A failed run needs operational review.",
            "impact_if_wrong": "An unsupported diagnosis could cause an unsafe change.",
            "constraints": ["Use only the approved replay environment."],
        },
        "operating_model": {
            "first_principle": "Operational work requires authorized actions and evidence.",
            "system_boundaries": [
                {"boundary": "replay command", "authority": "operator", "signal": "exit status", "unsafe_assumption": "A command success explains the trace."},
                {"boundary": "incident escalation", "authority": "reviewer", "signal": "no-go condition", "unsafe_assumption": "The operator may change production state."},
            ],
        },
        "readiness_check": {
            "required_starting_artifacts": ["A saved trace."],
            "preflight_checks": ["Trace exists.", "Replay environment is approved."],
            "no_go_conditions": ["Trace is corrupt."],
        },
        "worked_run": {
            "normal_path": ["Replay the trace.", "Record the result."],
            "degraded_or_failure_path": ["Detect a corrupt trace.", "Stop and escalate."],
            "decision_point": "The replay result determines whether to continue.",
        },
        "prediction_prompt": "Predict the next safe action.",
        "execution_contract": {
            "mode": "replay",
            "procedure": [
                {"action": "Check trace", "expected_signal": "File exists", "record": "Preflight note"},
                {"action": "Replay trace", "expected_signal": "Replay output", "record": "Replay result"},
            ],
            "authority_boundary": "Escalate any production change.",
            "guardrails": ["Do not mutate the original trace."],
            "forbidden_shortcuts": ["Skip preflight.", "Treat replay as a fix."],
        },
        "operational_proof": {
            "required_evidence": ["Preflight", "Procedure output", "Replay record", "Verification or safe stop"],
            "establishes": "The saved trace was replayed under the procedure.",
            "does_not_establish": "The production system is repaired.",
        },
        "handoff_or_postmortem": {
            "required_record": ["Operator handoff."],
            "explanation_prompt": "Explain the decision and evidence.",
        },
        "transfer_prompt": "Choose a response to a changed signal.",
    }


def test_project_manifest_uses_evidence_first_schema_and_publishes_buildable_work():
    manifest = load_manifest()

    assert manifest["schema_version"] == 3
    assert manifest["lessons"]["0006-agent-loop-primitive"]["starting_artifacts"]["source_files"]
    assert manifest["lessons"]["0006-agent-loop-primitive"]["target_artifacts"]["source_files"]
    trace_logger = manifest["lessons"]["0007-trace-logger"]
    eval_runner = manifest["lessons"]["0008-eval-runner"]
    assert trace_logger["publication"]["status"] == "published"
    assert trace_logger["target_artifacts"]["source_files"]
    assert trace_logger["proof_artifacts"]["proof_command"]
    assert eval_runner["publication"]["status"] == "published"
    assert eval_runner["target_artifacts"]["tests"]


def test_manifest_requires_schema_version_3():
    manifest = deepcopy(load_manifest())
    manifest["schema_version"] = 2

    with pytest.raises(ManifestError, match="schema_version 3"):
        validate_manifest(manifest)


@pytest.mark.parametrize(
    ("contract_name", "error"),
    [
        ("identity", "identity must be an object"),
        ("lecture_contract", "lecture_contract must be an object"),
        ("reading_contract", "reading_contract must be an object"),
    ],
)
def test_manifest_requires_identity_lecture_and_reading_contracts(contract_name, error):
    manifest = deepcopy(load_manifest())
    manifest["lessons"]["0001-model-call-primitive"].pop(contract_name)

    with pytest.raises(ManifestError, match=error):
        validate_manifest(manifest)


def test_lessons_have_ordered_unique_memorable_identities():
    manifest = load_manifest()

    for number, lesson in enumerate(manifest["lessons"].values(), start=1):
        assert lesson["identity"]["number"] == number
        assert lesson["identity"]["technical_name"].strip()
        assert lesson["identity"]["memorable_phrase"].strip()

    duplicate = deepcopy(manifest)
    lessons = list(duplicate["lessons"].values())
    lessons[1]["identity"]["number"] = lessons[0]["identity"]["number"]
    with pytest.raises(ManifestError, match=r"identity\.number must be unique"):
        validate_manifest(duplicate)

    out_of_order = deepcopy(manifest)
    first_lesson = next(iter(out_of_order["lessons"].values()))
    first_lesson["identity"]["number"] = 99
    with pytest.raises(ManifestError, match="must match curriculum order 1"):
        validate_manifest(out_of_order)


def test_lesson_identity_number_matches_lesson_id_prefix():
    lesson = deepcopy(
        load_manifest()["lessons"]["0001-model-call-primitive"]
    )

    with pytest.raises(ManifestError, match="must match the lesson id prefix"):
        validate_identity_contract(
            "0002-model-call-primitive",
            lesson,
            expected_number=1,
            seen_numbers=set(),
        )


@pytest.mark.parametrize("key", ["technical_name", "memorable_phrase"])
def test_lesson_identity_requires_technical_and_memorable_names(key):
    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0001-model-call-primitive"]
    lesson["identity"][key] = " "

    with pytest.raises(ManifestError, match=rf"identity\.{key}"):
        validate_manifest(manifest)


def test_lecture_contract_requires_thesis_and_three_unique_obligations():
    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0001-model-call-primitive"]
    lesson["lecture_contract"]["central_thesis"] = ""

    with pytest.raises(ManifestError, match=r"lecture_contract\.central_thesis"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    obligations = manifest["lessons"]["0001-model-call-primitive"]["lecture_contract"][
        "explanatory_obligations"
    ]
    del obligations[2:]

    with pytest.raises(ManifestError, match="needs at least 3 entries"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    obligations = manifest["lessons"]["0001-model-call-primitive"]["lecture_contract"][
        "explanatory_obligations"
    ]
    obligations[1]["id"] = obligations[0]["id"]

    with pytest.raises(ManifestError, match="obligation ids must be unique"):
        validate_manifest(manifest)


def test_lecture_worked_example_requires_real_artifact_and_three_step_arc():
    manifest = deepcopy(load_manifest())
    worked = manifest["lessons"]["0001-model-call-primitive"]["lecture_contract"][
        "worked_example"
    ]
    worked["artifact"] = "curriculum/not-a-real-artifact.py"

    with pytest.raises(ManifestError, match=r"worked_example\.artifact does not exist"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    worked = manifest["lessons"]["0001-model-call-primitive"]["lecture_contract"][
        "worked_example"
    ]
    worked["arc"] = ["start", "finish"]

    with pytest.raises(ManifestError, match=r"worked_example\.arc needs at least 3"):
        validate_manifest(manifest)


def test_lecture_coverage_exactly_maps_think_plan_and_conceptual_reflection():
    manifest = load_manifest()
    lesson = manifest["lessons"]["0001-model-call-primitive"]
    expected = {
        *(f"think.{prompt['id']}" for prompt in lesson["study_contract"]["think"]["prompts"]),
        *(f"plan.{field}" for field in {
            "target_function",
            "smallest_slice",
            "must_do",
            "must_not_do",
            "first_proof",
            "open_question",
        }),
        "reflect.feynman",
        "reflect.feynman_limit",
        "reflect.prediction_vs_evidence",
        "reflect.mental_model",
    }

    assert set(lesson["lecture_contract"]["study_prompt_coverage"]) == expected

    missing = deepcopy(manifest)
    missing_coverage = missing["lessons"]["0001-model-call-primitive"]["lecture_contract"][
        "study_prompt_coverage"
    ]
    missing_coverage.pop("plan.first_proof")
    with pytest.raises(ManifestError, match="must exactly cover study prompts"):
        validate_manifest(missing)

    extra = deepcopy(manifest)
    extra_coverage = extra["lessons"]["0001-model-call-primitive"]["lecture_contract"][
        "study_prompt_coverage"
    ]
    extra_coverage["reflect.next_step"] = [next(iter(extra_coverage.values()))[0]]
    with pytest.raises(ManifestError, match="must exactly cover study prompts"):
        validate_manifest(extra)


def test_lecture_coverage_requires_known_non_repeated_obligations():
    manifest = deepcopy(load_manifest())
    coverage = manifest["lessons"]["0001-model-call-primitive"]["lecture_contract"][
        "study_prompt_coverage"
    ]
    coverage["plan.first_proof"] = []

    with pytest.raises(ManifestError, match="must reference at least one"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    coverage = manifest["lessons"]["0001-model-call-primitive"]["lecture_contract"][
        "study_prompt_coverage"
    ]
    coverage["plan.first_proof"] = ["not-an-obligation"]

    with pytest.raises(ManifestError, match="references unknown explanatory obligations"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    coverage = manifest["lessons"]["0001-model-call-primitive"]["lecture_contract"][
        "study_prompt_coverage"
    ]
    coverage["plan.first_proof"] = [coverage["plan.first_proof"][0]] * 2

    with pytest.raises(ManifestError, match="must not repeat"):
        validate_manifest(manifest)


def test_reading_contract_requires_primary_and_one_to_three_further_readings():
    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0001-model-call-primitive"]
    lesson["reading_contract"]["primary"] = None

    with pytest.raises(ManifestError, match=r"reading_contract\.primary"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    further = manifest["lessons"]["0001-model-call-primitive"]["reading_contract"]["further"]
    further.clear()

    with pytest.raises(ManifestError, match="between 1 and 3 entries"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    further = manifest["lessons"]["0001-model-call-primitive"]["reading_contract"]["further"]
    further.extend(deepcopy(further[:1]) * 3)

    with pytest.raises(ManifestError, match="between 1 and 3 entries"):
        validate_manifest(manifest)


@pytest.mark.parametrize("key", ["title", "url", "why"])
def test_reading_entries_require_title_url_and_lesson_specific_annotation(key):
    manifest = deepcopy(load_manifest())
    primary = manifest["lessons"]["0001-model-call-primitive"]["reading_contract"]["primary"]
    primary[key] = ""

    with pytest.raises(ManifestError, match=rf"reading_contract entry\.{key}"):
        validate_manifest(manifest)


def test_reading_urls_are_unique_and_exactly_curated_in_resources():
    manifest = deepcopy(load_manifest())
    reading = manifest["lessons"]["0001-model-call-primitive"]["reading_contract"]
    reading["further"][0]["url"] = reading["primary"]["url"]

    with pytest.raises(ManifestError, match="URLs must be unique"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    reading = manifest["lessons"]["0001-model-call-primitive"]["reading_contract"]
    reading["primary"]["url"] = f"{reading['primary']['url']}?uncurated=1"

    with pytest.raises(ManifestError, match=r"exactly match links in curriculum/RESOURCES\.md"):
        validate_manifest(manifest)


def test_project_1a_primitives_use_the_foundation_build_episode_contract():
    manifest = load_manifest()
    primitive_ids = (
        "0001-model-call-primitive",
        "0002-message-state-primitive",
        "0003-manual-tool-protocol",
        "0004-schema-validation",
        "0005-sandboxed-file-tools",
    )

    for lesson_id in primitive_ids:
        lesson = manifest["lessons"][lesson_id]
        contract = lesson["teaching_contract"]
        assert lesson["episode_pattern"] == "foundation_build"
        assert contract["worked_walkthrough"]
        assert contract["boundary_and_invariant"]["invariant"]
        assert contract["proof_interpretation"]["does_not_establish"]


def test_foundation_build_lessons_have_a_pattern_aware_study_contract():
    manifest = load_manifest()
    for lesson_id in (
        "0001-model-call-primitive",
        "0002-message-state-primitive",
        "0003-manual-tool-protocol",
        "0004-schema-validation",
        "0005-sandboxed-file-tools",
    ):
        study = manifest["lessons"][lesson_id]["study_contract"]
        assert study["version"] == 1
        assert len(study["think"]["prompts"]) == 3
        assert "prediction_vs_evidence" in study["reflect"]
        assert set(study["plan"]["fields"]) == {
            "target_function", "smallest_slice", "must_do", "must_not_do", "first_proof", "open_question"
        }


def test_study_contract_cannot_remove_jot_notes_feynman_or_existing_handoff():
    manifest = deepcopy(load_manifest())
    study = manifest["lessons"]["0001-model-call-primitive"]["study_contract"]
    study["think"].pop("jot_notes")

    with pytest.raises(ManifestError, match="jot_notes"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    study = manifest["lessons"]["0001-model-call-primitive"]["study_contract"]
    study["reflect"].pop("feynman_limit")

    with pytest.raises(ManifestError, match="feynman_limit"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    study = manifest["lessons"]["0001-model-call-primitive"]["study_contract"]
    study["plan"]["fields"].pop("first_proof")

    with pytest.raises(ManifestError, match="existing handoff fields"):
        validate_manifest(manifest)


def test_foundation_build_requires_explanation_and_inspectable_starting_artifact():
    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0001-model-call-primitive"]
    lesson["teaching_contract"].pop("first_principle")

    with pytest.raises(ManifestError, match="first_principle"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0001-model-call-primitive"]
    lesson["starting_artifacts"] = {
        "source_files": [], "symbols": [], "tests": [], "scenario_sources": []
    }

    with pytest.raises(ManifestError, match="inspectable starting artifact"):
        validate_manifest(manifest)


def test_foundation_build_requires_a_real_tradeoff_and_proof_limit():
    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0004-schema-validation"]["teaching_contract"]
    contract["design_tension"]["options"] = ["Validate it"]

    with pytest.raises(ManifestError, match="design_tension.options"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0004-schema-validation"]["teaching_contract"]
    contract["proof_interpretation"].pop("does_not_establish")

    with pytest.raises(ManifestError, match="does_not_establish"):
        validate_manifest(manifest)


def test_agent_loop_uses_reusable_integration_build_contract():
    manifest = load_manifest()
    lesson = manifest["lessons"]["0006-agent-loop-primitive"]
    contract = lesson["teaching_contract"]

    assert lesson["episode_pattern"] == "integration_build"
    assert lesson["lesson_type"] == "reconstruction_lab"
    assert contract["intervention_strategy"]["mode"] == "reconstruct"
    assert len(contract["prerequisite_bridge"]["existing_components"]) >= 2
    assert len(contract["integration_proof"]["required_evidence"]) >= 2
    study = lesson["study_contract"]
    assert study["think"]["prompts"][0]["id"] == "model"
    assert "trajectory" in study["reflect"]["prediction_vs_evidence"]["prompt"]


def test_integration_build_reconstruction_requires_scaffold_and_matching_lab_type():
    manifest = deepcopy(load_manifest())
    strategy = manifest["lessons"]["0006-agent-loop-primitive"]["teaching_contract"]["intervention_strategy"]
    strategy.pop("scaffold")

    with pytest.raises(ManifestError, match="scaffold"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0006-agent-loop-primitive"]
    lesson["lesson_type"] = "implementation_lab"

    with pytest.raises(ManifestError, match="lesson_type reconstruction_lab"):
        validate_manifest(manifest)


def test_integration_build_requires_component_model_and_multiple_proof_outcomes():
    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0006-agent-loop-primitive"]["teaching_contract"]
    contract["system_model"]["components"] = []

    with pytest.raises(ManifestError, match="system_model.components"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0006-agent-loop-primitive"]["teaching_contract"]
    contract["integration_proof"]["required_evidence"] = ["one case"]

    with pytest.raises(ManifestError, match="integration_proof.required_evidence"):
        validate_manifest(manifest)


def test_trace_logger_uses_diagnostic_clinic_with_evidence_gap():
    manifest = load_manifest()
    lesson = manifest["lessons"]["0007-trace-logger"]
    contract = lesson["teaching_contract"]

    assert lesson["episode_pattern"] == "diagnostic_clinic"
    assert contract["worked_investigation"]["current_conclusion"].startswith("The incident is evidence-insufficient")
    assert contract["intervention_strategy"]["mode"] == "add_evidence"
    assert len(contract["diagnostic_model"]["candidate_causes"]) >= 2
    study = lesson["study_contract"]
    assert study["think"]["prompts"][0]["id"] == "incident_facts"
    assert "candidate cause" in study["reflect"]["prediction_vs_evidence"]["prompt"]


def test_diagnostic_clinic_requires_a_pattern_aware_study_contract():
    manifest = deepcopy(load_manifest())
    manifest["lessons"]["0007-trace-logger"].pop("study_contract")

    with pytest.raises(ManifestError, match="selected episode pattern requires a study_contract"):
        validate_manifest(manifest)


def test_diagnostic_clinic_requires_competing_causes_inspection_and_regression_evidence():
    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0007-trace-logger"]["teaching_contract"]
    contract["diagnostic_model"]["candidate_causes"] = []

    with pytest.raises(ManifestError, match="candidate_causes"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0007-trace-logger"]["teaching_contract"]
    contract["artifact_inspection_sequence"] = []

    with pytest.raises(ManifestError, match="artifact_inspection_sequence"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0007-trace-logger"]["teaching_contract"]
    contract["diagnostic_proof"]["required_evidence"] = ["partial fixture"]

    with pytest.raises(ManifestError, match="diagnostic_proof.required_evidence"):
        validate_manifest(manifest)


def test_eval_runner_uses_experiment_lab_with_repeatable_measurement():
    manifest = load_manifest()
    lesson = manifest["lessons"]["0008-eval-runner"]
    contract = lesson["teaching_contract"]

    assert lesson["episode_pattern"] == "experiment_lab"
    assert contract["experiment_strategy"]["mode"] == "construct"
    assert len(contract["measurement_model"]["outcome_contract"]) >= 2
    assert len(contract["measurement_proof"]["required_evidence"]) >= 4
    study = lesson["study_contract"]
    assert study["think"]["prompts"][0]["id"] == "behavioral_claim"
    assert "wrong-answer" in study["reflect"]["prediction_vs_evidence"]["prompt"]


def test_experiment_lab_requires_a_pattern_aware_study_contract():
    manifest = deepcopy(load_manifest())
    manifest["lessons"]["0008-eval-runner"].pop("study_contract")

    with pytest.raises(ManifestError, match="selected episode pattern requires a study_contract"):
        validate_manifest(manifest)


def test_experiment_lab_requires_case_coverage_controls_and_failed_case_evidence():
    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0008-eval-runner"]["teaching_contract"]
    contract["measurement_model"]["cases"]["minimum_coverage"] = ["one case"]

    with pytest.raises(ManifestError, match="minimum_coverage"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0008-eval-runner"]["teaching_contract"]
    contract["measurement_model"]["controlled_conditions"] = []

    with pytest.raises(ManifestError, match="controlled_conditions"):
        validate_manifest(manifest)

    manifest = deepcopy(load_manifest())
    contract = manifest["lessons"]["0008-eval-runner"]["teaching_contract"]
    contract["measurement_proof"]["required_evidence"] = ["aggregate score"]

    with pytest.raises(ManifestError, match="measurement_proof.required_evidence"):
        validate_manifest(manifest)


def test_operational_drill_contract_supports_constrained_evidence_backed_procedure():
    validate_operational_drill_contract("0099-trace-replay", operational_drill_contract())


def test_operational_drill_requires_a_pattern_aware_study_contract():
    lesson = {"episode_pattern": "operational_drill"}

    with pytest.raises(ManifestError, match="selected episode pattern requires a study_contract"):
        validate_study_contract("0099-trace-replay", lesson)

    lesson["study_contract"] = deepcopy(load_manifest()["lessons"]["0001-model-call-primitive"]["study_contract"])
    with pytest.raises(ManifestError, match="operational_drill workspace"):
        validate_study_contract("0099-trace-replay", lesson)

    lesson["study_contract"]["think"]["prompts"] = [
        {"id": "operational_context", "label": "Context", "prompt": "State the trigger and authority.", "kind": "evidence"},
        {"id": "next_safe_action", "label": "Action", "prompt": "Commit to the next authorized action.", "kind": "judgment"},
        {"id": "safe_stop_evidence", "label": "Stop", "prompt": "Name the no-go signal and handoff evidence.", "kind": "uncertainty"},
    ]
    validate_study_contract("0099-trace-replay", lesson)


def test_operational_drill_requires_preflight_authority_and_safe_stop_evidence():
    contract = operational_drill_contract()
    contract["readiness_check"]["preflight_checks"] = []

    with pytest.raises(ManifestError, match="preflight_checks"):
        validate_operational_drill_contract("0099-trace-replay", contract)

    contract = operational_drill_contract()
    contract["execution_contract"].pop("authority_boundary")

    with pytest.raises(ManifestError, match="authority_boundary"):
        validate_operational_drill_contract("0099-trace-replay", contract)

    contract = operational_drill_contract()
    contract["operational_proof"]["required_evidence"] = ["command output"]

    with pytest.raises(ManifestError, match="operational_proof.required_evidence"):
        validate_operational_drill_contract("0099-trace-replay", contract)


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
    lesson = manifest["lessons"]["0008-eval-runner"]
    lesson["publication"] = {"status": "locked", "reason": "A contract-only lesson cannot advance the course."}
    lesson["lesson_type"] = "specification"
    lesson["unlocks"] = ["0001-model-call-primitive"]

    with pytest.raises(ManifestError, match="cannot unlock"):
        validate_manifest(manifest)


def test_prerequisites_require_demonstrated_learning_and_publication():
    manifest = load_manifest()
    phases = {
        "0003-manual-tool-protocol": "learned",
        "0004-schema-validation": "learned",
        "0005-sandboxed-file-tools": "learned",
    }
    assert prerequisites_met("0006-agent-loop-primitive", phases, manifest)

    manifest = deepcopy(manifest)
    manifest["lessons"]["0005-sandboxed-file-tools"]["publication"] = {
        "status": "locked",
        "reason": "A locked lesson cannot satisfy a dependency.",
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


def test_lesson_identifiers_match_bound_source_and_error_codes_do_not_drift(tmp_path):
    manifest = deepcopy(load_manifest())
    lesson = manifest["lessons"]["0005-sandboxed-file-tools"]
    source = Path(__file__).resolve().parents[1] / "lessons" / "0005-sandboxed-file-tools.html"

    assert not lint_lesson("0005-sandboxed-file-tools", lesson, source)

    drifted_source = tmp_path / source.name
    drifted_source.write_text(
        source.read_text(encoding="utf-8").replace("FORBIDDEN_PATH", "PATH_OUTSIDE_SANDBOX", 1),
        encoding="utf-8",
    )

    errors = lint_lesson("0005-sandboxed-file-tools", lesson, drifted_source)

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
