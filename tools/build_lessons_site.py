from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
import shutil
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "curriculum"
LESSONS_SRC = CURRICULUM / "lessons"
ASSETS_SRC = CURRICULUM / "assets"
SITE = ROOT / "site"
LESSONS_OUT = SITE / "lessons"
ASSETS_OUT = SITE / "assets"

sys.path.insert(0, str(CURRICULUM))
from learning_flow import load_manifest  # noqa: E402
from lint_lessons import lint  # noqa: E402


LOCAL_LINK_PATTERN = re.compile(
    r'<a href="(?:\.\./phase-1/[^"]+|\.\./reference/[^"]+|\./\.\./Harness[^"]+)">(.*?)</a>',
    re.DOTALL,
)
H1_PATTERN = re.compile(r"<h1>(.*?)</h1>", re.DOTALL)
EYEBROW_PATTERN = re.compile(r'<p class="eyebrow">(.*?)</p>', re.DOTALL)
TITLE_PATTERN = re.compile(r"<title>.*?</title>", re.DOTALL)
TAG_PATTERN = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class Lesson:
    source: Path
    output_name: str
    number: int
    technical_name: str
    memorable_phrase: str
    title: str
    eyebrow: str

    @property
    def lesson_id(self) -> str:
        return self.source.stem


def text_from_html(raw: str) -> str:
    without_tags = TAG_PATTERN.sub("", raw)
    return " ".join(without_tags.split())


def read_lesson(source: Path, config: dict[str, Any] | None = None) -> Lesson:
    html = source.read_text(encoding="utf-8")
    h1_match = H1_PATTERN.search(html)
    eyebrow_match = EYEBROW_PATTERN.search(html)

    authored_title = text_from_html(h1_match.group(1)) if h1_match else source.stem
    authored_eyebrow = text_from_html(eyebrow_match.group(1)) if eyebrow_match else "Project 1A"
    identity = config.get("identity", {}) if config else {}
    number = identity.get("number", 0)
    technical_name = identity.get("technical_name", authored_eyebrow)
    memorable_phrase = identity.get("memorable_phrase", authored_title)

    return Lesson(
        source=source,
        output_name=source.name,
        number=number,
        technical_name=technical_name,
        memorable_phrase=memorable_phrase,
        title=memorable_phrase,
        eyebrow=f"Primitive {number} · {technical_name}" if number else authored_eyebrow,
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


def nav_html(
    lessons: list[Lesson],
    index: int,
    *,
    total_lessons: int | None = None,
    bottom: bool = False,
) -> str:
    lesson = lessons[index]
    navigation_links: list[str] = []

    if index > 0:
        previous = lessons[index - 1]
        navigation_links.append(
            f'        <a href="{previous.output_name}" aria-label="Previous lesson">Previous</a>'
        )

    if index < len(lessons) - 1:
        next_lesson = lessons[index + 1]
        navigation_links.append(
            f'        <a href="{next_lesson.output_name}" aria-label="Next lesson">Next</a>'
        )

    nav_class = "site-nav bottom-nav" if bottom else "site-nav"
    joined_links = "\n".join(navigation_links)
    course_size = total_lessons if total_lessons is not None else len(lessons)

    return f"""
      <nav class="{nav_class}" aria-label="Course navigation">
        <a href="../index.html">Course Home</a>
        <span>Lesson {lesson.number} of {course_size} · {escape(lesson.technical_name)}</span>
        <div class="nav-spacer"></div>
{joined_links}
      </nav>
"""


def render_lesson(
    lessons: list[Lesson],
    index: int,
    *,
    total_lessons: int | None = None,
) -> str:
    lesson = lessons[index]
    html = lesson.source.read_text(encoding="utf-8")
    browser_title = f"Project 1A · {lesson.technical_name} · {lesson.memorable_phrase}"
    html = TITLE_PATTERN.sub(f"<title>{escape(browser_title)}</title>", html, count=1)
    html = strip_private_links(html)
    html = add_site_assets(html)
    html = html.replace(
        "<main>",
        "<main>" + nav_html(lessons, index, total_lessons=total_lessons),
        1,
    )
    html = re.sub(
        r"(?m)^[ \t]*</main>",
        nav_html(lessons, index, total_lessons=total_lessons, bottom=True) + "    </main>",
        html,
        count=1,
    )
    return html


def write_lessons(lessons: list[Lesson], *, total_lessons: int | None = None) -> None:
    for index, lesson in enumerate(lessons):
        output = render_lesson(lessons, index, total_lessons=total_lessons)
        (LESSONS_OUT / lesson.output_name).write_text(output, encoding="utf-8")


def write_locked_lessons(lessons: list[Lesson], manifest: dict[str, object]) -> None:
    for lesson in lessons:
        config = manifest["lessons"][lesson.lesson_id]
        reason = config["publication"]["reason"]
        html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Project 1A · {escape(lesson.technical_name)} · {escape(lesson.memorable_phrase)} — Upcoming</title>
    <link rel="stylesheet" href="../assets/course.css">
    <link rel="stylesheet" href="../assets/site.css">
  </head>
  <body>
    <main class="course-home">
      <p class="eyebrow">Primitive {lesson.number} · {escape(lesson.technical_name)} · Upcoming specification</p>
      <h1>{escape(lesson.memorable_phrase)}</h1>
      <p>This lesson is locked. Implement its prerequisite capability and produce runnable evidence before studying it as a completed lesson.</p>
      <p>{escape(reason)}</p>
      <p><a href="../index.html">Return to course home</a></p>
    </main>
  </body>
</html>
"""
        (LESSONS_OUT / lesson.output_name).write_text(html, encoding="utf-8")


def render_index(lessons: list[Lesson], locked_lessons: list[Lesson], manifest: dict[str, object]) -> str:
    lesson_rows = "\n".join(
        f"""
        <li>
          <a href="lessons/{lesson.output_name}">
            <strong>{escape(lesson.memorable_phrase)}</strong>
            <span class="lesson-technical">Primitive {lesson.number} · {escape(lesson.technical_name)}</span>
          </a>
        </li>"""
        for lesson in lessons
    )
    locked_rows = "\n".join(
        f"""
        <li class="lesson-locked">
          <div>
            <strong>{escape(lesson.memorable_phrase)}</strong>
            <span class="lesson-technical">Primitive {lesson.number} · {escape(lesson.technical_name)}</span>
            <small>Upcoming: {escape(manifest['lessons'][lesson.lesson_id]['publication']['reason'])}</small>
          </div>
        </li>"""
        for lesson in locked_lessons
    )
    all_lessons = sorted([*lessons, *locked_lessons], key=lambda lesson: lesson.number)
    course_map = "\n".join(
        f'        <div><span>{lesson.number}</span>{escape(lesson.technical_name)}</div>'
        for lesson in all_lessons
    )
    active_section = lesson_rows or "        <li>No lessons are published while the current primitives are rebuilt against evidence-first contracts.</li>"
    upcoming_section = (
        f"""
      <section>
        <h2>Upcoming work</h2>
        <ol class="lesson-index">{locked_rows}
        </ol>
      </section>"""
        if locked_rows else ""
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
{course_map}
      </section>

      <section>
        <h2>Lessons</h2>
        <ol class="lesson-index">
{active_section}
        </ol>
      </section>
{upcoming_section}
    </main>
  </body>
</html>
"""


def write_index(lessons: list[Lesson], locked_lessons: list[Lesson], manifest: dict[str, object]) -> None:
    (SITE / "index.html").write_text(render_index(lessons, locked_lessons, manifest), encoding="utf-8")


def main() -> None:
    manifest = load_manifest()
    lesson_sources = sorted(LESSONS_SRC.glob("*.html"))
    lesson_ids = {source.stem for source in lesson_sources}
    manifest_ids = set(manifest["lessons"])
    if lesson_ids != manifest_ids:
        missing = sorted(lesson_ids - manifest_ids)
        extra = sorted(manifest_ids - lesson_ids)
        raise ValueError(f"Lesson manifest mismatch. Missing: {missing}; extra: {extra}")
    lessons = [
        read_lesson(source, manifest["lessons"][source.stem])
        for source in lesson_sources
    ]
    lessons.sort(key=lambda lesson: lesson.number)

    lint_errors = lint(manifest)
    if lint_errors:
        raise ValueError("Lesson lint failed:\n" + "\n".join(lint_errors))

    published = [lesson for lesson in lessons if manifest["lessons"][lesson.lesson_id]["publication"]["status"] == "published"]
    locked = [lesson for lesson in lessons if manifest["lessons"][lesson.lesson_id]["publication"]["status"] == "locked"]

    clean_site()
    copy_assets()
    write_review_page()
    write_lessons(published, total_lessons=len(lessons))
    write_locked_lessons(locked, manifest)
    write_index(published, locked, manifest)


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

.course-map div span {
  color: var(--muted);
  display: block;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  margin-bottom: 2px;
  text-transform: uppercase;
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

.lesson-index .lesson-locked > div {
  background: #f4f1e9;
  border: 1px solid var(--line);
  border-radius: 8px;
  display: grid;
  gap: 3px;
  min-height: 72px;
  padding: 14px;
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
  display: block;
  font-size: 1.05rem;
  line-height: 1.35;
}

.lesson-index small {
  color: var(--muted);
  display: block;
  margin-top: 4px;
}

@media (max-width: 680px) {
  .site-nav.bottom-nav {
    padding-bottom: 92px;
  }
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
