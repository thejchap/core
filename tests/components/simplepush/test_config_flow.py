"""Test Simplepush config flow."""

from collections.abc import Generator
from unittest.mock import patch

from simplepush import UnknownError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.simplepush.const import CONF_DEVICE_KEY, CONF_SALT, DOMAIN
from homeassistant.const import CONF_NAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass, mock_network

MOCK_CONFIG = {
    CONF_DEVICE_KEY: "abc",
    CONF_NAME: "simplepush",
}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def simplepush_setup_fixture() -> Generator[None]:
    """Patch simplepush setup entry."""
    with patch(
        "homeassistant.components.simplepush.async_setup_entry", return_value=True
    ):
        yield


@fixture
def mock_api_request() -> Generator[None]:
    """Patch simplepush api request."""
    with patch("homeassistant.components.simplepush.config_flow.send"):
        yield


@test
async def flow_successful(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _simplepush_setup_fixture: None = Depends(simplepush_setup_fixture),
    _mock_api_request: None = Depends(mock_api_request),
) -> None:
    """Test user initialized flow with minimum config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("simplepush")
    expect(result["data"]).to_equal(MOCK_CONFIG)


@test
async def flow_with_password(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _simplepush_setup_fixture: None = Depends(simplepush_setup_fixture),
    _mock_api_request: None = Depends(mock_api_request),
) -> None:
    """Test user initialized flow with password and salt."""
    mock_config_pass = {**MOCK_CONFIG, CONF_PASSWORD: "password", CONF_SALT: "salt"}
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=mock_config_pass,
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("simplepush")
    expect(result["data"]).to_equal(mock_config_pass)


@test
async def flow_user_device_key_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _simplepush_setup_fixture: None = Depends(simplepush_setup_fixture),
    _mock_api_request: None = Depends(mock_api_request),
) -> None:
    """Test user initialized flow with duplicate device key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        unique_id="abc",
    )

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_user_name_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _simplepush_setup_fixture: None = Depends(simplepush_setup_fixture),
    _mock_api_request: None = Depends(mock_api_request),
) -> None:
    """Test user initialized flow with duplicate name."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        unique_id="abc",
    )

    entry.add_to_hass(hass)

    new_entry = MOCK_CONFIG.copy()
    new_entry[CONF_DEVICE_KEY] = "abc1"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def error_on_connection_failure(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _simplepush_setup_fixture: None = Depends(simplepush_setup_fixture),
) -> None:
    """Test when connection to api fails."""
    with patch(
        "homeassistant.components.simplepush.config_flow.send",
        side_effect=UnknownError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_CONFIG,
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})
