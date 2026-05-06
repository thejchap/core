"""Test Dynalite config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import dynalite
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.dynalite._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("both_success", True, True, "create_entry", ConfigEntryState.LOADED, ""),
    test.case("both_fail", False, False, "abort", None, "cannot_connect"),
    test.case(
        "second_fail", True, False, "create_entry", ConfigEntryState.SETUP_RETRY, ""
    ),
)
async def flow(
    first_con: bool,
    second_con: bool,
    exp_type: str,
    exp_result: ConfigEntryState | None,
    exp_reason: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Run a flow with or without errors and return result."""
    host = "1.2.3.4"
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        side_effect=[first_con, second_con],
    ):
        result = await hass.config_entries.flow.async_init(
            dynalite.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: host},
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_equal(exp_type)
    if exp_result:
        expect(result["result"].state).to_equal(exp_result)
    if exp_reason:
        expect(result["reason"]).to_equal(exp_reason)


@test
async def existing(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test when the entry exists with the same config."""
    host = "1.2.3.4"
    MockConfigEntry(domain=dynalite.DOMAIN, data={CONF_HOST: host}).add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            dynalite.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: host},
        )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def existing_abort_update(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test when the entry exists with a different config."""
    host = "1.2.3.4"
    port1 = 7777
    port2 = 8888
    entry = MockConfigEntry(
        domain=dynalite.DOMAIN,
        data={CONF_HOST: host, CONF_PORT: port1},
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        mock_dyn_dev().configure.assert_called_once()
        expect(mock_dyn_dev().configure.mock_calls[0][1][0]["port"]).to_equal(port1)
        result = await hass.config_entries.flow.async_init(
            dynalite.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: host, CONF_PORT: port2},
        )
        await hass.async_block_till_done()
        expect(mock_dyn_dev().configure.call_count).to_equal(1)
        expect(mock_dyn_dev().configure.mock_calls[0][1][0]["port"]).to_equal(port1)
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def two_entries(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test when two different entries exist with different hosts."""
    host1 = "1.2.3.4"
    host2 = "5.6.7.8"
    MockConfigEntry(domain=dynalite.DOMAIN, data={CONF_HOST: host1}).add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            dynalite.DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: host2},
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["result"].state is ConfigEntryState.LOADED).to_be(True)


@test
async def setup_user(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test configuration via the user flow."""
    host = "3.4.5.6"
    port = 1234
    result = await hass.config_entries.flow.async_init(
        dynalite.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"] is None).to_be(True)

    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": host, "port": port},
        )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["result"].state is ConfigEntryState.LOADED).to_be(True)
    expect(result["title"]).to_equal(host)
    expect(result["data"]).to_equal(
        {
            "host": host,
            "port": port,
        }
    )


@test
async def setup_user_existing_host(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that when we setup a host that is defined, we get an error."""
    host = "3.4.5.6"
    MockConfigEntry(domain=dynalite.DOMAIN, data={CONF_HOST: host}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        dynalite.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": host, "port": 1234},
        )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
