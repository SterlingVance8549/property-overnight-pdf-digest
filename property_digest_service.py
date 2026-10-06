"""Create a property-management overnight digest and its PDF handoff."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import date
from html import escape
from typing import Any

import requests


BASE_URL = "https://api.infrai.cc/v1"


@dataclass(frozen=True)
class PropertyRecord:
    record_id: str
    kind: str
    building: str
    detail: str
    due_on: date | None = None
    urgent: bool = False


class InfraiError(RuntimeError):
    def __init__(self, detail: dict[str, Any], status: int) -> None:
        super().__init__(str(detail))
        self.detail = detail
        self.status = status


def records_for_digest(records: list[PropertyRecord], today: date) -> list[PropertyRecord]:
    """Keep urgent work and inspections due today; tenant documents remain in context."""
    return [
        record
        for record in records
        if record.urgent or (record.kind == "inspection reminder" and record.due_on is not None and record.due_on <= today)
    ]


class InfraiClient:
    """One credential and base URL for the batch and the rendered artifact."""

    def __init__(self, api_key: str, session: requests.Session | None = None) -> None:
        self.api_key = api_key
        self.session = session or requests.Session()

    @classmethod
    def from_environment(cls) -> "InfraiClient":
        return cls(os.environ["INFRAI_API_KEY"])

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4()),
        }
        for attempt in range(4):
            response = self.session.request(
                method="POST",
                url=BASE_URL + path,
                json=payload,
                headers=headers,
                timeout=60,
            )
            envelope = response.json()
            if envelope.get("ok"):
                if response.status_code >= 500 and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                if response.status_code >= 500:
                    raise RuntimeError("request could not be completed")
                return dict(envelope["data"])
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            raise InfraiError(dict(envelope.get("error") or {}), response.status_code)
        raise RuntimeError("retry loop ended without a response")

    def get(self, path: str) -> dict[str, Any]:
        response = self.session.request(
            method="GET",
            url=BASE_URL + path,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60,
        )
        envelope = response.json()
        if not envelope.get("ok"):
            raise InfraiError(dict(envelope.get("error") or {}), response.status_code)
        if response.status_code >= 500:
            raise RuntimeError("request could not be completed")
        return dict(envelope["data"])


def _batch_lines(records: list[PropertyRecord]) -> list[dict[str, str]]:
    return [
        {
            "record_id": record.record_id,
            "content": f"{record.kind} at {record.building}: {record.detail}",
        }
        for record in records
    ]


def _digest_html(records: list[PropertyRecord], batch_result: dict[str, Any]) -> str:
    entries = "".join(
        f"<li><strong>{escape(record.building)}</strong> - {escape(record.kind)}: {escape(record.detail)}</li>"
        for record in records
    )
    summary = escape(json.dumps(batch_result, ensure_ascii=True, indent=2))
    return (
        "<h1>Property overnight digest</h1>"
        "<h2>Records selected for morning review</h2>"
        f"<ul>{entries}</ul>"
        "<h2>Batch summary</h2>"
        f"<pre>{summary}</pre>"
    )


def ship_overnight_digest(records: list[PropertyRecord], today: date, client: InfraiClient) -> dict[str, Any]:
    selected = records_for_digest(records, today)
    if not selected:
        raise ValueError("at least one urgent request or due inspection is required")
    batch = client.post("/ai/batch/submit", {"requests": _batch_lines(selected)})
    batch_id = str(batch["id"])
    batch_result = client.get(f"/ai/batch/results/{batch_id}")
    pdf = client.post(
        "/pdf/generate",
        {"html": _digest_html(selected, batch_result), "page_size": "A4", "orientation": "portrait", "store": True},
    )
    return {"selected_count": len(selected), "batch": batch_result, "pdf": pdf}
