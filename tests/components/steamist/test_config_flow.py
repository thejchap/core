"""Test the Steamist config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.steamist.const import DOMAIN
from homeassistant.config_entries import SOURCE_IGNORE
from homeassistant.const import CONF_DEVICE, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from . import (
    DEFAULT_ENTRY_DATA,
    DEVICE_30303_NOT_STEAMIST,
    DEVICE_HOSTNAME,
    DEVICE_IP_ADDRESS,
    DEVICE_MAC_ADDRESS,
    DEVICE_NAME,
    DISCOVERY_30303,
    FORMATTED_MAC_ADDRESS,
    MOCK_ASYNC_GET_STATUS_INACTIVE,
    _patch_discovery,
    _patch_status,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MODULE = "homeassistant.components.steamist"

DHCP_DISCOVERY = DhcpServiceInfo(
    hostname=DEVICE_HOSTNAME,
    ip=DEVICE_IP_ADDRESS,
    macaddress=DEVICE_MAC_ADDRESS.lower().replace(":", ""),
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        _patch_discovery(no_device=True),
        patch(
            "homeassistant.components.steamist.config_flow.Steamist.async_get_status"
        ),
        patch(
            "homeassistant.components.steamist.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "127.0.0.1"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("127.0.0.1")
    expect(result2["data"]).to_equal({"host": "127.0.0.1"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_with_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can also discovery the device during manual setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        _patch_discovery(),
        patch(
            "homeassistant.components.steamist.config_flow.Steamist.async_get_status"
        ),
        patch(
            "homeassistant.components.steamist.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "127.0.0.1"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(DEVICE_NAME)
    expect(result2["data"]).to_equal(DEFAULT_ENTRY_DATA)
    expect(result2["context"]["unique_id"]).to_equal(FORMATTED_MAC_ADDRESS)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.steamist.config_flow.Steamist.async_get_status",
        side_effect=TimeoutError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "127.0.0.1"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unknown exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.steamist.config_flow.Steamist.async_get_status",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "127.0.0.1"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up discovery."""
    with _patch_discovery(), _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(bool(result["errors"])).to_be(False)

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("pick_device")
        expect(bool(result2["errors"])).to_be(False)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(bool(result["errors"])).to_be(False)

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("pick_device")
        expect(bool(result2["errors"])).to_be(False)

    with (
        _patch_discovery(),
        _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE),
        patch(f"{MODULE}.async_setup", return_value=True) as mock_setup,
        patch(f"{MODULE}.async_setup_entry", return_value=True) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: FORMATTED_MAC_ADDRESS},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(DEVICE_NAME)
    expect(result3["data"]).to_equal(DEFAULT_ENTRY_DATA)
    mock_setup.assert_called_once()
    mock_setup_entry.assert_called_once()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    with _patch_discovery(), _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("no_devices_found")


@test
async def discovered_by_discovery_and_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form with discovery and abort for dhcp source when we get both."""

    with _patch_discovery(), _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data=DISCOVERY_30303,
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with _patch_discovery(), _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE):
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_DISCOVERY,
        )
        await hass.async_block_till_done()
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_in_progress")

    with _patch_discovery(), _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE):
        result3 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                hostname="any",
                ip=DEVICE_IP_ADDRESS,
                macaddress="000000000000",
            ),
        )
        await hass.async_block_till_done()
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("already_in_progress")


@test
async def discovered_by_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup when discovered from discovery."""

    with _patch_discovery(), _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data=DISCOVERY_30303,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        _patch_discovery(),
        _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE),
        patch(f"{MODULE}.async_setup", return_value=True) as mock_async_setup,
        patch(
            f"{MODULE}.async_setup_entry", return_value=True
        ) as mock_async_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(DEFAULT_ENTRY_DATA)
    expect(mock_async_setup.called).to_be(True)
    expect(mock_async_setup_entry.called).to_be(True)


@test
async def discovered_by_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup when discovered from dhcp."""

    with _patch_discovery(), _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_DISCOVERY,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        _patch_discovery(),
        _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE),
        patch(f"{MODULE}.async_setup", return_value=True) as mock_async_setup,
        patch(
            f"{MODULE}.async_setup_entry", return_value=True
        ) as mock_async_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(DEFAULT_ENTRY_DATA)
    expect(mock_async_setup.called).to_be(True)
    expect(mock_async_setup_entry.called).to_be(True)


@test
async def discovered_by_dhcp_discovery_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup when discovered from dhcp but then we cannot get the device name."""

    with (
        _patch_discovery(no_device=True),
        _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_DISCOVERY,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def discovered_by_dhcp_discovery_finds_non_steamist_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup when discovered from dhcp but its not a steamist device."""

    with (
        _patch_discovery(device=DEVICE_30303_NOT_STEAMIST),
        _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DHCP_DISCOVERY,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_steamist_device")


@test.cases(
    test.case("dhcp", source=config_entries.SOURCE_DHCP, data=DHCP_DISCOVERY),
    test.case(
        "integration_discovery",
        source=config_entries.SOURCE_INTEGRATION_DISCOVERY,
        data=DISCOVERY_30303,
    ),
)
async def discovered_by_dhcp_or_discovery_adds_missing_unique_id(
    source: str,
    data: DhcpServiceInfo | dict,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup when discovered from dhcp or discovery and add a missing unique id."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: DEVICE_IP_ADDRESS})
    config_entry.add_to_hass(hass)

    with (
        _patch_discovery(),
        _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE),
        patch(f"{MODULE}.async_setup", return_value=True) as mock_setup,
        patch(f"{MODULE}.async_setup_entry", return_value=True) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": source}, data=data
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry.unique_id).to_equal(FORMATTED_MAC_ADDRESS)
    expect(mock_setup.called).to_be(True)
    expect(mock_setup_entry.called).to_be(True)


@test.cases(
    test.case("dhcp", source=config_entries.SOURCE_DHCP, data=DHCP_DISCOVERY),
    test.case(
        "integration_discovery",
        source=config_entries.SOURCE_INTEGRATION_DISCOVERY,
        data=DISCOVERY_30303,
    ),
)
async def discovered_by_dhcp_or_discovery_existing_unique_id_does_not_reload(
    source: str,
    data: DhcpServiceInfo | dict,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup when discovered from dhcp or discovery and it does not reload."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=DEFAULT_ENTRY_DATA, unique_id=FORMATTED_MAC_ADDRESS
    )
    config_entry.add_to_hass(hass)

    with (
        _patch_discovery(),
        _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE),
        patch(f"{MODULE}.async_setup", return_value=True) as mock_setup,
        patch(f"{MODULE}.async_setup_entry", return_value=True) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": source}, data=data
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(mock_setup.called).to_be(False)
    expect(mock_setup_entry.called).to_be(False)


@test
async def pick_device_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the pick device step can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FORMATTED_MAC_ADDRESS,
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with _patch_discovery(), _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("pick_device")

    expect(
        FORMATTED_MAC_ADDRESS in result2["data_schema"].schema[CONF_DEVICE].container
    ).to_be(True)

    with (
        _patch_discovery(),
        _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE),
        patch(f"{MODULE}.async_setup", return_value=True),
        patch(f"{MODULE}.async_setup_entry", return_value=True),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_DEVICE: FORMATTED_MAC_ADDRESS},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(DEVICE_NAME)
    expect(result3["data"]).to_equal(DEFAULT_ENTRY_DATA)
    expect(result3["result"].unique_id).to_equal(FORMATTED_MAC_ADDRESS)
