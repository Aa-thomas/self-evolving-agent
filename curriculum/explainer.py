"""Build faithful, printable explainers from captured implementation evidence."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = Path(__file__).with_name("explainers") / "generated"


def build_explainer(
    lesson_id: str,
    lesson: dict[str, Any],
    state: dict[str, Any],
    proof_artifact: Path,
) -> tuple[Path, Path]:
    proof = json.loads(proof_artifact.read_text(encoding="utf-8"))
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    markdown_path = OUTPUT_ROOT / f"{lesson_id}.md"
    html_path = OUTPUT_ROOT / f"{lesson_id}.html"
    invariant = state.get("responses", {}).get("invariant", {}).get("answer", "")
    open_question = state.get("plan", {}).get("open_question", "")
    diff = proof.get("diff", "").strip()
    diff_section = diff if diff else "No uncommitted target diff was present. Use the configured target and passing proof as the evidence boundary."
    targets = ", ".join(lesson["implementation"]["targets"]) or "No implementation target exists yet."
    source = lesson.get("micro_world", {}).get("scenario_source")
    questions = [
        f"State the invariant for {lesson_id} without reopening the lesson.",
        f"Explain how the passing proof `{lesson['implementation']['first_proof']}` demonstrates behavior but not understanding by itself.",
        "Choose one failure trajectory and explain which component must intervene next.",
    ]
    markdown = f"""# Implementation Explainer: {lesson_id}

## Background

Learning goal: {lesson['learning_goal']}

Prior invariant captured by the learner: {invariant or 'No learner invariant was captured; do not infer one.'}

## Intent Before Details

Smallest slice: {state.get('plan', {}).get('smallest_slice') or 'No smallest slice was recorded.'}

Must do: {state.get('plan', {}).get('must_do') or 'Not recorded.'}

Must not do: {state.get('plan', {}).get('must_not_do') or 'Not recorded.'}

## Evidence

- Targets: {targets}
- Proof: `{' '.join(proof.get('command', []))}`
- Result: {'passed' if proof.get('passed') else 'failed'} with exit code {proof.get('exit_code')}
- Trace scenarios: {source or 'No trace scenario source is configured.'}

## Literate Diff

Read this in the order implied by the learning goal and proof. The content below is restricted to the configured implementation targets.

```diff
{diff_section}
```

## Failure And Boundary Check

Open question carried into implementation: {open_question or 'None recorded.'}

The proof establishes only the tested behavior. It does not establish recall, transfer, or the correctness of unrelated paths.

## Recall From Memory

1. {questions[0]}
2. {questions[1]}
3. {questions[2]}
"""
    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(render_html(lesson_id, markdown, proof, questions), encoding="utf-8")
    return markdown_path, html_path


def render_html(lesson_id: str, markdown: str, proof: dict[str, Any], questions: list[str]) -> str:
    diff = proof.get("diff", "").strip() or "No uncommitted target diff was present."
    intent = markdown.split("## Intent Before Details\n\n", 1)[1].split("## Evidence", 1)[0].strip()
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Implementation Explainer · {html.escape(lesson_id)}</title>
<style>
body{{background:#f8f5ef;color:#242321;font:17px/1.6 ui-serif,Georgia,serif;margin:auto;max-width:850px;padding:32px 20px}}
h1,h2{{line-height:1.18}} pre{{background:#fff;border:1px solid #d8d3c8;border-radius:7px;overflow:auto;padding:16px}}
.evidence{{background:#fff;border-left:4px solid #4d6b57;padding:12px 16px}} @media print{{body{{background:white;max-width:none}}}}
</style></head><body>
<p>Evidence-grounded implementation explainer</p><h1>{html.escape(lesson_id)}</h1>
<h2>Intent</h2><p>{html.escape(intent)}</p>
<h2>Executable evidence</h2><div class="evidence"><p>Command: <code>{html.escape(' '.join(proof.get('command', [])))}</code></p><p>Result: {'passed' if proof.get('passed') else 'failed'} · exit code {proof.get('exit_code')}</p></div>
<h2>Relevant diff</h2><pre><code>{html.escape(diff)}</code></pre>
<h2>Recall from memory</h2><ol>{''.join(f'<li>{html.escape(question)}</li>' for question in questions)}</ol>
<p>The proof covers its declared behavior only. Missing evidence is not filled in by generation.</p>
</body></html>"""
