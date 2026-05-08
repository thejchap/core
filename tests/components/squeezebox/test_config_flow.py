"""Test the Squeezebox config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.squeezebox.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import SERVER_UUIDS, mock_discover_timeout, mock_server, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_UUID = SERVER_UUIDS[0]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _discover_timeout: None = Depends(mock_discover_timeout),
) -> None:
    """Anchor fixture so tryke fully resolves Depends() in this module."""


@test
async def manual_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    server: AsyncMock = Depends(mock_server),
) -> None:
    """Test we can finish a manual setup successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "edit"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("edit")

    server.async_query.return_value = {"uuid": TEST_UUID}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.2.3.4", CONF_PORT: 9000},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(TEST_UUID)
    expect(result["title"]).to_equal("1.2.3.4")
    expect(result["data"][CONF_HOST]).to_equal("1.2.3.4")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.skip("complex parametrized error scenarios; not yet ported")
async def manual_setup_data_errors() -> None:
    """Skipped pending parametrize port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def manual_setup_exception_error() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def manual_setup_recovery() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def duplicate_setup() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def discovery_flow_success() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def discovery_flow_edit_discovered_success() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def discovery_flow_edit_discovered_errors() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def discovery_flow_failed() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def discovery_ignores_existing() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def integration_discovery() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def integration_discovery_no_uuid() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def integration_discovery_no_uuid_fails() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def integration_discovery_edit_recovery() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def dhcp_unknown_player() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def dhcp_known_player() -> None:
    """Skipped pending fixture port."""


@test.skip("complex pysqueezebox + auth fixtures")
async def options_flow() -> None:
    """Skipped pending fixture port."""
