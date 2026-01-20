# dnd-concept-to-build

RP-first concept -> playable D&D 5e build draft (SRD-only by default).

## Current state (v0.1)
- Streamlit chat app scaffold works locally.
- **Public mode is SRD-only by design.**
- Optional **Homebrew** via UI toggle:
  - Homebrew OFF: SRD-only output.
  - If user requests homebrew while OFF: stay SRD-only and suggest enabling Homebrew.

## Why this project
- Portfolio-friendly Streamlit app that demonstrates **testable AI guardrails** and a repeatable “concept -> draft build” workflow.
- Focus: produce a practical **draft build outline** (not a full character sheet generator).
- Constraint: **SRD-only** output by default so the repo is safe to publish and easy to reproduce.

## SRD-only stance (public mode)
This repo intentionally stays **SRD-only**:
- No non-SRD classes/subclasses/species/backgrounds/spells/items.
- No non-SRD proper-noun setting/IP names.
- If Homebrew is enabled, any homebrew must be **explicitly labeled** as homebrew.

Docs:
- `docs/spec.md`
- `docs/ai-guardrails.md`

## Repo structure
```text
.
|   .gitignore
|   app.py
|   LICENSE
|   pytest.ini
|   requirements-dev.txt
|   requirements.txt
|
+---.github
|   \---workflows
|           ci.yml
|
+---docs
|       spec.md
|       ai-guardrails.md
|
\---tests
    |   test_import.py
    |   test_smoke.py
    |
    +---contract
    |       test_required_sections.py
    |       test_srd_only_mode_no_non_srd_names.py
    |
    \---unit
            test_guardrails_present.py
            test_hb_toggle_behavior.py
            test_no_empty_append.py
```

## Run locally
1) Create env var `OPENAI_API_KEY` (optionally via `.env` if supported by the app).
2) Install deps and run:
   - `pip install -r requirements.txt`
   - `streamlit run app.py`

## Run on Streamlit Community Cloud
1) Push this repo to GitHub (public).
2) Streamlit Community Cloud -> New app -> select repo/branch -> entry point `app.py`.
3) App -> Advanced settings -> Secrets:
   - Add `OPENAI_API_KEY` (and any other keys the app reads).

## Persistence (local-only)
This app supports local session persistence (save/load/versioning).

Storage:
- `.local/` (gitignored)

Notes:
- Loading is hardened (pending-load pattern) and enforces the system prompt at `messages[0]` on load.

## Testing
This repo uses `pytest` with markers:
- `unit`: fast tests (no network)
- `contract`: prompt/output invariants (no network)
- `integration`: reserved for external/system tests (not used yet)

Install test deps:
- `pip install -r requirements-dev.txt`

Run all tests:
- `python -m pytest`

Run only unit + contract (what CI runs):
- `python -m pytest -m "unit or contract"`

Run only unit:
- `python -m pytest -m unit`

Run only contract:
- `python -m pytest -m contract`

## Future work (out of scope for P3)
- P4: FastAPI SRD grounding service (backed by `dnd-srd-mongo`)
- P5: Export validators / formal contracts
- P6: UX polish beyond documentation references
