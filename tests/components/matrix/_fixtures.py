"""Tryke fixtures for matrix tests."""

from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.matrix import MatrixBot
from homeassistant.components.matrix.const import DOMAIN
from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture

from .conftest import MOCK_CONFIG_DATA, _MockAsyncClient


@fixture
def mock_client():
    """Return mocked AsyncClient."""
    with patch("homeassistant.components.matrix.AsyncClient", _MockAsyncClient) as mock:
        yield mock


@fixture
def mock_save_json():
    """Prevent saving test access_tokens."""
    with patch("homeassistant.components.matrix.save_json") as mock:
        yield mock


@fixture
def mock_allowed_path():
    """Allow using NamedTemporaryFile for mock image."""
    with patch(
        "homeassistant.core_config.Config.is_allowed_path", return_value=True
    ) as mock:
        yield mock


@fixture
async def matrix_bot(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: object = Depends(mock_client),
    mock_save_json: object = Depends(mock_save_json),
    mock_allowed_path: object = Depends(mock_allowed_path),
) -> MatrixBot:
    """Set up Matrix and Notify component."""
    assert await async_setup_component(hass, DOMAIN, MOCK_CONFIG_DATA)
    assert await async_setup_component(hass, NOTIFY_DOMAIN, MOCK_CONFIG_DATA)
    await hass.async_block_till_done()

    assert isinstance(matrix_bot := hass.data[DOMAIN], MatrixBot)

    await hass.async_start()

    return matrix_bot
