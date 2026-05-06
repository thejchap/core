"""Common fixtures for the acaia tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.acaia.const import CONF_IS_NEW_STYLE_SCALE, DOMAIN
from homeassistant.const import CONF_ADDRESS

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.acaia.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_verify() -> Generator[AsyncMock]:
    """Override is_new_scale check."""
    with patch(
        "homeassistant.components.acaia.config_flow.is_new_scale", return_value=True
    ) as mock_verify:
        yield mock_verify


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="LUNAR-DDEEFF",
        domain=DOMAIN,
        version=1,
        data={
            CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
            CONF_IS_NEW_STYLE_SCALE: True,
        },
        unique_id="aa:bb:cc:dd:ee:ff",
    )
