"""Configure and test MatrixBot."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.matrix import MatrixBot
from homeassistant.components.matrix.const import (
    DOMAIN,
    SERVICE_REACT,
    SERVICE_SEND_MESSAGE,
)
from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from homeassistant.core import HomeAssistant

from ._fixtures import matrix_bot as matrix_bot_fixture
from .conftest import TEST_NOTIFIER_NAME

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def services(
    hass: HomeAssistant = Depends(_trigger_executor),
    matrix_bot: MatrixBot = Depends(matrix_bot_fixture),
) -> None:
    """Test hass/MatrixBot state."""

    services = hass.services.async_services()

    # Verify that the matrix service is registered
    matrix_service = services.get(DOMAIN)
    expect(matrix_service is not None).to_be(True)
    expect(SERVICE_SEND_MESSAGE in matrix_service).to_be(True)
    expect(SERVICE_REACT in matrix_service).to_be(True)

    # Verify that the matrix notifier is registered
    notify_service = services.get(NOTIFY_DOMAIN)
    expect(notify_service is not None).to_be(True)
    expect(TEST_NOTIFIER_NAME in notify_service).to_be(True)
