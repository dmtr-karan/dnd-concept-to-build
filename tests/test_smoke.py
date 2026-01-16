import app.app as app


def test_app_module_exposes_secret_helper() -> None:
    assert callable(app.get_required_secret)
