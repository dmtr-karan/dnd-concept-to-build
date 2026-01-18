import pytest

pytestmark = pytest.mark.unit


def test_import():
    __import__("app")  # catches syntax/missing-deps early
