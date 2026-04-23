"""Common fixtures for Anova tests."""

from collections.abc import AsyncGenerator
from unittest.mock import patch

from anova_wifi import AnovaApi
from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass

from .conftest import anova_api_mock


@fixture
async def anova_api(
    hass: HomeAssistant = Depends(hass),
) -> AsyncGenerator[AnovaApi]:
    """Mock the Anova API for config flow tests."""
    api_mock = anova_api_mock()

    with (
        patch("homeassistant.components.anova.AnovaApi", return_value=api_mock),
        patch(
            "homeassistant.components.anova.config_flow.AnovaApi", return_value=api_mock
        ),
    ):
        api = AnovaApi(
            None,
            "sample@gmail.com",
            "sample",
        )
        yield api
