import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from study_server import StudyStore


def test_study_store_round_trip(tmp_path):
    store = StudyStore(tmp_path / "study.sqlite3")

    saved = store.save(
        "0006-agent-loop-primitive",
        {
            "status": "ready_to_implement",
            "responses": {
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
                "mental_model": "The model proposes; the harness decides.",
                "next_step": "Implement submit handling at home.",
            },
        },
    )

    assert saved["status"] == "ready_to_implement"
    assert saved["responses"]["invariant"]["answer"] == "The harness decides whether a request runs."
    assert saved["plan"]["target_function"] == "run_agent"
    assert saved["reflection"]["next_step"] == "Implement submit handling at home."
    assert store.progress() == [
        {
            "lesson_id": "0006-agent-loop-primitive",
            "status": "ready_to_implement",
            "updated_at": saved["updated_at"],
        }
    ]
