import pytest
import app

pytestmark = pytest.mark.unit


def test_hb_requested_while_off_includes_toggle_hint() -> None:
    prompt = app.build_system_prompt(build_level=5, homebrew=False)
    assert "Want homebrew elements? Toggle Homebrew ON in the UI and ask again." in prompt
