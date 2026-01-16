"""D&D Concept-to-Build (RP-first).

Current stage: base app imported from interview simulator.
We are only re-skinning UI text in this step (no logic changes yet).
"""

import os
import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval

# ---------- Page config ----------
st.set_page_config(page_title="D&D Concept-to-Build", page_icon="🧙")
# ---------- UI polish ----------
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        width: 200px !important;   /* default is ~250px */
    }
    section[data-testid="stSidebar"] > div {
        width: 200px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("🧙 D&D Concept-to-Build")
st.caption("RP-first concept → build draft (base app imported; re-skin step).")


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


client = get_openai_client()

# ---------- Session state ----------
defaults = {
    "setup_complete": False,
    "user_message_count": 0,
    "feedback_shown": False,
    "chat_complete": False,
    "messages": [],
    "name": "",
    "experience": "",
    "skills": "",
    "level": "Junior",
    "position": "Data Scientist",
    "company": "Amazon",
    "openai_model": "gpt-4.1-mini",
    # Stop-control state
    "stop_requested": False,
    # mark if Stop was pressed before any user message
    "stopped_early": False,
    # Idea #5 controls (public repo = SRD-only; no other sources shipped)
    "build_level": 5,
    "homebrew": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def complete_setup() -> None:
    """Mark setup as complete."""
    st.session_state.setup_complete = True


def show_feedback() -> None:
    """Show feedback section."""
    st.session_state.feedback_shown = True


def request_stop() -> None:
    """Stop interview; flag early stop if no user messages and end immediately."""
    st.session_state.stop_requested = True
    if st.session_state.user_message_count == 0:
        st.session_state.stopped_early = True
    st.session_state.chat_complete = True


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

    # Public repo policy: SRD-only. Additional books are intentionally not supported here.
    st.caption("Sources: SRD-only (public repo).")

    if st.button("Start Build", on_click=complete_setup):
        st.write("Setup complete. Starting build...")

# ---------- Interview phase ----------
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:
    st.info("Describe your character concept to begin.", icon="👋")

    # Initialize system message only once
    if not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system",
                "content": (
                    "You are a D&D 5e assistant that turns a roleplay-first character concept into a playable build draft. "
                    "This PUBLIC app is SRD-only by design: do not rely on PHB/Xanathar/Tasha content.\n\n"
                    "Hard rule:\n"
                    "- If you are not sure an option is in SRD, do not name it; instead say 'SRD limitation' and offer a generic SRD-safe alternative (e.g., base class choice + ASIs + generic spell themes).\n"
                    "- Only recommend options that exist in the SRD dataset shipped with this app.\n"
                    "- If the concept suggests a non-SRD subclass/spell/feat, say it's unavailable in SRD and offer a generic SRD-safe alternative without naming book-specific options.\n"
                    "- Do not mention non-SRD options by name (even to disclaim them). Just say 'SRD limitation' and proceed with SRD-safe choices.\n"
                    "- Never invent subclass names, land types, or 'winter variants'. If you cannot name a subclass with certainty as SRD, do not name any subclass.\n"
                    "- If subclass is uncertain: write 'Subclass: SRD limitation (not specified)' and proceed with a class-first build using SRD-safe spell/ASI suggestions.\n"
                    "- Do not name PHB/Xanathar/Tasha subclasses (e.g., Land: Arctic) or feats.\n\n"
                    f"Constraints:\n"
                    f"- Target level: {st.session_state['build_level']}\n"
                    f"- Homebrew: {'ON' if st.session_state['homebrew'] else 'OFF'} "
                    "(If ON: you MAY invent RP-flavored options, but label them clearly as HOMEBREW.)\n\n"
                    "Output style:\n"
                    "- Ask at most 1 clarifying question if needed; otherwise proceed.\n"
                    "- Provide: (1) Concept summary, (2) Class: <name>. Subclass: <name or 'SRD limitation (not specified)'>. RP rationale, "
                    "(3) Key feature milestones up to the target level, (4) Spell suggestions if applicable (SRD-only), "
                    "(5) In SRD-only mode: prefer ASIs; only mention feats if you are certain they are SRD-available, otherwise explicitly skip feats, "
                    "(6) Short RP hooks (2–4 bullets).\n"
                    "- Keep it concise and practical. No copyrighted text.\n"
                )

                ,
            }
        ]

    # Render prior chat (excluding system)
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # ---------- Stop controls (button + ESC) ----------
    # ---------- Controls (sidebar) ----------
    with st.sidebar:
        st.markdown("### Controls (temporary)")
        st.button(
            "🛑 Stop",
            on_click=request_stop,
            key="stop_btn",
            help="Stop the current response",
            disabled=st.session_state.get("stop_requested", False)
        )

    # ESC key listener via streamlit_js_eval (best-effort; safe to ignore if unsupported)
    try:
        esc_signal = streamlit_js_eval(
            js_expressions=[
                # Install a one-time keydown listener
                """
                if (!window.__stopEscListenerInstalled) {
                    window.addEventListener('keydown', (e) => {
                        if (e.key === 'Escape') {
                            window.name = 'STOP_REQUESTED';
                        }
                    });
                    window.__stopEscListenerInstalled = true;
                }
                'OK'
                """,
                # Read the flag
                "window.name || ''"
            ],
            key="esc_listener"
        )
        if isinstance(esc_signal, list) and len(esc_signal) == 2 and esc_signal[1] == "STOP_REQUESTED":
            st.session_state.stop_requested = True
            if st.session_state.user_message_count == 0:
                st.session_state.stopped_early = True
            st.session_state.chat_complete = True
    except Exception:
        pass  # Non-fatal if JS eval is unavailable

    # Chat loop (no message cap)
    if not st.session_state.stop_requested:
        if prompt := st.chat_input("Your concept / refinement", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Model responds on every user message (until stopped)
            if True:
                try:
                    with st.chat_message("assistant"):
                        stream = client.chat.completions.create(
                            model=st.session_state["openai_model"],
                            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                            stream=True,
                        )

                        # Manual stream rendering with early-stop support
                        placeholder = st.empty()
                        full_response = ""
                        try:
                            for chunk in stream:
                                # Respect Stop from button or ESC
                                if st.session_state.stop_requested:
                                    break
                                # Extract streamed delta content (OpenAI Chat Completions stream)
                                try:
                                    delta = chunk.choices[0].delta.content
                                except Exception:
                                    delta = None
                                if delta:
                                    full_response += delta
                                    placeholder.markdown(full_response)
                        except Exception as e:
                            st.error(f"Assistant streaming failed: {e}")

                    # If user requested stop during streaming, mark interview complete
                    if st.session_state.stop_requested:
                        st.session_state.chat_complete = True
                        st.info("Generation stopped by user.", icon="🛑")

                    # Persist whatever was generated (even if empty)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    st.error(f"Assistant response failed: {e}")

            # Increment the user message count
            st.session_state.user_message_count += 1

    # End chat only when stopped
    if st.session_state.stop_requested:
        st.session_state.chat_complete = True

st.markdown("---")
st.markdown(f"<small>v0.1 • Concept-to-Build • Model: {st.session_state.get('openai_model', 'n/a')}</small>",
            unsafe_allow_html=True)
