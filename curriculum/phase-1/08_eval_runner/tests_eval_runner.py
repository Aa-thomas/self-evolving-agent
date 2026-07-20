import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODULE_PATH = ROOT / "eval_runner.py"
FIXTURE_PATH = ROOT / "fixtures" / "eval-cases.json"
spec = importlib.util.spec_from_file_location("eval_runner", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_eval_case_fixture_describes_a_composed_workflow():
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert cases[0]["name"] == "copy-file"
    assert cases[0]["expected"] == {"exit_reason": "submitted", "final_answer": "copied", "target_content": "hello"}
    assert len(cases[0]["model_outputs"]) == 3


def test_eval_runner_reports_each_case_and_causal_trace():
    copied = module.EvalCase(
        name="copy-file",
        run=lambda: {"exit_reason": "submitted", "final_answer": "copied", "target_content": "hello"},
        expected={"exit_reason": "submitted", "final_answer": "copied", "target_content": "hello"},
        trace_path="traces/copy-file.json",
    )
    wrong_answer = module.EvalCase(
        name="wrong-answer",
        run=lambda: {"exit_reason": "submitted", "final_answer": "wrong", "target_content": "hello"},
        expected={"exit_reason": "submitted", "final_answer": "copied", "target_content": "hello"},
        trace_path="traces/wrong-answer.json",
    )

    report = module.run_eval_suite([copied, wrong_answer])

    assert report.total == 2
    assert report.passed == 1
    assert report.failed == 1
    assert report.cases[0].passed is True
    assert report.cases[1].passed is False
    assert report.cases[1].trace_path == "traces/wrong-answer.json"
    assert "final_answer" in report.cases[1].failure_reason
