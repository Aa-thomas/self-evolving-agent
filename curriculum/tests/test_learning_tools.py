import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "curriculum"))

from study_server import StudyStore


def ready_agent_loop(store: StudyStore):
    return store.save(
        "0006-agent-loop-primitive",
        {
            "status": "ready_to_implement",
            "responses": {
                "invariant": {
                    "answer": "The harness alone decides what executes.",
                    "self_assessment": "clear",
                }
            },
            "plan": {
                "target_function": "run_agent",
                "smallest_slice": "Stop on submit.",
                "must_do": "Return the final answer.",
                "must_not_do": "Dispatch submit as a registered tool.",
                "first_proof": "test_submit_stops_loop",
                "open_question": "When is the assistant message appended?",
            },
        },
    )


def test_prove_lesson_advances_to_consolidation_and_builds_explainer(tmp_path):
    database = tmp_path / "study.sqlite3"
    store = StudyStore(database)
    ready_agent_loop(store)

    result = subprocess.run(
        [str(ROOT / "tools" / "prove-lesson"), "0006-agent-loop-primitive", "--database", str(database), "--local"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    state = store.load("0006-agent-loop-primitive")
    assert state["phase"] == "consolidating"
    assert state["milestones"]["proof_passed"] is True
    assert state["evidence"]["proof_runs"][-1]["passed"] is True
    assert state["evidence"]["explainer_path"].endswith("0006-agent-loop-primitive.html")
