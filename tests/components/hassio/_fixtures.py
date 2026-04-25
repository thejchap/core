"""Tryke fixtures for Hass.io tests."""

from collections.abc import Generator
import re
from unittest.mock import patch

from tryke import fixture


@fixture
def disable_security_filter() -> Generator[None]:
    """Disable the security filter to ensure the integration is secure."""
    with patch(
        "homeassistant.components.http.security_filter.FILTERS",
        re.compile("not-matching-anything"),
    ):
        yield
