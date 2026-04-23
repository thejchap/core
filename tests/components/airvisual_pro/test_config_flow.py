"""Test the AirVisual Pro config flow."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from pyairvisual.node import (
    InvalidAuthenticationError,
    NodeConnectionError,
    NodeProError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.airvisual_pro.const import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.airvisual_pro._fixtures import (
    config,
    config_entry,
    mock_setup_entry,
    pro,
    setup_airvisual_pro,
)
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("unknown", Exception, {"base": "unknown"}),
    test.case("invalid_auth", InvalidAuthenticationError, {"base": "invalid_auth"}),
    test.case("cannot_connect", NodeConnectionError, {"base": "cannot_connect"}),
    test.case("node_pro_error", NodeProError, {"base": "unknown"}),
)
async def create_entry(
    connect_exc: type[Exception],
    connect_errors: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    config: dict[str, Any] = Depends(config),
    pro: Mock = Depends(pro),
    _setup_airvisual_pro: None = Depends(setup_airvisual_pro),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with patch.object(pro, "async_connect", AsyncMock(side_effect=connect_exc)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal(connect_errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("192.168.1.101")
    expect(result["data"]).to_equal(
        {CONF_IP_ADDRESS: "192.168.1.101", CONF_PASSWORD: "password123"}
    )


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass),
    config: dict[str, Any] = Depends(config),
    _config_entry: MockConfigEntry = Depends(config_entry),
    _setup_airvisual_pro: None = Depends(setup_airvisual_pro),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that errors are shown when duplicates are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def step_import(
    hass: HomeAssistant = Depends(hass),
    config: dict[str, Any] = Depends(config),
    _setup_airvisual_pro: None = Depends(setup_airvisual_pro),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=config
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("192.168.1.101")
    expect(result["data"]).to_equal(
        {CONF_IP_ADDRESS: "192.168.1.101", CONF_PASSWORD: "password123"}
    )


@test.cases(
    test.case("unknown", Exception, {"base": "unknown"}),
    test.case("invalid_auth", InvalidAuthenticationError, {"base": "invalid_auth"}),
    test.case("cannot_connect", NodeConnectionError, {"base": "cannot_connect"}),
    test.case("node_pro_error", NodeProError, {"base": "unknown"}),
)
async def reauth(
    connect_exc: type[Exception],
    connect_errors: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    config_entry: MockConfigEntry = Depends(config_entry),
    pro: Mock = Depends(pro),
    _setup_airvisual_pro: None = Depends(setup_airvisual_pro),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test re-auth (including errors)."""
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch.object(pro, "async_connect", AsyncMock(side_effect=connect_exc)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PASSWORD: "new_password"}
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal(connect_errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "new_password"}
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)
