from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Optional, Tuple


DEFAULT_TIMEOUT_S = 2.5


def fetch_json(base_url: str, path: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> Tuple[Optional[Any], Optional[str]]:
    """
    Fetch JSON from base_url + path.
    Returns: (data, error_message). Exactly one of them is None.
    """
    base = base_url.rstrip("/")
    p = path if path.startswith("/") else f"/{path}"
    url = f"{base}{p}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8")
        return json.loads(raw), None
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = ""
        return None, f"HTTP {e.code} for {p}: {body or e.reason}"
    except urllib.error.URLError as e:
        return None, f"URL error for {p}: {e.reason}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON for {p}: {e.msg}"
    except Exception as e:
        return None, f"Unexpected error for {p}: {e}"


def get_meta(base_url: str) -> Tuple[Optional[dict], Optional[str]]:
    data, err = fetch_json(base_url, "/meta")
    if err:
        return None, err
    if not isinstance(data, dict):
        return None, "Invalid /meta payload (expected object)"
    return data, None


def get_class(base_url: str, name: str) -> Tuple[Optional[dict], Optional[str]]:
    data, err = fetch_json(base_url, f"/classes/{name}")
    if err:
        return None, err
    if not isinstance(data, dict):
        return None, "Invalid /classes/{name} payload (expected object)"
    return data, None
