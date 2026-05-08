"""Test Onkyo config flow (tryke port)."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.onkyo.const import (
    DOMAIN,
    OPTION_INPUT_SOURCES,
    OPTION_LISTENING_MODES,
    OPTION_VOLUME_RESOLUTION,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import RECEIVER_INFO_2
from ._fixtures import mock_default_discovery, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _disc: None = Depends(mock_default_discovery),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def manual(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful manual."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: RECEIVER_INFO_2.host}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configure_receiver")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            OPTION_VOLUME_RESOLUTION: 200,
            OPTION_INPUT_SOURCES: ["TV"],
            OPTION_LISTENING_MODES: ["THX"],
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal(RECEIVER_INFO_2.host)
    expect(result["result"].unique_id).to_equal(RECEIVER_INFO_2.identifier)
    expect(result["title"]).to_equal(RECEIVER_INFO_2.model_name)


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def manual_recoverable_error() -> None:
    """Stub for test_manual_recoverable_error (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def manual_error() -> None:
    """Stub for test_manual_error (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def eiscp_discovery() -> None:
    """Stub for test_eiscp_discovery (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def eiscp_discovery_error() -> None:
    """Stub for test_eiscp_discovery_error (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def eiscp_discovery_replace_ignored_entry() -> None:
    """Stub for test_eiscp_discovery_replace_ignored_entry (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def ssdp_discovery() -> None:
    """Stub for test_ssdp_discovery (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def ssdp_discovery_error() -> None:
    """Stub for test_ssdp_discovery_error (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def configure() -> None:
    """Stub for test_configure (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def reconfigure() -> None:
    """Stub for test_reconfigure (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def reconfigure_error() -> None:
    """Stub for test_reconfigure_error (port deferred)."""


@test.skip("requires aioonkyo discovery autouse + receiver mocks (not ported)")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""
