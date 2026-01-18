import pytest
import app

pytestmark = pytest.mark.contract


def test_prompt_requires_six_sections() -> None:
    prompt = app.build_system_prompt(build_level=5, homebrew=False)

    required_phrases = [
        "Concept summary",
        "Class:",
        "Subclass:",
        "Key feature milestones",
        "Spell suggestions",
        "Short RP hooks",
    ]
    for p in required_phrases:
        assert p in prompt
