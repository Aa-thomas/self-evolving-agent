from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().with_name("01_model_call") / "01_model_call.py"
MODULE_NAME = "project_1a_model_call"

spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)

assert spec is not None
assert spec.loader is not None

module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
spec.loader.exec_module(module)

ModelCallRecord = module.ModelCallRecord
OpenRouterModel = module.OpenRouterModel
call_model = module.call_model
estimate_tokens = module.estimate_tokens
record_to_dict = module.record_to_dict


if __name__ == "__main__":
    module.app()
