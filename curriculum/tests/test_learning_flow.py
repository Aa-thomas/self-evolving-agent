import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from learning_flow import ManifestError, load_manifest, prerequisites_met, validate_manifest


def test_project_manifest_is_valid_and_uses_real_targets():
    manifest = load_manifest()

    assert len(manifest["lessons"]) == 8
    assert manifest["lessons"]["0006-agent-loop-primitive"]["micro_world"]["decision"] == "required"


def test_manifest_rejects_prerequisite_cycles():
    manifest = deepcopy(load_manifest())
    manifest["lessons"]["0001-model-call-primitive"]["requires"] = ["0008-eval-runner"]

    with pytest.raises(ManifestError, match="cycle"):
        validate_manifest(manifest)


def test_manifest_rejects_decorative_micro_worlds():
    manifest = deepcopy(load_manifest())
    micro_world = manifest["lessons"]["0001-model-call-primitive"]["micro_world"]
    micro_world.update({"decision": "required", "score": 2, "component": "fancy-demo"})

    with pytest.raises(ManifestError, match="at least 6"):
        validate_manifest(manifest)


def test_prerequisites_require_demonstrated_learning():
    phases = {
        "0003-manual-tool-protocol": "learned",
        "0004-schema-validation": "learned",
        "0005-sandboxed-file-tools": "ready_to_implement",
    }

    assert not prerequisites_met("0006-agent-loop-primitive", phases)
    phases["0005-sandboxed-file-tools"] = "learned"
    assert prerequisites_met("0006-agent-loop-primitive", phases)


def test_trace_lab_choices_do_not_hint_by_word_count():
    scenarios = json.loads(
        (Path(__file__).resolve().parents[1] / "traces" / "agent-loop-scenarios.json").read_text()
    )["scenarios"]

    for scenario in scenarios:
        for step in scenario["steps"]:
            assert len({len(choice.split()) for choice in step["choices"]}) == 1
            assert 0 <= step["answer"] < len(step["choices"])
            assert step["explanation"]
