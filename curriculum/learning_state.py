"""Use the configured remote learner store, falling back to local SQLite."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from study_server import DEFAULT_DATABASE, StudyStore


class LearnerStateBackend(Protocol):
    def load(self, lesson_id: str) -> dict[str, Any]: ...
    def save(self, lesson_id: str, payload: dict[str, object]) -> dict[str, Any]: ...


class RemoteStudyStore:
    def __init__(self, site_url: str, token: str) -> None:
        self.site_url = site_url.rstrip("/")
        self.token = token

    def request(self, lesson_id: str, *, payload: dict[str, object] | None = None) -> dict[str, Any]:
        url = f"{self.site_url}/api/lessons/{lesson_id}/study"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            url,
            data=body,
            method="PUT" if payload is not None else "GET",
            headers={
                "X-Study-Token": self.token,
                **({"Content-Type": "application/json"} if body is not None else {}),
            },
        )
        try:
            with urlopen(request, timeout=20) as response:
                result = json.load(response)
        except (URLError, TimeoutError) as error:
            raise RuntimeError(f"Remote study state request failed: {error}") from error
        if not isinstance(result, dict):
            raise RuntimeError("Remote study state returned an invalid payload.")
        return result

    def load(self, lesson_id: str) -> dict[str, Any]:
        return self.request(lesson_id)

    def save(self, lesson_id: str, payload: dict[str, object]) -> dict[str, Any]:
        return self.request(lesson_id, payload=payload)

    def due_reviews(self) -> list[dict[str, object]]:
        request = Request(
            f"{self.site_url}/api/reviews/due",
            headers={"X-Study-Token": self.token},
        )
        try:
            with urlopen(request, timeout=20) as response:
                result = json.load(response)
        except HTTPError as error:
            if error.code == 404:
                return []
            raise RuntimeError(f"Remote review request failed: {error}") from error
        except (URLError, TimeoutError) as error:
            raise RuntimeError(f"Remote review request failed: {error}") from error
        reviews = result.get("reviews", []) if isinstance(result, dict) else []
        if not isinstance(reviews, list):
            raise RuntimeError("Remote review state returned an invalid payload.")
        return reviews


def state_backend(database: Path = DEFAULT_DATABASE, *, prefer_remote: bool = True) -> LearnerStateBackend:
    site_url = os.environ.get("STUDY_SITE_URL", "").strip()
    token = os.environ.get("STUDY_ACCESS_TOKEN", "").strip()
    if prefer_remote and site_url and token:
        return RemoteStudyStore(site_url, token)
    return StudyStore(database)
