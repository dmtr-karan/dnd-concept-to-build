"""Streamlit interview simulator.

Features:
- Guided setup (candidate + target role)
- Chat interview (OpenAI Chat Completions, streaming)
- Stop control (button + ESC) with early-stop rule
- Post-interview feedback generator
"""


import os
import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval

# ---------- Page config ----------
st.set_page_config(page_title="StreamlitChatMessageHistory", page_icon="💬")
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
st.title("Chatbot")
st.caption("A minimal Streamlit interview simulator using OpenAI with Stop + feedback flow.")


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
    st.subheader("Personal Information")

    st.session_state["name"] = st.text_input(
        label="Name",
        value=st.session_state["name"],
        placeholder="Enter your name",
        max_chars=40,
    )
    st.session_state["experience"] = st.text_area(
        label="Experience",
        value=st.session_state["experience"],
        placeholder="Describe your experience",
        max_chars=200,
    )
    st.session_state["skills"] = st.text_area(
        label="Skills",
        value=st.session_state["skills"],
        placeholder="List your skills",
        max_chars=200,
    )

    st.subheader("Company and Position")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose level",
            options=["Junior", "Mid-level", "Senior"],
            index=["Junior", "Mid-level", "Senior"].index(st.session_state["level"]),
            key="level_radio",
        )
    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a position",
            ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst"),
            index=("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst").index(
                st.session_state["position"]
            ),
            key="position_select",
        )

    st.session_state["company"] = st.selectbox(
        "Select a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"),
        index=("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify").index(
            st.session_state["company"]
        ),
        key="company_select",
    )

    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")

# ---------- Interview phase ----------
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:
    st.info("Start by introducing yourself", icon="👋")

    # Initialize system message only once
    if not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system",
                "content": (
                    f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                    f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                    f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
                    f"at the company {st.session_state['company']}"
                ),
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
        st.markdown("### Controls")
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

    # Input loop limited to 5 user messages
    if st.session_state.user_message_count < 5 and not st.session_state.stop_requested:
        if prompt := st.chat_input("Your response", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Model responds for first 4 user messages (original logic)
            if st.session_state.user_message_count < 4:
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
                        st.info("Interview stopped by user.", icon="🛑")

                    # Persist whatever was generated (even if empty)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    st.error(f"Assistant response failed: {e}")

            # Increment the user message count
            st.session_state.user_message_count += 1

    # End interview after 5 user messages or when stopped
    if st.session_state.user_message_count >= 5 or st.session_state.stop_requested:
        st.session_state.chat_complete = True

# ---------- Get Feedback ----------
if (
    st.session_state.chat_complete
    and not st.session_state.feedback_shown
    and not st.session_state.stopped_early
    and st.session_state.user_message_count > 0
):
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

if (
    st.session_state.chat_complete
    and not st.session_state.feedback_shown
    and st.session_state.stopped_early
):
    st.info("Interview was stopped before it began.", icon="🛑")
    if st.button("Restart Interview", type="primary", key="restart_early"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

# ---------- Feedback screen ----------
if st.session_state.feedback_shown:
    if st.session_state.stopped_early or st.session_state.user_message_count == 0:
        st.info("Interview was stopped before it began. No feedback available.")
        # Optional: also offer Restart here as a fallback (won't normally hit due to gating above)
        if st.button("Restart Interview", type="primary", key="restart_guard"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")
        st.stop()
    st.subheader("Feedback")

    conversation_history = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages]
    )

    try:
        feedback_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful tool that provides feedback on an interviewee performance. "
                        "Before the Feedback give a score of 1 to 10.\n"
                        "Follow this format:\n"
                        "Overal Score: //Your score\n"
                        "Feedback: //Here you put your feedback\n"
                        "Give only the feedback do not ask any additional questins."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "This is the interview you need to evaluate. "
                        "Keep in mind that you are only a tool. "
                        "And you shouldn't engage in any converstation: "
                        f"{conversation_history}"
                    ),
                },
            ],
        )
        st.write(feedback_completion.choices[0].message.content)
    except Exception as e:
        st.error(f"Feedback generation failed: {e}")

    # Allow user to download full conversation as .txt
    transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    st.download_button(
        label="Download Transcript",
        data=transcript,
        file_name="interview_transcript.txt",
        mime="text/plain"
    )

    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

st.markdown("---")
st.markdown(f"<small>v0.1 • Model: {st.session_state.get('openai_model','n/a')}</small>", unsafe_allow_html=True)
