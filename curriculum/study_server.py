"""Serve the study site and persist learner data in a local SQLite database."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from learning_flow import ManifestError, lesson_config, load_manifest

ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "site"
DEFAULT_DATABASE = ROOT / "curriculum" / "data" / "study.sqlite3"
LESSON_ID = re.compile(r"^\d{4}-[a-z0-9-]+$")
STATUSES = {"not_started", "studying", "ready_to_implement", "review"}
PHASES = {
    "not_started",
    "studying",
    "ready_to_implement",
    "implementing",
    "consolidating",
    "learned",
}
MILESTONE_KEYS = {
    "prediction_committed",
    "case_set_passed",
    "artifact_inspected",
    "implementation_plan_ready",
    "proof_passed",
    "failure_explained",
    "regression_added",
    "reconstruction_passed",
    "recall_passed",
    "learning_record_written",
}
PHASE_ORDER = {
    "not_started": 0,
    "studying": 1,
    "ready_to_implement": 2,
    "implementing": 3,
    "consolidating": 4,
    "learned": 5,
}


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class StudyStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS lesson_study (
                    lesson_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'not_started',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS responses (
                    lesson_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    answer TEXT NOT NULL DEFAULT '',
                    self_assessment TEXT NOT NULL DEFAULT 'unrated',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (lesson_id, prompt_id),
                    FOREIGN KEY (lesson_id) REFERENCES lesson_study(lesson_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS implementation_plans (
                    lesson_id TEXT PRIMARY KEY,
                    target_function TEXT NOT NULL DEFAULT '',
                    smallest_slice TEXT NOT NULL DEFAULT '',
                    must_do TEXT NOT NULL DEFAULT '',
                    must_not_do TEXT NOT NULL DEFAULT '',
                    first_proof TEXT NOT NULL DEFAULT '',
                    open_question TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (lesson_id) REFERENCES lesson_study(lesson_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS reflections (
                    lesson_id TEXT PRIMARY KEY,
                    feynman_explanation TEXT NOT NULL DEFAULT '',
                    feynman_limit TEXT NOT NULL DEFAULT '',
                    prediction_vs_evidence TEXT NOT NULL DEFAULT '',
                    mental_model TEXT NOT NULL DEFAULT '',
                    next_step TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (lesson_id) REFERENCES lesson_study(lesson_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS learning_state (
                    lesson_id TEXT PRIMARY KEY,
                    phase TEXT NOT NULL DEFAULT 'not_started',
                    milestones_json TEXT NOT NULL DEFAULT '{}',
                    evidence_json TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (lesson_id) REFERENCES lesson_study(lesson_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
                    from_phase TEXT NOT NULL,
                    to_phase TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    FOREIGN KEY (lesson_id) REFERENCES lesson_study(lesson_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS review_schedule (
                    lesson_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    interval_index INTEGER NOT NULL DEFAULT 0,
                    last_reviewed_at TEXT,
                    PRIMARY KEY (lesson_id, kind),
                    FOREIGN KEY (lesson_id) REFERENCES lesson_study(lesson_id) ON DELETE CASCADE
                );
                """
            )
            self.ensure_columns(
                connection,
                "reflections",
                {
                    "feynman_explanation": "TEXT NOT NULL DEFAULT ''",
                    "feynman_limit": "TEXT NOT NULL DEFAULT ''",
                    "prediction_vs_evidence": "TEXT NOT NULL DEFAULT ''",
                },
            )

    def ensure_columns(
        self,
        connection: sqlite3.Connection,
        table: str,
        columns: dict[str, str],
    ) -> None:
        existing = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def load(self, lesson_id: str) -> dict[str, object]:
        with self.connect() as connection:
            study = connection.execute(
                "SELECT status, updated_at FROM lesson_study WHERE lesson_id = ?", (lesson_id,)
            ).fetchone()
            response_rows = connection.execute(
                "SELECT prompt_id, answer, self_assessment FROM responses WHERE lesson_id = ?",
                (lesson_id,),
            ).fetchall()
            plan = connection.execute(
                "SELECT target_function, smallest_slice, must_do, must_not_do, first_proof, open_question "
                "FROM implementation_plans WHERE lesson_id = ?",
                (lesson_id,),
            ).fetchone()
            reflection = connection.execute(
                "SELECT feynman_explanation, feynman_limit, prediction_vs_evidence, mental_model, next_step "
                "FROM reflections WHERE lesson_id = ?",
                (lesson_id,),
            ).fetchone()
            learning = connection.execute(
                "SELECT phase, milestones_json, evidence_json FROM learning_state WHERE lesson_id = ?",
                (lesson_id,),
            ).fetchone()
            event_rows = connection.execute(
                "SELECT event_id, event_type, source, evidence_refs_json, from_phase, to_phase, occurred_at "
                "FROM learning_events WHERE lesson_id = ? ORDER BY occurred_at DESC LIMIT 50",
                (lesson_id,),
            ).fetchall()
            review_rows = connection.execute(
                "SELECT kind, due_at, interval_index, last_reviewed_at FROM review_schedule "
                "WHERE lesson_id = ? ORDER BY due_at",
                (lesson_id,),
            ).fetchall()

        phase = learning["phase"] if learning else phase_for_status(study["status"] if study else "not_started")
        milestones = json.loads(learning["milestones_json"]) if learning else empty_milestones()
        evidence = json.loads(learning["evidence_json"]) if learning else empty_evidence()

        return {
            "lesson_id": lesson_id,
            "status": study["status"] if study else "not_started",
            "updated_at": study["updated_at"] if study else None,
            "responses": {row["prompt_id"]: dict(row) for row in response_rows},
            "plan": dict(plan) if plan else {},
            "reflection": dict(reflection) if reflection else {},
            "phase": phase,
            "milestones": {**empty_milestones(), **milestones},
            "evidence": {**empty_evidence(), **evidence},
            "events": [
                {
                    **{key: row[key] for key in row.keys() if key != "evidence_refs_json"},
                    "evidence_refs": json.loads(row["evidence_refs_json"]),
                }
                for row in event_rows
            ],
            "reviews": [dict(row) for row in review_rows],
        }

    def save(self, lesson_id: str, payload: dict[str, object]) -> dict[str, object]:
        status = payload.get("status", "studying")
        if status not in STATUSES:
            raise ValueError("Invalid lesson status.")

        responses = payload.get("responses", {})
        plan = payload.get("plan", {})
        reflection = payload.get("reflection", {})
        if not isinstance(responses, dict) or not isinstance(plan, dict) or not isinstance(reflection, dict):
            raise ValueError("Study data has an invalid shape.")

        timestamp = now()
        with self.connect() as connection:
            current_learning = connection.execute(
                "SELECT phase, milestones_json, evidence_json FROM learning_state WHERE lesson_id = ?",
                (lesson_id,),
            ).fetchone()
            current_phase = current_learning["phase"] if current_learning else "not_started"
            requested_phase = payload.get("phase")
            if requested_phase is None:
                requested_phase = phase_for_status(status)
                if PHASE_ORDER[requested_phase] < PHASE_ORDER[current_phase]:
                    requested_phase = current_phase
            if requested_phase not in PHASES:
                raise ValueError("Invalid lesson phase.")
            evidence = sanitize_evidence(
                payload.get("evidence"),
                json.loads(current_learning["evidence_json"]) if current_learning else None,
            )
            lesson = lesson_contract(lesson_id)
            milestones = derive_milestones(lesson, plan, reflection, evidence)
            validate_learning_transition(current_phase, requested_phase, milestones, lesson)
            connection.execute(
                "INSERT INTO lesson_study (lesson_id, status, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(lesson_id) DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at",
                (lesson_id, status, timestamp),
            )
            for prompt_id, response in responses.items():
                if not isinstance(prompt_id, str) or not isinstance(response, dict):
                    raise ValueError("Study response has an invalid shape.")
                answer = text_value(response.get("answer"))
                assessment = text_value(response.get("self_assessment"), "unrated")
                connection.execute(
                    "INSERT INTO responses (lesson_id, prompt_id, answer, self_assessment, updated_at) "
                    "VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(lesson_id, prompt_id) DO UPDATE SET "
                    "answer = excluded.answer, self_assessment = excluded.self_assessment, updated_at = excluded.updated_at",
                    (lesson_id, prompt_id[:80], answer, assessment[:32], timestamp),
                )
            connection.execute(
                "INSERT INTO implementation_plans "
                "(lesson_id, target_function, smallest_slice, must_do, must_not_do, first_proof, open_question, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(lesson_id) DO UPDATE SET target_function = excluded.target_function, "
                "smallest_slice = excluded.smallest_slice, must_do = excluded.must_do, "
                "must_not_do = excluded.must_not_do, first_proof = excluded.first_proof, "
                "open_question = excluded.open_question, updated_at = excluded.updated_at",
                (
                    lesson_id,
                    text_value(plan.get("target_function")),
                    text_value(plan.get("smallest_slice")),
                    text_value(plan.get("must_do")),
                    text_value(plan.get("must_not_do")),
                    text_value(plan.get("first_proof")),
                    text_value(plan.get("open_question")),
                    timestamp,
                ),
            )
            connection.execute(
                "INSERT INTO reflections "
                "(lesson_id, feynman_explanation, feynman_limit, prediction_vs_evidence, mental_model, next_step, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(lesson_id) DO UPDATE SET feynman_explanation = excluded.feynman_explanation, "
                "feynman_limit = excluded.feynman_limit, mental_model = excluded.mental_model, "
                "prediction_vs_evidence = excluded.prediction_vs_evidence, next_step = excluded.next_step, updated_at = excluded.updated_at",
                (
                    lesson_id,
                    text_value(reflection.get("feynman_explanation")),
                    text_value(reflection.get("feynman_limit")),
                    text_value(reflection.get("prediction_vs_evidence")),
                    text_value(reflection.get("mental_model")),
                    text_value(reflection.get("next_step")),
                    timestamp,
                ),
            )
            connection.execute(
                "INSERT INTO learning_state (lesson_id, phase, milestones_json, evidence_json, updated_at) "
                "VALUES (?, ?, ?, ?, ?) ON CONFLICT(lesson_id) DO UPDATE SET "
                "phase = excluded.phase, milestones_json = excluded.milestones_json, "
                "evidence_json = excluded.evidence_json, updated_at = excluded.updated_at",
                (
                    lesson_id,
                    requested_phase,
                    json.dumps(milestones, sort_keys=True),
                    json.dumps(evidence, sort_keys=True),
                    timestamp,
                ),
            )
            if requested_phase != current_phase:
                append_learning_event(
                    connection,
                    lesson_id=lesson_id,
                    event_type=event_for_phase(requested_phase),
                    source=text_value(payload.get("event_source"), "study-api")[:80],
                    evidence_refs=[],
                    from_phase=current_phase,
                    to_phase=requested_phase,
                    timestamp=timestamp,
                )
            schedule_kind = (
                "pre_implementation" if requested_phase == "ready_to_implement"
                else "retention" if requested_phase == "learned"
                else None
            )
            if schedule_kind:
                connection.execute(
                    "INSERT OR IGNORE INTO review_schedule "
                    "(lesson_id, kind, due_at, interval_index) VALUES (?, ?, ?, 0)",
                    (lesson_id, schedule_kind, (datetime.now(UTC) + timedelta(days=1)).isoformat(timespec="seconds")),
                )
        return self.load(lesson_id)

    def progress(self) -> list[dict[str, str]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT s.lesson_id, s.status, COALESCE(l.phase, s.status) AS phase, s.updated_at "
                "FROM lesson_study s LEFT JOIN learning_state l ON l.lesson_id = s.lesson_id "
                "ORDER BY s.lesson_id"
            ).fetchall()
        return [dict(row) for row in rows]

    def due_reviews(self, at: datetime | None = None) -> list[dict[str, object]]:
        cutoff = (at or datetime.now(UTC)).isoformat(timespec="seconds")
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT lesson_id, kind, due_at, interval_index, last_reviewed_at "
                "FROM review_schedule WHERE due_at <= ? ORDER BY due_at",
                (cutoff,),
            ).fetchall()
        return [dict(row) for row in rows]


def phase_for_status(status: str) -> str:
    return {
        "not_started": "not_started",
        "studying": "studying",
        "ready_to_implement": "ready_to_implement",
        "review": "studying",
    }[status]


def plan_is_complete(plan: object) -> bool:
    if not isinstance(plan, dict):
        return False
    required = ("target_function", "smallest_slice", "must_do", "must_not_do", "first_proof")
    return all(isinstance(plan.get(field), str) and plan[field].strip() for field in required)


def empty_milestones() -> dict[str, bool]:
    return {key: False for key in sorted(MILESTONE_KEYS)}


def empty_evidence() -> dict[str, object]:
    return {
        "practice_attempts": [],
        "artifact_inspections": [],
        "proof_runs": [],
        "trace_paths": [],
        "explainer_path": None,
        "failure_explanations": [],
        "regression_paths": [],
        "reconstruction_attempts": [],
        "recall_attempts": [],
        "learning_record_path": None,
    }


def sanitize_milestones(value: object, existing: dict[str, object] | None = None) -> dict[str, bool]:
    """Validate legacy payload shape; milestones are always derived from evidence."""
    result = {**empty_milestones(), **(existing or {})}
    if value is None:
        return {key: bool(result[key]) for key in sorted(MILESTONE_KEYS)}
    if not isinstance(value, dict) or set(value) - MILESTONE_KEYS:
        raise ValueError("Learning milestones have an invalid shape.")
    for key, enabled in value.items():
        if not isinstance(enabled, bool):
            raise ValueError("Learning milestones must be booleans.")
        result[key] = enabled
    return {key: bool(result[key]) for key in sorted(MILESTONE_KEYS)}


def sanitize_evidence(value: object, existing: dict[str, object] | None = None) -> dict[str, object]:
    result = {**empty_evidence(), **(existing or {})}
    if value is None:
        return result
    if not isinstance(value, dict) or set(value) - set(empty_evidence()):
        raise ValueError("Learning evidence has an invalid shape.")
    for key, item in value.items():
        if key in {
            "practice_attempts", "artifact_inspections", "proof_runs", "trace_paths",
            "failure_explanations", "regression_paths", "reconstruction_attempts", "recall_attempts",
        }:
            if not isinstance(item, list):
                raise ValueError(f"Evidence field {key} must be a list.")
            result[key] = item[-50:]
        elif item is not None and not isinstance(item, str):
            raise ValueError(f"Evidence field {key} must be text or null.")
        else:
            result[key] = item
    return result


def lesson_contract(lesson_id: str) -> dict[str, object]:
    try:
        return lesson_config(lesson_id, load_manifest())
    except ManifestError as error:
        raise ValueError(str(error)) from error


def has_textual_evidence(entries: object, *, key: str | None = None) -> bool:
    if not isinstance(entries, list):
        return False
    for entry in entries:
        if isinstance(entry, str) and entry.strip():
            return True
        if isinstance(entry, dict):
            value = entry.get(key, "") if key else next((item for item in entry.values() if isinstance(item, str)), "")
            if isinstance(value, str) and value.strip():
                return True
    return False


def derive_milestones(
    lesson: dict[str, object],
    plan: dict[str, object],
    reflection: dict[str, object],
    evidence: dict[str, object],
) -> dict[str, bool]:
    """Derive completion state from inspectable evidence; never trust browser booleans."""
    attempts = evidence.get("practice_attempts", [])
    prediction = any(
        isinstance(attempt, dict)
        and attempt.get("kind") == "prediction"
        and isinstance(attempt.get("selected"), str) and attempt["selected"].strip()
        and isinstance(attempt.get("rationale"), str) and attempt["rationale"].strip()
        for attempt in attempts if isinstance(attempts, list)
    )
    latest_cases: dict[str, bool] = {}
    if isinstance(attempts, list):
        for attempt in attempts:
            if not isinstance(attempt, dict) or attempt.get("kind") != "case":
                continue
            case_id = attempt.get("case_id")
            if isinstance(case_id, str) and case_id and isinstance(attempt.get("passed"), bool):
                latest_cases[case_id] = attempt["passed"]
    practice = lesson["practice_contract"]
    minimum = practice["minimum_cases"]
    threshold = practice["passing_threshold"]
    case_set_passed = len(latest_cases) >= minimum and (sum(latest_cases.values()) / len(latest_cases)) >= threshold
    proof_passed = any(
        isinstance(run, dict) and run.get("passed") is True
        for run in evidence.get("proof_runs", []) if isinstance(evidence.get("proof_runs", []), list)
    )
    reconstruction = lesson["reconstruction_contract"]
    reconstruction_passed = reconstruction["mode"] == "none" or any(
        isinstance(attempt, dict) and attempt.get("passed") is True
        for attempt in evidence.get("reconstruction_attempts", []) if isinstance(evidence.get("reconstruction_attempts", []), list)
    )
    recall_passed = any(
        isinstance(attempt, dict) and attempt.get("assessed_as") == "passed"
        for attempt in evidence.get("recall_attempts", []) if isinstance(evidence.get("recall_attempts", []), list)
    )
    record_path = evidence.get("learning_record_path")
    record_exists = False
    if isinstance(record_path, str) and record_path:
        candidate = (ROOT / record_path).resolve()
        record_exists = ROOT in candidate.parents and candidate.is_file()
    return {
        "prediction_committed": prediction,
        "case_set_passed": case_set_passed,
        "artifact_inspected": has_textual_evidence(evidence.get("artifact_inspections")),
        "implementation_plan_ready": plan_is_complete(plan),
        "proof_passed": proof_passed,
        "failure_explained": has_textual_evidence(evidence.get("failure_explanations"), key="explanation")
        or bool(text_value(reflection.get("feynman_explanation")).strip() and text_value(reflection.get("feynman_limit")).strip()),
        "regression_added": has_textual_evidence(evidence.get("regression_paths")),
        "reconstruction_passed": reconstruction_passed,
        "recall_passed": recall_passed,
        "learning_record_written": record_exists,
    }


def validate_learning_transition(
    from_phase: str,
    to_phase: str,
    milestones: dict[str, bool],
    lesson: dict[str, object],
) -> None:
    if PHASE_ORDER[to_phase] < PHASE_ORDER[from_phase]:
        raise ValueError("Lesson phase cannot move backward.")
    if lesson["publication"]["status"] == "locked" and to_phase == "learned":
        raise ValueError("Locked specifications cannot be marked learned.")
    required = {
        "ready_to_implement": ("prediction_committed", "case_set_passed", "implementation_plan_ready"),
        "consolidating": ("proof_passed",),
        "learned": ("failure_explained", "recall_passed", "learning_record_written"),
    }.get(to_phase, ())
    if lesson["reconstruction_contract"]["mode"] != "none" and to_phase == "learned":
        required = (*required, "reconstruction_passed")
    missing = [milestone for milestone in required if not milestones[milestone]]
    if missing:
        raise ValueError(f"Phase {to_phase} requires evidence for: {', '.join(missing)}.")


def event_for_phase(phase: str) -> str:
    return {
        "studying": "lesson.started",
        "ready_to_implement": "lesson.ready_to_implement",
        "implementing": "implementation.started",
        "consolidating": "implementation.proof_passed",
        "learned": "consolidation.recall_passed",
        "not_started": "lesson.reset",
    }[phase]


def append_learning_event(
    connection: sqlite3.Connection,
    *,
    lesson_id: str,
    event_type: str,
    source: str,
    evidence_refs: list[str],
    from_phase: str,
    to_phase: str,
    timestamp: str,
) -> None:
    connection.execute(
        "INSERT INTO learning_events "
        "(event_id, lesson_id, event_type, source, evidence_refs_json, from_phase, to_phase, occurred_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            str(uuid.uuid4()),
            lesson_id,
            event_type,
            source,
            json.dumps(evidence_refs),
            from_phase,
            to_phase,
            timestamp,
        ),
    )


def text_value(value: object, default: str = "") -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError("Study fields must be text.")
    return value[:12000]


class StudyRequestHandler(SimpleHTTPRequestHandler):
    store: StudyStore

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(SITE_ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        if parsed.path == "/api/health":
            self.respond_json({"ok": True})
            return
        if parsed.path == "/api/progress":
            self.respond_json({"lessons": self.store.progress()})
            return
        lesson_id = api_lesson_id(parsed.path)
        if lesson_id:
            self.respond_json(self.store.load(lesson_id))
            return
        self.serve_site_file(parsed.path)

    def do_PUT(self) -> None:  # noqa: N802
        lesson_id = api_lesson_id(urlparse(self.path).path)
        if not lesson_id:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown API endpoint")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 250_000:
                raise ValueError("Study payload is too large.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Study payload must be an object.")
            self.respond_json(self.store.save(lesson_id, payload))
        except (ValueError, json.JSONDecodeError) as error:
            self.respond_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def serve_site_file(self, request_path: str) -> None:
        relative_path = unquote(request_path).lstrip("/") or "index.html"
        target = (SITE_ROOT / relative_path).resolve()
        if SITE_ROOT not in target.parents and target != SITE_ROOT:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.path = "/" + str(target.relative_to(SITE_ROOT))
        super().do_GET()

    def respond_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def api_lesson_id(path: str) -> str | None:
    match = re.fullmatch(r"/api/lessons/([^/]+)/study", path)
    if not match:
        return None
    lesson_id = match.group(1)
    return lesson_id if LESSON_ID.fullmatch(lesson_id) else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()

    StudyRequestHandler.store = StudyStore(args.database)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), StudyRequestHandler)
    print(f"Study workspace: http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
