import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PHASE_ROOT = ROOT.parent
sys.path.insert(0, str(PHASE_ROOT))

MODULE_PATH = ROOT / "eval_runner.py"
FIXTURE_PATH = ROOT / "fixtures" / "eval-cases.json"
AGENT_LOOP_PATH = PHASE_ROOT / "06_agent_loop" / "agent_loop.py"
spec = importlib.util.spec_from_file_location("eval_runner", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

agent_spec = importlib.util.spec_from_file_location("agent_loop_for_eval", AGENT_LOOP_PATH)
assert agent_spec is not None and agent_spec.loader is not None
agent_loop = importlib.util.module_from_spec(agent_spec)
sys.modules[agent_spec.name] = agent_loop
agent_spec.loader.exec_module(agent_loop)


class FakeModel:
    def __init__(self, outputs: list[str]):
        self.outputs = outputs

    def complete(self, messages: list[dict[str, str]]) -> str:
        return self.outputs.pop(0)


def copy_file_run(*, answer: str) -> dict[str, str]:
    files = {"a.txt": "hello"}

    def read_file(path: str):
        return agent_loop.Ok(files[path])

    def write_file(path: str, content: str):
        files[path] = content
        return agent_loop.Ok({"path": path, "bytes_written": len(content)})

    result = agent_loop.run_agent(
        user_task="Copy a.txt to b.txt.",
        model=FakeModel([
            '{"tool":"read_file","args":{"path":"a.txt"}}',
            '{"tool":"write_file","args":{"path":"b.txt","content":"hello"}}',
            f'{{"tool":"submit","args":{{"answer":"{answer}"}}}}',
        ]),
        tools={"read_file": read_file, "write_file": write_file},
        max_steps=4,
    )
    return {
        "exit_reason": result.exit_reason,
        "final_answer": result.final_answer or "",
        "target_content": files.get("b.txt", ""),
    }


def test_eval_case_fixture_describes_a_composed_workflow():
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert cases[0]["name"] == "copy-file"
    assert cases[0]["expected"] == {"exit_reason": "submitted", "final_answer": "copied", "target_content": "hello"}
    assert len(cases[0]["model_outputs"]) == 3


def test_eval_runner_reports_each_case_and_causal_trace():
    assert copy_file_run(answer="copied") == {
        "exit_reason": "submitted",
        "final_answer": "copied",
        "target_content": "hello",
    }
    copied = module.EvalCase(
        name="copy-file",
        run=lambda: copy_file_run(answer="copied"),
        expected={"exit_reason": "submitted", "final_answer": "copied", "target_content": "hello"},
        trace_path="traces/copy-file.json",
    )
    wrong_answer = module.EvalCase(
        name="wrong-answer",
        run=lambda: copy_file_run(answer="wrong"),
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
