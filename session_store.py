"""Local session persistence for the Streamlit app.

P2 scope: save/load chat sessions + build versions.

Design goals:
- Zero new dependencies (JSON on disk).
- Safe for CI import/py_compile (no Streamlit access at import time).
- Works locally by default; storage location can be overridden via env var.

Storage:
- Default directory: .local/session_store
- Override with env var: DND_SESSION_STORE_DIR
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SessionSummary:
    session_id: str
    title: str
    updated_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_store_dir(store_dir: Optional[str | Path] = None) -> Path:
    """Return the session store directory, creating it if needed."""
    if store_dir is None:
        store_dir = os.getenv("DND_SESSION_STORE_DIR", ".local/session_store")
    path = Path(store_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def new_session_id() -> str:
    """Generate a short, URL-safe-ish session id."""
    return uuid.uuid4().hex[:12]


def _session_path(session_id: str, store_dir: Optional[str | Path] = None) -> Path:
    return get_store_dir(store_dir) / f"{session_id}.json"


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def save_session(payload: Dict[str, Any], store_dir: Optional[str | Path] = None) -> None:
    """Persist a full session payload to disk."""
    session_id = payload.get("session_id")
    if not session_id:
        raise ValueError("payload.session_id is required")

    now = _now_iso()
    payload.setdefault("created_at", now)
    payload["updated_at"] = now

    path = _session_path(session_id=session_id, store_dir=store_dir)
    _atomic_write_json(path, payload)


def load_session(session_id: str, store_dir: Optional[str | Path] = None) -> Dict[str, Any]:
    """Load a session payload from disk."""
    path = _session_path(session_id=session_id, store_dir=store_dir)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_sessions(store_dir: Optional[str | Path] = None, limit: int = 50) -> List[SessionSummary]:
    """List sessions sorted by updated_at (desc)."""
    base = get_store_dir(store_dir)
    summaries: List[SessionSummary] = []

    for p in base.glob("*.json"):
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            session_id = str(data.get("session_id") or p.stem)
            title = str(data.get("title") or "").strip()
            updated_at = str(data.get("updated_at") or "")
            summaries.append(SessionSummary(session_id=session_id, title=title, updated_at=updated_at))
        except Exception:
            continue

    summaries.sort(key=lambda s: s.updated_at, reverse=True)
    return summaries[:limit]


def create_build_version(
    *,
    messages: List[Dict[str, str]],
    build_level: int,
    homebrew: bool,
    label: str = "",
) -> Optional[Dict[str, Any]]:
    """Create a build-version record from the latest assistant message.

    Returns None if there is no non-empty assistant message yet.
    """
    latest_assistant = ""
    for m in reversed(messages):
        if m.get("role") == "assistant":
            latest_assistant = (m.get("content") or "").strip()
            break

    if not latest_assistant:
        return None

    return {
        "version_id": uuid.uuid4().hex[:12],
        "created_at": _now_iso(),
        "label": label.strip(),
        "build_level": int(build_level),
        "homebrew": bool(homebrew),
        "assistant_text": latest_assistant,
    }
