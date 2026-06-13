"""UUID-keyed session store (PRD cross-device persistence shape).

In-memory for the first build slice; the interface is the contract, the
backing store can move to SQLite/DB without touching routes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from threading import Lock

_store: dict[str, dict] = {}
_lock = Lock()


def create_session() -> str:
    session_id = str(uuid.uuid4())
    with _lock:
        _store[session_id] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "address": None,
            "answers": {},
            "issues": [],
            "issues_submitted": False,
            "custom_issue": "",
            "facts": None,
            "plan": None,
        }
    return session_id


def get_session(session_id: str) -> dict | None:
    with _lock:
        return _store.get(session_id)


def reset_plan(session_id: str) -> None:
    session = get_session(session_id)
    if session is not None:
        session["plan"] = None
        # Drop cached property facts so a re-run fetches fresh county records.
        session["facts"] = None
