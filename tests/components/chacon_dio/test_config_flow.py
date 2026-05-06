"""Test the chacon_dio config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from dio_chacon_wifi_api.exceptions import DIOChaconAPIError, DIOChaconInvalidAuthError
from tryke import Depends, expect, fixture, test

from homeassistant.components.chacon_dio.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.chacon_dio._fixtures import (
    mock_config_entry,
    mock_dio_chacon_client,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_dio_chacon_client: AsyncMock = Depends(mock_dio_chacon_client),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_USERNAME: "dummylogin",
            CONF_PASSWORD: "dummypass",
        },
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Chacon DiO dummylogin")
    expect(result["result"].unique_id).to_equal("dummy-user-id")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "dummylogin",
            CONF_PASSWORD: "dummypass",
        }
    )


@test.cases(
    test.case("unknown", Exception("Bad request Boy :) --"), {"base": "unknown"}),
    test.case("invalid_auth", DIOChaconInvalidAuthError, {"base": "invalid_auth"}),
    test.case("cannot_connect", DIOChaconAPIError, {"base": "cannot_connect"}),
)
async def errors(
    exception: Exception,
    expected: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_dio_chacon_client: AsyncMock = Depends(mock_dio_chacon_client),
) -> None:
    """Test we handle any error."""
    mock_dio_chacon_client.get_user_id.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_USERNAME: "nada",
            CONF_PASSWORD: "nadap",
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal(expected)

    mock_dio_chacon_client.get_user_id.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "dummylogin",
            CONF_PASSWORD: "dummypass",
        },
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("Chacon DiO dummylogin")
    expect(result["result"].unique_id).to_equal("dummy-user-id")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "dummylogin",
            CONF_PASSWORD: "dummypass",
        }
    )


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_dio_chacon_client: AsyncMock = Depends(mock_dio_chacon_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test abort when setting up duplicate entry."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(bool(result["errors"])).to_be(False)

    mock_dio_chacon_client.get_user_id.return_value = "test_entry_unique_id"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "dummylogin",
            CONF_PASSWORD: "dummypass",
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
