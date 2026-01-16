import os

import streamlit as st


def get_required_secret(key: str) -> str:
    """Return a required secret value from env or Streamlit secrets."""
    value = os.getenv(key)
    if value:
        return value

    if key in st.secrets:
        return st.secrets[key]

    st.error(f"Missing required secret: {key}")
    st.stop()


def main() -> None:
    st.title("D&D Concept to Build")
    st.write("Scaffolded Streamlit app shell.")


if __name__ == "__main__":
    main()
