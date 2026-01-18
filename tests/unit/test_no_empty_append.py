import pytest
import app

pytestmark = pytest.mark.unit


def test_no_empty_assistant_message_append_rule() -> None:
    assert app.should_append_assistant_message("hello") is True
    assert app.should_append_assistant_message("   \n\t") is False
