"""Test the Pentair ScreenLogic config flow."""

from __future__ import annotations

from unittest.mock import patch

from screenlogicpy import ScreenLogicError
from screenlogicpy.const.common import (
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    SL_GATEWAY_SUBTYPE,
    SL_GATEWAY_TYPE,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.screenlogic.config_flow import (
    GATEWAY_MANUAL_ENTRY,
    GATEWAY_SELECT_KEY,
)
from homeassistant.components.screenlogic.const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import mock_disconnect

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _disconnect: None = Depends(mock_disconnect),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the flow works with basic discovery."""

    with patch(
        "homeassistant.components.screenlogic.config_flow.discovery.async_discover",
        return_value=[
            {
                SL_GATEWAY_IP: "1.1.1.1",
                SL_GATEWAY_PORT: 80,
                SL_GATEWAY_TYPE: 12,
                SL_GATEWAY_SUBTYPE: 2,
                SL_GATEWAY_NAME: "Pentair: 01-01-01",
            },
        ],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("gateway_select")

    with patch(
        "homeassistant.components.screenlogic.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={GATEWAY_SELECT_KEY: "00:c0:33:01:01:01"}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Pentair: 01-01-01")
    expect(result2["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_PORT: 80,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def flow_discover_none(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test when nothing is discovered."""

    with patch(
        "homeassistant.components.screenlogic.config_flow.discovery.async_discover",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("gateway_entry")


@test
async def flow_replace_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can replace ignored entries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="00:c0:33:01:01:01",
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.screenlogic.config_flow.discovery.async_discover",
        return_value=[
            {
                SL_GATEWAY_IP: "1.1.1.1",
                SL_GATEWAY_PORT: 80,
                SL_GATEWAY_TYPE: 12,
                SL_GATEWAY_SUBTYPE: 2,
                SL_GATEWAY_NAME: "Pentair: 01-01-01",
            },
        ],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("gateway_select")

    with patch(
        "homeassistant.components.screenlogic.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={GATEWAY_SELECT_KEY: "00:c0:33:01:01:01"}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Pentair: 01-01-01")
    expect(result2["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_PORT: 80,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def flow_discover_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test when discovery errors."""

    with patch(
        "homeassistant.components.screenlogic.config_flow.discovery.async_discover",
        side_effect=ScreenLogicError("Fake error"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("gateway_entry")

    with (
        patch(
            "homeassistant.components.screenlogic.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.screenlogic.config_flow.login.async_get_mac_address",
            return_value="00-C0-33-01-01-01",
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "1.1.1.1",
                CONF_PORT: 80,
            },
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("Pentair: 01-01-01")
    expect(result3["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_PORT: 80,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="Pentair: 01-01-01",
            ip="1.1.1.1",
            macaddress="aabbccddeeff",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("gateway_entry")

    with (
        patch(
            "homeassistant.components.screenlogic.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.screenlogic.config_flow.login.async_get_mac_address",
            return_value="00-C0-33-01-01-01",
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "1.1.1.1",
                CONF_PORT: 80,
            },
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("Pentair: 01-01-01")
    expect(result3["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_PORT: 80,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_manual_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""

    with patch(
        "homeassistant.components.screenlogic.config_flow.discovery.async_discover",
        return_value=[
            {
                SL_GATEWAY_IP: "1.1.1.1",
                SL_GATEWAY_PORT: 80,
                SL_GATEWAY_TYPE: 12,
                SL_GATEWAY_SUBTYPE: 2,
                SL_GATEWAY_NAME: "Pentair: 01-01-01",
            },
        ],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("gateway_select")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={GATEWAY_SELECT_KEY: GATEWAY_MANUAL_ENTRY}
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({})
    expect(result2["step_id"]).to_equal("gateway_entry")

    with (
        patch(
            "homeassistant.components.screenlogic.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.screenlogic.config_flow.login.async_get_mac_address",
            return_value="00-C0-33-01-01-01",
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "1.1.1.1",
                CONF_PORT: 80,
            },
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("Pentair: 01-01-01")
    expect(result3["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_PORT: 80,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    with patch(
        "homeassistant.components.screenlogic.config_flow.discovery.async_discover",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    with patch(
        "homeassistant.components.screenlogic.config_flow.login.async_get_mac_address",
        side_effect=ScreenLogicError("Failed to connect to host at 1.1.1.1:80"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "1.1.1.1",
                CONF_PORT: 80,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_IP_ADDRESS: "cannot_connect"})


@test
async def option_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.screenlogic.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 15},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_SCAN_INTERVAL: 15})


@test
async def option_flow_defaults(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.screenlogic.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        }
    )


@test
async def option_flow_input_floor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.screenlogic.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_SCAN_INTERVAL: 1}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_SCAN_INTERVAL: MIN_SCAN_INTERVAL,
        }
    )
