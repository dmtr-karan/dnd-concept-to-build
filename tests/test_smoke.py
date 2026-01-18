import pytest
import app as app

pytestmark = pytest.mark.unit


def test_app_module_exposes_secret_helper() -> None:
    assert callable(app.get_required_secret)
