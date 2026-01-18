import pytest
import app

pytestmark = pytest.mark.unit


def test_guardrails_present_in_system_prompt() -> None:
    prompt = app.build_system_prompt(build_level=5, homebrew=False)
    assert "Hard rule:" in prompt
    assert "SRD limitation" in prompt
    assert "Do not mention non-SRD options by name" in prompt
