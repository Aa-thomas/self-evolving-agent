"""Serve the study site and persist learner data in a local SQLite database."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "site"
DEFAULT_DATABASE = ROOT / "curriculum" / "data" / "study.sqlite3"
LESSON_ID = re.compile(r"^\d{4}-[a-z0-9-]+$")
STATUSES = {"not_started", "studying", "ready_to_implement", "review"}


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
                    mental_model TEXT NOT NULL DEFAULT '',
                    next_step TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
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
                "SELECT feynman_explanation, feynman_limit, mental_model, next_step "
                "FROM reflections WHERE lesson_id = ?",
                (lesson_id,),
            ).fetchone()

        return {
            "lesson_id": lesson_id,
            "status": study["status"] if study else "not_started",
            "updated_at": study["updated_at"] if study else None,
            "responses": {row["prompt_id"]: dict(row) for row in response_rows},
            "plan": dict(plan) if plan else {},
            "reflection": dict(reflection) if reflection else {},
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
                "(lesson_id, feynman_explanation, feynman_limit, mental_model, next_step, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(lesson_id) DO UPDATE SET feynman_explanation = excluded.feynman_explanation, "
                "feynman_limit = excluded.feynman_limit, mental_model = excluded.mental_model, "
                "next_step = excluded.next_step, updated_at = excluded.updated_at",
                (
                    lesson_id,
                    text_value(reflection.get("feynman_explanation")),
                    text_value(reflection.get("feynman_limit")),
                    text_value(reflection.get("mental_model")),
                    text_value(reflection.get("next_step")),
                    timestamp,
                ),
            )
        return self.load(lesson_id)

    def progress(self) -> list[dict[str, str]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT lesson_id, status, updated_at FROM lesson_study ORDER BY lesson_id"
            ).fetchall()
        return [dict(row) for row in rows]


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
