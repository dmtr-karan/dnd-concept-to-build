# dnd-concept-to-build

RP-first concept → playable D&D 5e build draft.

## Current state (v0.1)
- Streamlit chat app scaffold is working locally.
- **Public mode is SRD-only by design.**
- Optional **Homebrew** via UI toggle:
  - If Homebrew is OFF: SRD-only output.
  - If Homebrew is requested while OFF: the app stays SRD-only and suggests toggling Homebrew ON.

## Run locally
1) Create env var `OPENAI_API_KEY`
2) Install deps and run:
   - `pip install -r requirements.txt`
   - `streamlit run app.py`

## Notes
- This repo is a scaffold. Next planned work includes MongoDB persistence and an SRD-backed data layer.
