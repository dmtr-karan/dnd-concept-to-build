# dnd-concept-to-build

RP-first concept → playable D&D 5e build draft.

## Current state (v0.1)
- Streamlit chat app scaffold is working locally.
- **Public mode is SRD-only by design.**
- Optional **Homebrew** via UI toggle:
  - If Homebrew is OFF: SRD-only output.
  - If Homebrew is requested while OFF: the app stays SRD-only and suggests toggling Homebrew ON.

## Repo structure

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
    |       README.md
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

## Run locally
1) Create env var `OPENAI_API_KEY`
2) Install deps and run:
   - `pip install -r requirements.txt`
   - `streamlit run app.py`

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

## Notes
- This repo is a scaffold. Next planned work includes MongoDB persistence and an SRD-backed data layer.
