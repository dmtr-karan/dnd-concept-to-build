"""D&D Concept-to-Build (RP-first).

Current stage: base app imported from interview simulator.
We are only re-skinning UI text in this step (no logic changes yet).
"""

import os

import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
# Optional local dev: load .env if python-dotenv is installed.
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

import session_store

# ---------- Secrets & client setup (unified) ----------
def get_required_secret(name: str) -> str:
    """Return required secret from env (local) or st.secrets (Cloud); stop app with a helpful error if missing."""
    # Prefer env var locally (avoids StreamlitSecretNotFoundError in dev)
    value = os.getenv(name)
    if not value:
        try:
            value = st.secrets[name]  # Cloud
        except Exception:
            value = None

    if not value:
        st.error(
            f"Missing required secret: {name}. "
            "Set it as an environment variable locally or in Streamlit Cloud (Advanced settings → Secrets)."
        )
        st.stop()
    return value


@st.cache_resource(show_spinner=False)
def get_openai_client() -> OpenAI:
    """Create and cache the OpenAI client using the resolved API key."""
    api_key = get_required_secret("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def should_append_assistant_message(text: str) -> bool:
    """Rule: never append empty assistant messages to history."""
    return bool(text.strip())


def build_system_prompt(build_level: int, homebrew: bool) -> str:
    """Build the system prompt (pure function; safe to unit-test)."""
    return (
        "You are a D&D 5e assistant that turns a roleplay-first character concept into a playable build draft. "
        "This PUBLIC app is SRD-only by design: do not rely on non-SRD sources.\n\n"
        "Hard rule:\n"
        "- If you are not sure an option is in SRD, do not name it; instead say 'SRD limitation' and offer a generic SRD-safe alternative (e.g., base class choice + ASIs + generic spell themes).\n"
        "- Only recommend options that exist in the SRD dataset shipped with this app.\n"
        "- Never claim you are 'set to SRD-only mode' if Homebrew is ON. Always follow the UI Homebrew toggle.\n"
        "- If the user requests homebrew (e.g., says 'HB', 'homebrew', 'invent') AND Homebrew is OFF: do not generate homebrew. Instead, proceed SRD-only and add one final line: 'Want homebrew elements? Toggle Homebrew ON in the UI and ask again.'\n"
        "- If the user asks a meta question like '12th lvl ok?', answer briefly (e.g., 'Yes') and ask for the concept template; do NOT restate the current Target level from constraints.\n"
        "- Never ask the user whether to stick to SRD-only vs homebrew; follow the UI setting. Only ask for the character concept if missing.\n"
        "- If the concept suggests a non-SRD subclass/spell/feat, say it's unavailable in SRD and offer a generic SRD-safe alternative without naming non-SRD options.\n"
        "- Do not mention non-SRD options by name (even to disclaim them). Just say 'SRD limitation' and proceed with SRD-safe choices.\n"
        "- Never invent subclass names. If you cannot name a subclass with certainty as SRD, do not name any subclass.\n"
        "- If subclass is uncertain: write 'Subclass: SRD limitation (not specified)' and proceed with a class-first build using SRD-safe spell/ASI suggestions.\n\n"
        f"Constraints:\n"
        f"- Target level: {build_level}\n"
        f"- Homebrew: {'ON' if homebrew else 'OFF'} "
        "(If ON: you MAY invent RP-flavored options, but label them clearly as HOMEBREW.)\n\n"
        "Output style:\n"
        "- Decide fast: If the user message is a CONCEPT (even vague, e.g., two words), proceed with a best-effort draft immediately and ask at most ONE follow-up question at the end. If the user message is NOT a concept, reply with: (a) a one-line confirmation, then (b) ONE request for a one-sentence concept using this template: '<fantasy vibe> <class vibe> <key motif> <tone>'.\n"
        "- Do not restate constraints unless you are actually producing a build draft.\n"
        "- Provide: (1) Concept summary, (2) Class: <name>. Subclass: <name or 'SRD limitation (not specified)'>. RP rationale, "
        "(3) Key feature milestones up to the target level, (4) Spell suggestions if applicable (SRD-only), "
        "(5) In SRD-only mode: prefer ASIs; only mention feats if you are certain they are SRD-available, otherwise explicitly skip feats, "
        "(6) Short RP hooks (2–4 bullets).\n"
        "- Keep it concise and practical. No copyrighted text.\n"
    )


def main() -> None:
    # ---------- Page config ----------
    st.set_page_config(page_title="D&D Concept-to-Build", page_icon="🧙")

    st.title("🧙 D&D Concept-to-Build")
    st.caption("RP-first concept → build draft (base app imported; re-skin step).")

    client = get_openai_client()

    # ---------- Session state ----------
    defaults = {
        "setup_complete": False,
        "user_message_count": 0,
        "feedback_shown": False,
        "chat_complete": False,
        "messages": [],
        "openai_model": "gpt-4.1-mini",
        # Stop-control state
        "stop_requested": False,
        # mark if Stop was pressed before any user message
        "stopped_early": False,
        # Idea #5 controls (public repo = SRD-only; no other sources shipped)
        "build_level": 5,
        "is_generating": False,
        "homebrew": False,
        # P2 persistence
        "session_id": "",
        "session_title": "",
        "build_versions": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Ensure we have a session_id for persistence
    if not st.session_state.get("session_id"):
        st.session_state["session_id"] = session_store.new_session_id()

    # Apply pending load BEFORE any widgets are created (Streamlit constraint)
    pending = st.session_state.pop("_pending_load_payload", None)
    if pending is not None:
        params = pending.get("params", {})

        st.session_state["session_id"] = pending.get("session_id") or session_store.new_session_id()
        st.session_state["session_title"] = pending.get("title", "")
        st.session_state["build_versions"] = pending.get("versions", [])

        st.session_state["build_level"] = int(params.get("build_level", st.session_state.get("build_level", 5)))
        st.session_state["homebrew"] = bool(params.get("homebrew", st.session_state.get("homebrew", False)))
        st.session_state["openai_model"] = params.get(
            "openai_model",
            st.session_state.get("openai_model", "gpt-4.1-mini"),
        )

        loaded_messages = pending.get("messages", []) or []

        # Ensure system message at index 0 and refresh it from current params
        system_prompt = build_system_prompt(
            build_level=int(st.session_state.get("build_level", 5)),
            homebrew=bool(st.session_state.get("homebrew", False)),
        )

        if not loaded_messages:
            loaded_messages = [{"role": "system", "content": system_prompt}]
        elif loaded_messages[0].get("role") != "system":
            loaded_messages.insert(0, {"role": "system", "content": system_prompt})
        else:
            loaded_messages[0]["content"] = system_prompt

        st.session_state["messages"] = loaded_messages
        st.session_state["setup_complete"] = True
        st.session_state["chat_complete"] = False
        st.session_state["stop_requested"] = False
        st.session_state["is_generating"] = False

        st.rerun()

    def complete_setup() -> None:
        st.session_state.setup_complete = True

    def request_stop() -> None:
        st.session_state.stop_requested = True
        if st.session_state.user_message_count == 0:
            st.session_state.stopped_early = True
        st.session_state.chat_complete = True

    def reset_build() -> None:
        """Reset all state to start a brand-new build."""
        st.session_state.setup_complete = False
        st.session_state.chat_complete = False
        st.session_state.messages = []
        st.session_state.stop_requested = False
        st.session_state.stopped_early = False
        st.session_state.is_generating = False
        st.session_state.user_message_count = 0
        st.session_state.build_versions = []
        st.session_state.session_title = ""
        st.session_state.session_id = session_store.new_session_id()

    # ---------- Setup stage ----------
    if not st.session_state.setup_complete:
        st.subheader("Concept Setup")

        st.session_state["build_level"] = st.selectbox(
            "Character level",
            options=list(range(1, 21)),
            index=list(range(1, 21)).index(st.session_state["build_level"]),
        )

        st.session_state["homebrew"] = st.toggle(
            "Homebrew (RP-only, clearly labeled)", value=st.session_state["homebrew"]
        )

        st.caption("Sources: SRD-only (public repo).")

        if st.button("Start Build", on_click=complete_setup):
            st.write("Setup complete. Starting build...")

    # ---------- Chat phase ----------
    if st.session_state.setup_complete and not st.session_state.chat_complete:
        st.info("Describe your character concept to begin.", icon="👋")

        if not st.session_state.messages:
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": build_system_prompt(
                        build_level=st.session_state["build_level"],
                        homebrew=st.session_state["homebrew"],
                    ),
                }
            ]

        for message in st.session_state.messages:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        with st.sidebar:
            st.markdown("### Constraints")
            st.session_state["build_level"] = st.selectbox(
                "Level",
                options=list(range(1, 21)),
                index=list(range(1, 21)).index(st.session_state["build_level"]),
                key="sidebar_level",
            )
            st.session_state["homebrew"] = st.toggle(
                "Homebrew",
                value=st.session_state["homebrew"],
                key="sidebar_homebrew",
                help="If ON, the assistant may include clearly-labeled HOMEBREW options.",
            )

            st.markdown("### Controls")
            st.button(
                "🛑 Stop",
                on_click=request_stop,
                key="stop_btn",
                help="Stop the current response",
                disabled=st.session_state.get("stop_requested", False),
            )

            st.button(
                "🆕 New Build",
                on_click=reset_build,
                key="new_build_btn",
                help="Clear current chat and start a new build session.",
                disabled=st.session_state.get("is_generating", False),
            )

            st.markdown("### Persistence")
            st.text_input("Session title", key="session_title")

            notice = None
            notice_kind = "success"

            if st.button("💾 Save", key="save_session_btn"):
                payload = {
                    "session_id": st.session_state.get("session_id"),
                    "title": st.session_state.get("session_title", ""),
                    "params": {
                        "build_level": int(st.session_state.get("build_level", 5)),
                        "homebrew": bool(st.session_state.get("homebrew", False)),
                        "openai_model": st.session_state.get("openai_model", ""),
                    },
                    "messages": st.session_state.get("messages", []),
                    "versions": st.session_state.get("build_versions", []),
                }
                try:
                    session_store.save_session(payload)
                    notice = "Saved ✅"
                except Exception as e:
                    notice_kind = "error"
                    notice = f"Save failed: {e}"

            if st.button("➕ Save version", key="save_version_btn"):
                version = session_store.create_build_version(
                    messages=st.session_state.get("messages", []),
                    build_level=int(st.session_state.get("build_level", 5)),
                    homebrew=bool(st.session_state.get("homebrew", False)),
                    label="",
                )
                if not version:
                    notice_kind = "warning"
                    notice = "No assistant build draft yet to version."
                else:
                    st.session_state.build_versions.append(version)
                    payload = {
                        "session_id": st.session_state.get("session_id"),
                        "title": st.session_state.get("session_title", ""),
                        "params": {
                            "build_level": int(st.session_state.get("build_level", 5)),
                            "homebrew": bool(st.session_state.get("homebrew", False)),
                            "openai_model": st.session_state.get("openai_model", ""),
                        },
                        "messages": st.session_state.get("messages", []),
                        "versions": st.session_state.get("build_versions", []),
                    }
                    try:
                        session_store.save_session(payload)
                        notice = "Version saved ✅"
                    except Exception as e:
                        notice_kind = "error"
                        notice = f"Save failed: {e}"

            if notice:
                if notice_kind == "success":
                    st.success(notice)
                elif notice_kind == "warning":
                    st.warning(notice)
                else:
                    st.error(notice)

            summaries = session_store.list_sessions()
            if not summaries:
                st.caption("No saved sessions yet.")
            else:
                options = {}
                for s in summaries:
                    label = f"{s.title or s.session_id} • {s.updated_at[:19]}"
                    options[label] = s.session_id

                selected_label = st.selectbox(
                    "Load saved session",
                    options=list(options.keys()),
                    key="load_session_select",
                )
                if st.button("Load", key="load_session_btn"):
                    try:
                        payload = session_store.load_session(options[selected_label])
                        st.session_state["_pending_load_payload"] = payload
                        st.rerun()
                    except Exception as e:
                        st.error(f"Load failed: {e}")

        # Always refresh the system prompt from current constraints
        if st.session_state.messages and st.session_state.messages[0].get("role") == "system":
            st.session_state.messages[0]["content"] = build_system_prompt(
                build_level=st.session_state["build_level"],
                homebrew=st.session_state["homebrew"],
            )

        try:
            esc_signal = streamlit_js_eval(
                js_expressions=[
                    """ ... install listener ... """,
                    "(function(){const v = window.name || ''; if (v === 'STOP_REQUESTED') { window.name = ''; } return v; })()",
                ],
                key="esc_listener",
            )
            if isinstance(esc_signal, list) and len(esc_signal) == 2 and esc_signal[1] == "STOP_REQUESTED":
                st.session_state.stop_requested = True
                if st.session_state.user_message_count == 0:
                    st.session_state.stopped_early = True
                st.session_state.chat_complete = True
        except Exception:
            pass

        if not st.session_state.stop_requested:
            if not st.session_state.get("is_generating", False):
                if prompt := st.chat_input("Your concept / refinement", max_chars=1000):
                    st.session_state.is_generating = True
                    try:
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        with st.chat_message("user"):
                            st.markdown(prompt)

                        with st.chat_message("assistant"):
                            stream = client.chat.completions.create(
                                model=st.session_state["openai_model"],
                                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                                stream=True,
                            )

                            placeholder = st.empty()
                            full_response = ""
                            for chunk in stream:
                                if st.session_state.stop_requested:
                                    break
                                delta = getattr(chunk.choices[0].delta, "content", None)
                                if delta:
                                    full_response += delta
                                    placeholder.markdown(full_response)

                        if should_append_assistant_message(full_response):
                            st.session_state.messages.append({"role": "assistant", "content": full_response})
                        else:
                            st.warning("No assistant text was received (empty stream). Please try again.")
                    finally:
                        st.session_state.is_generating = False

        if st.session_state.stop_requested:
            st.session_state.chat_complete = True

    if st.session_state.chat_complete:
        st.info("Generation stopped by user.", icon="🛑")
        if st.button("Restart Build", key="restart_after_stop"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

    st.markdown("---")
    st.markdown(
        f"<small>v0.1 • Concept-to-Build • Model: {st.session_state.get('openai_model', 'n/a')}</small>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
