"""Tryke fixtures for the WiLight tests."""

from unittest.mock import patch

from tryke import fixture


@fixture
def dummy_get_components_from_model_clear():
    """Mock a clear components list."""
    components = []
    with patch(
        "pywilight.get_components_from_model",
        return_value=components,
    ):
        yield components


@fixture
def dummy_get_components_from_model_wrong():
    """Mock a wrong components list."""
    components = ["wrong"]
    with patch(
        "pywilight.get_components_from_model",
        return_value=components,
    ):
        yield components
