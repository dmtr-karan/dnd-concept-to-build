import pytest
import app

pytestmark = pytest.mark.contract


def test_srd_only_prompt_does_not_name_non_srd_books_or_options() -> None:
    prompt = app.build_system_prompt(build_level=5, homebrew=False)

    banned = [
        "PHB",
        "Player's Handbook",
        "Xanathar",
        "Tasha",
        "Volo",
        "Mordenkainen",
        "Sword Coast",
    ]
    for token in banned:
        assert token not in prompt
