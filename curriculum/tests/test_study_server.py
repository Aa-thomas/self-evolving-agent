import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from study_server import StudyStore


def test_study_store_migrates_legacy_reflections(tmp_path):
    database = tmp_path / "study.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TABLE reflections (
                lesson_id TEXT PRIMARY KEY,
                mental_model TEXT NOT NULL DEFAULT '',
                next_step TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );
            INSERT INTO reflections (lesson_id, mental_model, next_step, updated_at)
            VALUES ('0001-model-call-primitive', 'Keep the boundary thin.', 'Write the focused proof.', '2026-01-01T00:00:00+00:00');
            """
        )

    store = StudyStore(database)

    migrated = store.load("0001-model-call-primitive")

    assert migrated["reflection"] == {
        "feynman_explanation": "",
        "feynman_limit": "",
        "mental_model": "Keep the boundary thin.",
        "next_step": "Write the focused proof.",
    }


def test_study_store_round_trip(tmp_path):
    store = StudyStore(tmp_path / "study.sqlite3")

    saved = store.save(
        "0006-agent-loop-primitive",
        {
            "status": "ready_to_implement",
            "responses": {
                "jot_notes": {
                    "answer": "submit, stop condition, no external tool",
                    "self_assessment": "unrated",
                },
                "invariant": {
                    "answer": "The harness decides whether a request runs.",
                    "self_assessment": "clear",
                }
            },
            "plan": {
                "target_function": "run_agent",
                "smallest_slice": "Stop on submit.",
                "must_do": "Return the submitted answer.",
                "must_not_do": "Call an external tool.",
                "first_proof": "test_submit_stops_loop",
                "open_question": "When is the assistant message appended?",
            },
            "reflection": {
                "feynman_explanation": "The model suggests moves, but the harness is the referee.",
                "feynman_limit": "The analogy hides JSON parsing and validation details.",
                "mental_model": "The model proposes; the harness decides.",
                "next_step": "Implement submit handling at home.",
            },
        },
    )

    assert saved["status"] == "ready_to_implement"
    assert saved["responses"]["jot_notes"]["answer"] == "submit, stop condition, no external tool"
    assert saved["responses"]["invariant"]["answer"] == "The harness decides whether a request runs."
    assert saved["plan"]["target_function"] == "run_agent"
    assert saved["reflection"]["feynman_explanation"] == (
        "The model suggests moves, but the harness is the referee."
    )
    assert saved["reflection"]["feynman_limit"] == (
        "The analogy hides JSON parsing and validation details."
    )
    assert saved["reflection"]["next_step"] == "Implement submit handling at home."
    assert saved["phase"] == "ready_to_implement"
    assert saved["milestones"]["implementation_plan_ready"] is True
    assert saved["milestones"]["proof_passed"] is False
    assert saved["events"][0]["event_type"] == "lesson.ready_to_implement"
    assert saved["reviews"][0]["kind"] == "pre_implementation"
    assert store.progress() == [
        {
            "lesson_id": "0006-agent-loop-primitive",
            "status": "ready_to_implement",
            "phase": "ready_to_implement",
            "updated_at": saved["updated_at"],
        }
    ]


def test_study_store_requires_proof_before_consolidation(tmp_path):
    store = StudyStore(tmp_path / "study.sqlite3")
    ready = store.save(
        "0006-agent-loop-primitive",
        {
            "status": "ready_to_implement",
            "plan": {
                "target_function": "run_agent",
                "smallest_slice": "Stop on submit.",
                "must_do": "Return the answer.",
                "must_not_do": "Execute submit.",
                "first_proof": "test_submit_stops_loop",
                "open_question": "none",
            },
        },
    )

    try:
        store.save(
            "0006-agent-loop-primitive",
            {
                "status": ready["status"],
                "phase": "consolidating",
                "milestones": ready["milestones"],
            },
        )
    except ValueError as error:
        assert "proof_passed" in str(error)
    else:
        raise AssertionError("Consolidation advanced without a passing proof")
