from pathlib import Path

import pytest

import session_store

pytestmark = pytest.mark.unit


def test_session_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DND_SESSION_STORE_DIR", str(tmp_path))

    sid = session_store.new_session_id()
    payload = {
        "session_id": sid,
        "title": "test",
        "params": {"build_level": 5, "homebrew": False, "openai_model": "gpt-4.1-mini"},
        "messages": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ],
        "versions": [],
    }

    session_store.save_session(payload)
    loaded = session_store.load_session(sid)

    assert loaded["session_id"] == sid
    assert loaded["title"] == "test"
    assert loaded["params"]["build_level"] == 5
    assert loaded["messages"][1]["content"] == "hi"


def test_create_build_version_requires_assistant_message() -> None:
    version = session_store.create_build_version(messages=[{"role": "user", "content": "x"}], build_level=5, homebrew=False)
    assert version is None

    version2 = session_store.create_build_version(
        messages=[
            {"role": "system", "content": "sys"},
            {"role": "assistant", "content": "draft"},
        ],
        build_level=5,
        homebrew=False,
        label="v1",
    )
    assert version2 is not None
    assert version2["assistant_text"] == "draft"
    assert version2["label"] == "v1"


def test_list_sessions_returns_saved_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DND_SESSION_STORE_DIR", str(tmp_path))

    sid = "abc123"
    session_store.save_session({"session_id": sid, "title": "", "params": {}, "messages": [], "versions": []})

    items = session_store.list_sessions(limit=10)
    assert any(s.session_id == sid for s in items)
