import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "curriculum"))

def test_prove_lesson_requires_an_implementation_handoff(tmp_path):
    database = tmp_path / "study.sqlite3"

    result = subprocess.run(
        [str(ROOT / "tools" / "prove-lesson"), "0006-agent-loop-primitive", "--database", str(database), "--local"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "complete implementation handoff" in result.stderr
