from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from build_lessons_site import read_lesson, render_index, render_lesson  # noqa: E402
from lint_lessons import lint_publication_contract  # noqa: E402


PRIMARY_URL = "https://developers.openai.com/api/docs/guides/function-calling"
FURTHER_URL = "https://docs.python.org/3/library/typing.html#typing.Protocol"


def publication_contract() -> dict[str, object]:
    return {
        "identity": {
            "number": 1,
            "technical_name": "Model-Call Boundary",
            "memorable_phrase": "A model call is text in, text out, plus evidence",
        },
        "lecture_contract": {
            "central_thesis": "A boundary should normalize provider output.",
            "explanatory_obligations": [
                {"id": "provider-boundary", "claim": "The adapter owns normalization."},
                {"id": "evidence-record", "claim": "The record retains evidence."},
                {"id": "proof-limit", "claim": "One test proves one behavior."},
            ],
            "worked_example": {
                "artifact": "agent_primitives/model.py",
                "arc": ["input", "normalization", "record"],
            },
            "study_prompt_coverage": {},
        },
        "reading_contract": {
            "primary": {
                "title": "OpenAI docs: Function calling",
                "url": PRIMARY_URL,
                "why": "Connect the local adapter to the application-side tool contract.",
            },
            "further": [
                {
                    "title": "Python docs: typing.Protocol",
                    "url": FURTHER_URL,
                    "why": "Understand the structural interface at the provider boundary.",
                }
            ],
        },
    }


def valid_publication_html() -> str:
    return f"""<!doctype html>
<html lang="en">
  <head><title>Project 1A · Model-Call Boundary · A model call is text in, text out, plus evidence</title></head>
  <body>
    <main>
      <header data-lesson-identity>
        <p class="eyebrow">Primitive 1 · Model-Call Boundary</p>
        <h1>A model call is text in, text out, plus evidence</h1>
      </header>
      <article data-lecture>
        <section data-lecture-obligation="provider-boundary"><h2>The boundary</h2></section>
        <section data-lecture-obligation="evidence-record" data-worked-example><h2>Worked example</h2></section>
        <section data-lecture-obligation="proof-limit" data-lecture-reveal="after-prediction" hidden>
          <h2>Proof limits</h2>
        </section>
      </article>
      <section data-engineering-lab>
        <section data-prediction><h2>Prediction</h2></section>
      </section>
      <section data-further-reading>
        <h2>Further reading</h2>
        <article class="source-card">
          <p>Primary source</p>
          <a href="{PRIMARY_URL}">OpenAI docs: Function calling</a>
          <p>Connect the local adapter to the application-side tool contract.</p>
        </article>
        <article class="source-card">
          <p>Go deeper</p>
          <a href="{FURTHER_URL}">Python docs: typing.Protocol</a>
          <p>Understand the structural interface at the provider boundary.</p>
        </article>
      </section>
    </main>
  </body>
</html>"""


def test_publication_contract_accepts_complete_lecture_identity_and_readings():
    errors = lint_publication_contract(
        "0001-model-call-primitive",
        publication_contract(),
        valid_publication_html(),
        resource_urls={PRIMARY_URL, FURTHER_URL},
    )

    assert errors == []


def test_publication_contract_reports_structure_identity_and_reading_drift():
    html = (
        valid_publication_html()
        .replace(
            "</article>",
            """<section data-lecture-obligation="undeclared"><h2>Undeclared</h2></section>
      </article>""",
            1,
        )
        .replace(" data-engineering-lab", "")
        .replace(' data-lecture-obligation="proof-limit"', "")
        .replace(" data-worked-example", "")
        .replace(" hidden>", ">")
        .replace("OpenAI docs: Function calling</a>", "Different source</a>")
        .replace(
            "<p>Connect the local adapter to the application-side tool contract.</p>",
            "<p>The primary annotation is missing from this card.</p>",
        )
        .replace(
            "<p>Understand the structural interface at the provider boundary.</p>",
            """<p>Understand the structural interface at the provider boundary.</p>
            <p>Connect the local adapter to the application-side tool contract.</p>
            <a href="https://example.com/uncontracted">Uncontracted reading</a>""",
        )
    )

    errors = lint_publication_contract(
        "0001-model-call-primitive",
        publication_contract(),
        html,
        resource_urls={FURTHER_URL},
    )

    assert any("section[data-engineering-lab]" in error for error in errors)
    assert any("missing explanatory obligation: proof-limit" in error for error in errors)
    assert any("requires a data-worked-example" in error for error in errors)
    assert any("after-prediction lecture reveals must be hidden" in error for error in errors)
    assert any("missing its source title" in error for error in errors)
    assert any("missing its lesson-specific annotation" in error for error in errors)
    assert any("reading URL is absent from RESOURCES.md" in error for error in errors)
    assert any("uncontracted external source" in error for error in errors)
    assert any("undeclared explanatory obligation" in error for error in errors)


def test_publication_contract_reports_memorable_identity_drift():
    html = (
        valid_publication_html()
        .replace(
            "Project 1A · Model-Call Boundary · A model call is text in, text out, plus evidence",
            "Project 1A: Old title",
        )
        .replace(
            "<p class=\"eyebrow\">Primitive 1 · Model-Call Boundary</p>",
            "<p class=\"eyebrow\">Project 1A</p>",
        )
        .replace(
            "<h1>A model call is text in, text out, plus evidence</h1>",
            "<h1>Old assignment title</h1>",
        )
        .replace(
            "<section data-engineering-lab>",
            "<section data-engineering-lab><section data-prediction></section>",
        )
    )

    errors = lint_publication_contract(
        "0001-model-call-primitive",
        publication_contract(),
        html,
        resource_urls={PRIMARY_URL, FURTHER_URL},
    )

    assert any("H1 must equal the memorable phrase" in error for error in errors)
    assert any("browser title must be" in error for error in errors)
    assert any("lesson identity must name Primitive 1" in error for error in errors)
    assert any("exactly one section[data-prediction]" in error for error in errors)


def test_publication_contract_rejects_unscoped_lecture_markers():
    worked_example = (
        '<section data-lecture-obligation="evidence-record" data-worked-example>'
        "<h2>Worked example</h2></section>"
    )
    html = valid_publication_html().replace(worked_example, "")
    html = html.replace("</article>", f"</article>{worked_example}", 1)

    errors = lint_publication_contract(
        "0001-model-call-primitive",
        publication_contract(),
        html,
        resource_urls={PRIMARY_URL, FURTHER_URL},
    )

    assert any("missing explanatory obligation: evidence-record" in error for error in errors)
    assert any("explanatory obligation must be inside" in error for error in errors)
    assert any("lecture requires a data-worked-example" in error for error in errors)
    assert any("data-worked-example must be inside" in error for error in errors)


def test_publication_contract_accepts_explicit_post_prediction_lecture_continuation():
    worked_example = (
        '<section data-lecture-obligation="evidence-record" data-worked-example>'
        "<h2>Worked example</h2></section>"
    )
    continuation = worked_example.replace(
        "<section ",
        "<section data-lecture-continuation ",
        1,
    )
    html = valid_publication_html().replace(worked_example, "")
    html = html.replace("</article>", f"</article>{continuation}", 1)

    errors = lint_publication_contract(
        "0001-model-call-primitive",
        publication_contract(),
        html,
        resource_urls={PRIMARY_URL, FURTHER_URL},
    )

    assert errors == []


def test_builder_uses_manifest_identity_for_index_navigation_and_browser_title(tmp_path):
    source = tmp_path / "0001-model-call-primitive.html"
    source.write_text(
        """<!doctype html><html><head><title>Authored title</title>
        <link rel="stylesheet" href="../assets/course.css"></head>
        <body><main><h1>Authored heading</h1></main></body></html>""",
        encoding="utf-8",
    )
    lesson = read_lesson(source, publication_contract())

    index = render_index([lesson], [], {"lessons": {}})
    rendered_lesson = render_lesson([lesson], 0, total_lessons=8)

    phrase = "A model call is text in, text out, plus evidence"
    technical = "Model-Call Boundary"
    assert index.index(phrase) < index.index(f"Primitive 1 · {technical}")
    assert "<div><span>1</span>Model-Call Boundary</div>" in index
    assert f"<title>Project 1A · {technical} · {phrase}</title>" in rendered_lesson
    assert f"Lesson 1 of 8 · {technical}" in rendered_lesson
