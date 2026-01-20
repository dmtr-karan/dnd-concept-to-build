# Spec — dnd-concept-to-build (P3)

This document specifies observable app behavior, state, and basic data contracts.
SRD-only policy details are in `docs/ai-guardrails.md`.

---

## Scope
In scope (P3):
- Document SRD-only stance and app behavior.
- Document local persistence model and expected session snapshot shape.
- Document state invariants enforced by the app.

Out of scope:
- DMV import/export
- FastAPI SRD service (P4)
- Export validators/contracts (P5)
- UX polish beyond documentation references (P6)

---

## User flow
1) User provides an RP concept and constraints.
2) App generates a draft build outline under SRD-only guardrails.
3) User iterates via chat.
4) User optionally persists the session locally (save/load/versioning).

---

## State model (Streamlit session_state)

### Primary state
- `messages`: list of chat messages (dicts with `role` + `content`).
  - Invariant: `messages[0]` is always the system message.
  - Rendering excludes the system message.

### Persistence control state
The load path is hardened to avoid partial state:
- A “pending-load” selection is staged first.
- The in-memory session is replaced atomically.
- After load, the app ensures `messages[0]` is the system message.

(Implementation details live in `app.py` / `session_store.py`.)

---

## Local persistence

### Location
- `.local/session_store/`
- `.local/` is gitignored.

### Operations
- Save: stores the current session snapshot.
- Save version: stores a versioned snapshot (timestamp or incrementing scheme).
- Load: loads a chosen snapshot into session state via the hardened load flow.
- New Build: resets to a clean initial state.

### Session snapshot contract (minimum)
A stored snapshot should be JSON with at least:
- `messages`: list of `{ "role": "...", "content": "..." }`

Recommended fields (if you already store them or plan to):
- `schema_version`
- `created_at` (ISO8601)
- `app_version`
- `concept_inputs` (if captured separately from chat)

If a snapshot is invalid/corrupt, the app should fail safely (no partial load).

---

## AI output contract (high-level)
Assistant outputs must:
- Stay SRD-only by default.
- Avoid non-SRD names/proper nouns.
- If homebrew is enabled/explicitly requested, clearly label it as homebrew.
- Avoid “quoting rules text”; summarize and guide instead.

---

## Error handling expectations
- Missing secrets: show a clear message and stop safely.
- Invalid session file: show a clear message; do not partially load.
- Loaded messages missing a system prompt: repair by re-inserting system prompt at index 0.