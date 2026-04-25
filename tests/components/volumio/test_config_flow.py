"""Test the Volumio config flow."""

from ipaddress import ip_address
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.volumio.config_flow import CannotConnectError
from homeassistant.components.volumio.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_SYSTEM_INFO = {"id": "1111-1111-1111-1111", "name": "TestVolumio"}


TEST_CONNECTION = {
    "host": "1.1.1.1",
    "port": 3000,
}


TEST_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("1.1.1.1"),
    ip_addresses=[ip_address("1.1.1.1")],
    hostname="mock_hostname",
    name="mock_name",
    port=3000,
    properties={"volumioName": "discovered", "UUID": "2222-2222-2222-2222"},
    type="mock_type",
)

TEST_DISCOVERY_RESULT = {
    "host": TEST_DISCOVERY.host,
    "port": TEST_DISCOVERY.port,
    "id": TEST_DISCOVERY.properties["UUID"],
    "name": TEST_DISCOVERY.properties["volumioName"],
}


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
        patch(
            "homeassistant.components.volumio.config_flow.Volumio.get_system_info",
            return_value=TEST_SYSTEM_INFO,
        ),
        patch(
            "homeassistant.components.volumio.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("TestVolumio")
    expect(result2["data"]).to_equal({**TEST_SYSTEM_INFO, **TEST_CONNECTION})

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_updates_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a duplicate id aborts and updates existing entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_SYSTEM_INFO["id"],
        data={
            "host": "dummy",
            "port": 11,
            "name": "dummy",
            "id": TEST_SYSTEM_INFO["id"],
        },
    )

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with (
        patch(
            "homeassistant.components.volumio.config_flow.Volumio.get_system_info",
            return_value=TEST_SYSTEM_INFO,
        ),
        patch(
            "homeassistant.components.volumio.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")

    expect(entry.data).to_equal({**TEST_SYSTEM_INFO, **TEST_CONNECTION})


@test
async def empty_system_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test old volumio versions with empty system info."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.volumio.config_flow.Volumio.get_system_info",
            return_value={},
        ),
        patch(
            "homeassistant.components.volumio.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_CONNECTION["host"])
    expect(result2["data"]).to_equal(
        {
            "host": TEST_CONNECTION["host"],
            "port": TEST_CONNECTION["port"],
            "name": TEST_CONNECTION["host"],
            "id": None,
        }
    )

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
        "homeassistant.components.volumio.config_flow.Volumio.get_system_info",
        side_effect=CannotConnectError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle generic error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.volumio.config_flow.Volumio.get_system_info",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery flow works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=TEST_DISCOVERY
    )

    with (
        patch(
            "homeassistant.components.volumio.config_flow.Volumio.get_system_info",
            return_value=TEST_SYSTEM_INFO,
        ),
        patch(
            "homeassistant.components.volumio.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_DISCOVERY_RESULT["name"])
    expect(result2["data"]).to_equal(TEST_DISCOVERY_RESULT)

    expect(bool(result2["result"])).to_be(True)
    expect(result2["result"].unique_id).to_equal(TEST_DISCOVERY_RESULT["id"])

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def discovery_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery aborts if cannot connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=TEST_DISCOVERY
    )

    with patch(
        "homeassistant.components.volumio.config_flow.Volumio.get_system_info",
        side_effect=CannotConnectError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("cannot_connect")


@test
async def discovery_duplicate_data(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery aborts if same mDNS packet arrives."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=TEST_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=TEST_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def discovery_updates_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a duplicate discovery id aborts and updates existing entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_DISCOVERY_RESULT["id"],
        data={
            "host": "dummy",
            "port": 11,
            "name": "dummy",
            "id": TEST_DISCOVERY_RESULT["id"],
        },
        state=config_entries.ConfigEntryState.SETUP_RETRY,
    )

    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.volumio.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=TEST_DISCOVERY,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(entry.data).to_equal(TEST_DISCOVERY_RESULT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
