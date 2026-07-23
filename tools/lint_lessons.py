#!/usr/bin/env python3
"""Lint published Project 1A lessons against their evidence and practice contracts."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "curriculum"
sys.path.insert(0, str(CURRICULUM))

from learning_flow import load_manifest, resolve_repository_file  # noqa: E402


LOCAL_HREF = re.compile(r'''(?:href|src)=["']([^"']+)["']''')
TEST_IDENTIFIER = re.compile(r"\b(test_[A-Za-z0-9_]+)\b")
ERROR_CODE = re.compile(r"\b(?:[A-Z][A-Z0-9]*_){1,}[A-Z0-9]+\b")
CASE_ID = re.compile(r"\bdata-case-id=[\"'][^\"']+[\"']")
CHOICE_GROUP = re.compile(r"(<fieldset[^>]*data-case-id=[\"'][^\"']+[\"'][^>]*>)(.*?)</fieldset>", re.DOTALL)
OPTION = re.compile(r"<input[^>]*\bvalue=[\"']([^\"']+)[\"'][^>]*>", re.DOTALL)
ANSWER = re.compile(r"\bdata-answer=[\"']([^\"']+)[\"']")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")


def normalized_text(value: object) -> str:
    """Collapse presentation whitespace so authored prose can be compared safely."""
    return " ".join(str(value).split())


def curated_resource_urls(resources: Path = CURRICULUM / "RESOURCES.md") -> set[str]:
    """Return the exact link targets admitted by the curated resource catalog."""
    return set(MARKDOWN_LINK.findall(resources.read_text(encoding="utf-8")))


class LessonHTMLProbe(HTMLParser):
    """Collect the small amount of structure needed by the publication contract."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, dict[str, str | None]]] = []
        self.required_regions: set[str] = set()
        self.region_counts: dict[str, int] = {}
        self.obligations: list[str] = []
        self.unscoped_obligations: list[str] = []
        self.reveals: list[bool] = []
        self.unscoped_reveal_count = 0
        self.h1_text: list[str] = []
        self.title_text: list[str] = []
        self.eyebrow_text: list[str] = []
        self.metadata_text: list[str] = []
        self.reading_text: list[str] = []
        self.reading_hrefs: list[str] = []
        self.reading_cards: list[dict[str, Any]] = []
        self.reading_card_stack: list[tuple[int, int]] = []
        self.worked_example_count = 0
        self.unscoped_worked_example_count = 0

    @staticmethod
    def _attributes(attrs: list[tuple[str, str | None]]) -> dict[str, str | None]:
        return dict(attrs)

    def _inside(self, attribute: str) -> bool:
        return any(attribute in attrs for _, attrs in self.stack)

    def _inside_tag(self, tag_name: str) -> bool:
        return any(tag == tag_name for tag, _ in self.stack)

    def _inside_class(self, class_name: str) -> bool:
        return any(class_name in (attrs.get("class") or "").split() for _, attrs in self.stack)

    def _record_region(self, name: str) -> None:
        self.required_regions.add(name)
        self.region_counts[name] = self.region_counts.get(name, 0) + 1

    def _inside_lecture_scope(self, attributes: dict[str, str | None]) -> bool:
        return (
            "data-lecture" in attributes
            or "data-lecture-continuation" in attributes
            or self._inside("data-lecture")
            or self._inside("data-lecture-continuation")
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = self._attributes(attrs)

        if tag == "header" and "data-lesson-identity" in attributes:
            self._record_region("identity")
        if tag == "article" and "data-lecture" in attributes:
            self._record_region("lecture")
        if tag == "section" and "data-prediction" in attributes:
            self._record_region("prediction")
        if tag == "section" and "data-engineering-lab" in attributes:
            self._record_region("engineering_lab")
        if tag == "section" and "data-further-reading" in attributes:
            self._record_region("further_reading")

        lecture_context = self._inside_lecture_scope(attributes)
        obligation = attributes.get("data-lecture-obligation")
        if obligation:
            if lecture_context:
                self.obligations.append(obligation)
            else:
                self.unscoped_obligations.append(obligation)
        if "data-worked-example" in attributes:
            if lecture_context:
                self.worked_example_count += 1
            else:
                self.unscoped_worked_example_count += 1
        if attributes.get("data-lecture-reveal") == "after-prediction":
            self.reveals.append("hidden" in attributes)
            if not lecture_context:
                self.unscoped_reveal_count += 1

        if tag == "meta":
            content = attributes.get("content")
            if content:
                self.metadata_text.append(content)

        reading_context = self._inside("data-further-reading") or "data-further-reading" in attributes
        is_reading_card = (
            reading_context
            and (
                "data-reading-source" in attributes
                or "source-card" in (attributes.get("class") or "").split()
            )
        )
        if is_reading_card:
            card_index = len(self.reading_cards)
            self.reading_cards.append({"text": [], "hrefs": []})
            self.reading_card_stack.append((len(self.stack), card_index))
        if tag == "a" and reading_context and attributes.get("href"):
            href = attributes["href"] or ""
            self.reading_hrefs.append(href)
            if self.reading_card_stack:
                self.reading_cards[self.reading_card_stack[-1][1]]["hrefs"].append(href)

        self.stack.append((tag, attributes))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                while self.reading_card_stack and self.reading_card_stack[-1][0] >= index:
                    self.reading_card_stack.pop()
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if self._inside_tag("h1"):
            self.h1_text.append(data)
        if self._inside_tag("title"):
            self.title_text.append(data)
        if self._inside("data-lesson-identity") and self._inside_class("eyebrow"):
            self.eyebrow_text.append(data)
        if self._inside("data-further-reading"):
            self.reading_text.append(data)
        if self.reading_card_stack:
            self.reading_cards[self.reading_card_stack[-1][1]]["text"].append(data)


def lint_publication_contract(
    lesson_id: str,
    lesson: dict[str, Any],
    html: str,
    *,
    resource_urls: set[str] | None = None,
) -> list[str]:
    """Validate the learner-facing lecture, identity, and reading contract."""
    errors: list[str] = []
    probe = LessonHTMLProbe()
    probe.feed(html)

    required_regions = {
        "identity": "header[data-lesson-identity]",
        "lecture": "article[data-lecture]",
        "prediction": "section[data-prediction]",
        "engineering_lab": "section[data-engineering-lab]",
        "further_reading": "section[data-further-reading]",
    }
    for region, selector in required_regions.items():
        if region not in probe.required_regions:
            errors.append(f"{lesson_id}: published lesson requires {selector}")
    if probe.region_counts.get("prediction", 0) > 1:
        errors.append(f"{lesson_id}: published lesson must have exactly one section[data-prediction]")

    identity = lesson.get("identity", {})
    number = identity.get("number")
    technical_name = normalized_text(identity.get("technical_name", ""))
    memorable_phrase = normalized_text(identity.get("memorable_phrase", ""))
    h1 = normalized_text("".join(probe.h1_text))
    eyebrow = normalized_text("".join(probe.eyebrow_text))
    metadata = normalized_text(" ".join(probe.metadata_text))
    browser_title = normalized_text("".join(probe.title_text))
    expected_title = f"Project 1A · {technical_name} · {memorable_phrase}"

    if h1 != memorable_phrase:
        errors.append(f"{lesson_id}: H1 must equal the memorable phrase: {memorable_phrase}")
    if browser_title != expected_title:
        errors.append(f"{lesson_id}: browser title must be: {expected_title}")
    identity_context = f"{eyebrow} {metadata}"
    if technical_name not in identity_context or f"Primitive {number}" not in identity_context:
        errors.append(
            f"{lesson_id}: lesson identity must name Primitive {number} and {technical_name} in its eyebrow or metadata"
        )

    lecture = lesson.get("lecture_contract", {})
    declared_obligations = {
        item.get("id")
        for item in lecture.get("explanatory_obligations", [])
        if isinstance(item, dict) and item.get("id")
    }
    present_obligations = set(probe.obligations)
    for obligation_id in sorted(declared_obligations - present_obligations):
        errors.append(f"{lesson_id}: lecture is missing explanatory obligation: {obligation_id}")
    for obligation_id in sorted(present_obligations - declared_obligations):
        errors.append(f"{lesson_id}: lesson publishes undeclared explanatory obligation: {obligation_id}")
    for obligation_id in sorted(set(probe.unscoped_obligations)):
        errors.append(
            f"{lesson_id}: explanatory obligation must be inside article[data-lecture] "
            f"or an explicit data-lecture-continuation: {obligation_id}"
        )
    if not probe.worked_example_count:
        errors.append(f"{lesson_id}: lecture requires a data-worked-example region")
    if probe.unscoped_worked_example_count:
        errors.append(
            f"{lesson_id}: data-worked-example must be inside article[data-lecture] "
            "or an explicit data-lecture-continuation"
        )
    if any(not initially_hidden for initially_hidden in probe.reveals):
        errors.append(f"{lesson_id}: after-prediction lecture reveals must be hidden initially")
    if probe.unscoped_reveal_count:
        errors.append(
            f"{lesson_id}: after-prediction lecture reveals require an explicit lecture scope"
        )

    reading = lesson.get("reading_contract", {})
    reading_entries = [
        ("Primary source", reading.get("primary")),
        *(("Go deeper", entry) for entry in reading.get("further", [])),
    ]
    reading_entries = [
        (kind, entry)
        for kind, entry in reading_entries
        if isinstance(entry, dict)
    ]
    reading_hrefs = set(probe.reading_hrefs)
    admitted_urls = resource_urls if resource_urls is not None else curated_resource_urls()
    contracted_urls = {entry.get("url", "") for _, entry in reading_entries}

    for href in reading_hrefs:
        if not href.startswith(("https://", "http://")):
            continue
        if href not in admitted_urls:
            errors.append(f"{lesson_id}: reading URL is absent from RESOURCES.md: {href}")
        if href not in contracted_urls:
            errors.append(f"{lesson_id}: further reading links an uncontracted external source: {href}")

    for expected_kind, entry in reading_entries:
        url = entry.get("url", "")
        title = normalized_text(entry.get("title", ""))
        annotation = normalized_text(entry.get("why", ""))
        if url not in admitted_urls:
            errors.append(f"{lesson_id}: reading URL is absent from RESOURCES.md: {url}")
        if url not in reading_hrefs:
            errors.append(f"{lesson_id}: further reading does not link its contracted URL: {url}")
        matching_cards = [
            card
            for card in probe.reading_cards
            if url in card["hrefs"]
        ]
        if len(matching_cards) != 1:
            errors.append(f"{lesson_id}: contracted reading must appear in exactly one source card: {url}")
            continue
        card_text = normalized_text(" ".join(matching_cards[0]["text"]))
        if title and title not in card_text:
            errors.append(f"{lesson_id}: further reading is missing its source title: {title}")
        if annotation and annotation not in card_text:
            errors.append(f"{lesson_id}: further reading is missing its lesson-specific annotation for: {title}")
        if expected_kind == "Primary source" and expected_kind not in card_text:
            errors.append(f"{lesson_id}: reading card for {title} must be labeled {expected_kind}")
        if expected_kind != "Primary source" and "Primary source" in card_text:
            errors.append(f"{lesson_id}: further reading card for {title} cannot be labeled Primary source")

    return errors


def bound_files(lesson: dict[str, Any]) -> list[Path]:
    paths: list[str] = []
    for contract_name in ("starting_artifacts", "target_artifacts"):
        contract = lesson[contract_name]
        paths.extend(contract["source_files"])
        paths.extend(contract["tests"])
        paths.extend(contract.get("scenario_sources", []))
    paths.append(lesson["failure_contract"]["source"])
    paths.extend(lesson["proof_artifacts"]["traces_or_output"])
    paths.extend(
        argument
        for argument in lesson["proof_artifacts"]["proof_command"]
        if argument.endswith((".py", ".json", ".txt", ".yaml", ".yml")) or "/" in argument
    )
    return [resolve_repository_file("lesson", path, "bound artifact") for path in dict.fromkeys(paths)]


def lint_lesson(lesson_id: str, lesson: dict[str, Any], source: Path) -> list[str]:
    """Return all publishing errors for one lesson source."""
    errors: list[str] = []
    html = source.read_text(encoding="utf-8")
    errors.extend(lint_publication_contract(lesson_id, lesson, html))
    files = bound_files(lesson)
    bound_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files)
    starting_files = [
        resolve_repository_file(lesson_id, path, "starting artifact")
        for path in lesson["starting_artifacts"]["source_files"]
    ]
    starting_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in starting_files)

    for href in LOCAL_HREF.findall(html):
        if href.startswith(("https://", "http://", "#", "mailto:")):
            continue
        candidate = (source.parent / href).resolve()
        if ROOT not in candidate.parents or not candidate.is_file():
            errors.append(f"{lesson_id}: linked repository artifact does not exist: {href}")

    command = lesson["proof_artifacts"]["proof_command"]
    if not command:
        errors.append(f"{lesson_id}: published lesson has no runnable proof")

    for test_name in set(TEST_IDENTIFIER.findall(html)) | set(lesson["proof_artifacts"]["assertions"]):
        if test_name not in bound_text:
            errors.append(f"{lesson_id}: referenced test identifier drifted: {test_name}")

    for symbol in lesson["starting_artifacts"]["symbols"]:
        if not re.search(rf"\b{re.escape(symbol)}\b", starting_text):
            errors.append(f"{lesson_id}: declared starting symbol does not exist: {symbol}")

    for code in set(ERROR_CODE.findall(html)):
        if code not in bound_text:
            errors.append(f"{lesson_id}: error code is not present in bound artifacts: {code}")

    if re.search(r"\bdoes not yet (?:provide|exist|support|implement)\b", html, re.IGNORECASE):
        errors.append(f"{lesson_id}: published lesson claims an unavailable capability")

    if "data-prediction-submit" not in html or "data-prediction-answer" not in html:
        errors.append(f"{lesson_id}: prediction commitment and deferred answer are required")
    elif html.index("data-prediction-answer") < html.index("data-prediction-submit"):
        errors.append(f"{lesson_id}: prediction answer appears before commitment")

    minimum_cases = lesson["practice_contract"]["minimum_cases"]
    case_count = len(CASE_ID.findall(html))
    if case_count < minimum_cases:
        errors.append(f"{lesson_id}: practice has {case_count} cases; contract requires {minimum_cases}")
    if "data-rationale" not in html:
        errors.append(f"{lesson_id}: practice must collect a written rationale")
    if "data-feedback" not in html:
        errors.append(f"{lesson_id}: practice needs boundary feedback")

    positions: list[int] = []
    for opening_tag, contents in CHOICE_GROUP.findall(html):
        answer_match = ANSWER.search(opening_tag + contents)
        choices = OPTION.findall(contents)
        if not answer_match or answer_match.group(1) not in choices:
            errors.append(f"{lesson_id}: case is missing a valid answer choice")
            continue
        positions.append(choices.index(answer_match.group(1)))
    if positions and len(set(positions)) == 1:
        errors.append(f"{lesson_id}: correct answer positions are degenerate")
    if case_count and len(positions) != case_count:
        errors.append(f"{lesson_id}: every practice case must use a case-set choice group")

    return errors


def lint(manifest: dict[str, Any], lessons_dir: Path = CURRICULUM / "lessons") -> list[str]:
    errors: list[str] = []
    for lesson_id, lesson in manifest["lessons"].items():
        if lesson["publication"]["status"] != "published":
            continue
        source = lessons_dir / f"{lesson_id}.html"
        if not source.is_file():
            errors.append(f"{lesson_id}: published lesson source is missing")
            continue
        errors.extend(lint_lesson(lesson_id, lesson, source))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=CURRICULUM / "learning-flow.json")
    parser.add_argument("--lessons-dir", type=Path, default=CURRICULUM / "lessons")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    errors = lint(manifest, args.lessons_dir)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("Lesson lint passed.")


if __name__ == "__main__":
    main()
