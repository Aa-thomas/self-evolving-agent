from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "curriculum"
LESSONS_SRC = CURRICULUM / "lessons"
ASSETS_SRC = CURRICULUM / "assets"
SITE = ROOT / "site"
LESSONS_OUT = SITE / "lessons"
ASSETS_OUT = SITE / "assets"

sys.path.insert(0, str(CURRICULUM))
from learning_flow import load_manifest  # noqa: E402


LOCAL_LINK_PATTERN = re.compile(
    r'<a href="(?:\.\./phase-1/[^"]+|\.\./reference/[^"]+|\./\.\./Harness[^"]+)">(.*?)</a>',
    re.DOTALL,
)
H1_PATTERN = re.compile(r"<h1>(.*?)</h1>", re.DOTALL)
EYEBROW_PATTERN = re.compile(r'<p class="eyebrow">(.*?)</p>', re.DOTALL)
TAG_PATTERN = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class Lesson:
    source: Path
    output_name: str
    title: str
    eyebrow: str


def text_from_html(raw: str) -> str:
    without_tags = TAG_PATTERN.sub("", raw)
    return " ".join(without_tags.split())


def read_lesson(source: Path) -> Lesson:
    html = source.read_text(encoding="utf-8")
    h1_match = H1_PATTERN.search(html)
    eyebrow_match = EYEBROW_PATTERN.search(html)

    title = text_from_html(h1_match.group(1)) if h1_match else source.stem
    eyebrow = text_from_html(eyebrow_match.group(1)) if eyebrow_match else "Project 1A"

    return Lesson(
        source=source,
        output_name=source.name,
        title=title,
        eyebrow=eyebrow,
    )


def clean_site() -> None:
    if LESSONS_OUT.exists():
        shutil.rmtree(LESSONS_OUT)
    if (SITE / "traces").exists():
        shutil.rmtree(SITE / "traces")

    LESSONS_OUT.mkdir(parents=True)
    ASSETS_OUT.mkdir(parents=True, exist_ok=True)
    (SITE / "traces").mkdir(parents=True, exist_ok=True)


def copy_assets() -> None:
    for asset in ASSETS_SRC.iterdir():
        if asset.is_file():
            shutil.copy2(asset, ASSETS_OUT / asset.name)

    (ASSETS_OUT / "site.css").write_text(SITE_CSS, encoding="utf-8")
    shutil.copy2(CURRICULUM / "learning-flow.json", SITE / "learning-flow.json")
    for trace in (CURRICULUM / "traces").glob("*.json"):
        shutil.copy2(trace, SITE / "traces" / trace.name)


def write_review_page() -> None:
    shutil.copy2(CURRICULUM / "review.html", SITE / "review.html")


def strip_private_links(html: str) -> str:
    return LOCAL_LINK_PATTERN.sub(lambda match: match.group(1), html)


def add_site_assets(html: str) -> str:
    stylesheet_marker = '<link rel="stylesheet" href="../assets/course.css">'
    script_marker = '<script defer src="../assets/lesson.js"></script>'

    if stylesheet_marker in html and "../assets/site.css" not in html:
        html = html.replace(
            stylesheet_marker,
            stylesheet_marker + '\n    <link rel="stylesheet" href="../assets/site.css">',
            1,
        )

    if script_marker in html and "../assets/study.js" not in html:
        html = html.replace(
            script_marker,
            script_marker
            + '\n    <link rel="stylesheet" href="../assets/study.css">'
            + '\n    <script defer src="../assets/study.js"></script>',
            1,
        )

    return html


def nav_html(lessons: list[Lesson], index: int, *, bottom: bool = False) -> str:
    lesson = lessons[index]
    previous_link = ""
    next_link = ""

    if index > 0:
        previous = lessons[index - 1]
        previous_link = (
            f'<a href="{previous.output_name}" aria-label="Previous lesson">Previous</a>'
        )

    if index < len(lessons) - 1:
        next_lesson = lessons[index + 1]
        next_link = f'<a href="{next_lesson.output_name}" aria-label="Next lesson">Next</a>'

    nav_class = "site-nav bottom-nav" if bottom else "site-nav"

    return f"""
      <nav class="{nav_class}" aria-label="Course navigation">
        <a href="../index.html">Course Home</a>
        <span>Lesson {index + 1} of {len(lessons)}</span>
        <span>{escape(lesson.eyebrow)}</span>
        <div class="nav-spacer"></div>
        {previous_link}
        {next_link}
      </nav>
"""


def render_lesson(lessons: list[Lesson], index: int) -> str:
    lesson = lessons[index]
    html = lesson.source.read_text(encoding="utf-8")
    html = strip_private_links(html)
    html = add_site_assets(html)
    html = html.replace("<main>", "<main>" + nav_html(lessons, index), 1)
    html = html.replace("</main>", nav_html(lessons, index, bottom=True) + "    </main>", 1)
    return html


def write_lessons(lessons: list[Lesson]) -> None:
    for index, lesson in enumerate(lessons):
        output = render_lesson(lessons, index)
        (LESSONS_OUT / lesson.output_name).write_text(output, encoding="utf-8")


def render_index(lessons: list[Lesson]) -> str:
    lesson_rows = "\n".join(
        f"""
        <li>
          <a href="lessons/{lesson.output_name}">
            <span>{escape(lesson.eyebrow)}</span>
            <strong>{escape(lesson.title)}</strong>
          </a>
        </li>"""
        for lesson in lessons
    )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Project 1A Lessons</title>
    <link rel="stylesheet" href="assets/course.css">
    <link rel="stylesheet" href="assets/site.css">
    <link rel="stylesheet" href="assets/study.css">
    <script defer src="assets/study.js"></script>
  </head>
  <body data-course-home>
    <main class="course-home">
      <header>
        <p class="eyebrow">Harness Engineering</p>
        <h1>Project 1A Lessons</h1>
        <p class="lede">Study the Project 1A agent primitives, capture what you understand, and leave each lesson with a focused plan for your next home coding session.</p>
      </header>

      <section class="workflow-link" aria-label="Study workflow">
        <h2>Study, then build later</h2>
        <p>Each lesson has a private synced workspace for retrieval, notes, a narrow implementation plan, and reflection. Nothing on the site edits or runs your code.</p>
        <p><a href="study-workflow.html">Open the Study Workflow</a></p>
        <div class="study-summary" id="study-progress" aria-live="polite"></div>
      </section>

      <section class="course-map" aria-label="Project 1A primitive flow">
        <div>Model call</div>
        <div>Message state</div>
        <div>Tool JSON</div>
        <div>Validation</div>
        <div>Sandbox tools</div>
        <div>Agent loop</div>
        <div>Trace</div>
        <div>Eval</div>
      </section>

      <section>
        <h2>Lessons</h2>
        <ol class="lesson-index">
{lesson_rows}
        </ol>
      </section>
    </main>
  </body>
</html>
"""


def write_index(lessons: list[Lesson]) -> None:
    (SITE / "index.html").write_text(render_index(lessons), encoding="utf-8")


def main() -> None:
    manifest = load_manifest()
    lessons = [read_lesson(path) for path in sorted(LESSONS_SRC.glob("*.html"))]
    lesson_ids = {lesson.source.stem for lesson in lessons}
    manifest_ids = set(manifest["lessons"])
    if lesson_ids != manifest_ids:
        missing = sorted(lesson_ids - manifest_ids)
        extra = sorted(manifest_ids - lesson_ids)
        raise ValueError(f"Lesson manifest mismatch. Missing: {missing}; extra: {extra}")

    clean_site()
    copy_assets()
    write_review_page()
    write_lessons(lessons)
    write_index(lessons)


SITE_CSS = """
.site-nav {
  align-items: center;
  border-bottom: 1px solid var(--line);
  color: var(--muted);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  padding: 0 0 14px;
}

.site-nav.bottom-nav {
  border-bottom: 0;
  border-top: 1px solid var(--line);
  margin: 42px 0 0;
  padding: 16px 0 0;
}

.site-nav a {
  align-items: center;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  color: var(--accent-ink);
  display: inline-flex;
  line-height: 1;
  min-height: 44px;
  padding: 9px 10px;
  text-decoration: none;
}

.site-nav span {
  font-size: 0.82rem;
}

.nav-spacer {
  display: none;
}

.course-home header {
  margin-bottom: 24px;
}

.course-map {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 24px 0 8px;
}

.course-map div {
  background: #eef7f5;
  border: 1px solid var(--line);
  border-radius: 6px;
  color: var(--accent-ink);
  font-size: 0.9rem;
  font-weight: 700;
  min-height: 54px;
  padding: 12px;
}

.lesson-index {
  display: grid;
  gap: 10px;
  list-style: none;
  padding: 0;
}

.lesson-index li {
  margin: 0;
}

.lesson-index a {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  display: grid;
  gap: 2px;
  min-height: 72px;
  padding: 14px;
  text-decoration: none;
}

.lesson-index span {
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.lesson-index strong {
  color: var(--ink);
  font-size: 1.05rem;
}

@media (min-width: 480px) {
  .course-map {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (min-width: 640px) {
  .site-nav {
    gap: 10px 14px;
    margin-bottom: 26px;
  }

  .site-nav span {
    font-size: 0.9rem;
  }

  .nav-spacer {
    display: block;
    flex: 1 1 auto;
  }

  .course-map {
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  }

  .lesson-index a {
    padding: 14px 16px;
  }
}
"""


if __name__ == "__main__":
    main()
