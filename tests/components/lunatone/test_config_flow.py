"""Define tests for the Lunatone config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock

import aiohttp
from lunatone_rest_api_client.models import InfoData
from tryke import Depends, expect, fixture, test
from yarl import URL

from homeassistant.components.lunatone.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import (
    BASE_IP,
    BASE_URL,
    INFO_DATA,
    LEGACY_INFO_DATA,
    MANUFACTURER,
    UUID,
    setup_integration,
)
from ._fixtures import (
    mock_config_entry,
    mock_lunatone_devices,
    mock_lunatone_info,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address(BASE_IP),
    ip_addresses=[ip_address(BASE_IP)],
    hostname="dali2_display.local.",
    name="DALI-2 Display._http._tcp.local.",
    port=80,
    type="_http._tcp.local.",
    properties={
        "path": "/",
        "manufacturer": MANUFACTURER.lower(),
        "device": "dali-2 display",
        "uid": UUID.lower(),
        "type": "dali-2-display",
    },
)


@test.cases(
    test.case("info_data", info_data=INFO_DATA),
    test.case("legacy_info_data", info_data=LEGACY_INFO_DATA),
)
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    info: AsyncMock = Depends(mock_lunatone_info),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    info_data: InfoData,
) -> None:
    """Test full user flow."""
    info.set_data(info_data)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: BASE_URL},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(BASE_URL)
    expect(result["data"]).to_equal({CONF_URL: BASE_URL})


@test
async def full_flow_fail_because_of_missing_device_infos(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    info: AsyncMock = Depends(mock_lunatone_info),
) -> None:
    """Test full flow."""
    info.serial_number = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: BASE_URL},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "missing_device_info"})


@test
async def device_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the flow is aborted when the device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_URL: BASE_URL},
    )

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_url",
        exception=aiohttp.InvalidUrlClientError(BASE_URL),
        expected_error="invalid_url",
    ),
    test.case(
        "cannot_connect",
        exception=aiohttp.ClientConnectionError(),
        expected_error="cannot_connect",
    ),
)
async def user_step_fail_with_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    info: AsyncMock = Depends(mock_lunatone_info),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test user step with an error."""
    info.async_update.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: BASE_URL},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    info.async_update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: BASE_URL},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(BASE_URL)
    expect(result["data"]).to_equal({CONF_URL: BASE_URL})


@test
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _devices: AsyncMock = Depends(mock_lunatone_devices),
    _info: AsyncMock = Depends(mock_lunatone_info),
) -> None:
    """Test zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_DISCOVERY
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(BASE_URL)
    expect(result["data"]).to_equal({CONF_URL: BASE_URL})
    expect(result["result"].unique_id).to_equal(UUID.replace("-", ""))


@test
async def zeroconf_flow_abort_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _devices: AsyncMock = Depends(mock_lunatone_devices),
    _info: AsyncMock = Depends(mock_lunatone_info),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf flow aborts with duplicate."""
    await setup_integration(hass, config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_url",
        exception=aiohttp.InvalidUrlClientError(BASE_URL),
        expected_error="invalid_url",
    ),
    test.case(
        "cannot_connect",
        exception=aiohttp.ClientConnectionError(),
        expected_error="cannot_connect",
    ),
)
async def zeroconf_flow_abort_with_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _devices: AsyncMock = Depends(mock_lunatone_devices),
    info: AsyncMock = Depends(mock_lunatone_info),
    *,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test zeroconf flow aborts with error."""
    info.async_update.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_error)

    info.async_update.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _info: AsyncMock = Depends(mock_lunatone_info),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    url = URL.build(scheme="http", host="10.0.0.100").human_repr()[:-1]

    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: url}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal({CONF_URL: url})


@test.cases(
    test.case(
        "invalid_url",
        exception=aiohttp.InvalidUrlClientError(BASE_URL),
        expected_error="invalid_url",
    ),
    test.case(
        "cannot_connect",
        exception=aiohttp.ClientConnectionError(),
        expected_error="cannot_connect",
    ),
)
async def reconfigure_fail_with_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    info: AsyncMock = Depends(mock_lunatone_info),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test reconfigure flow with an error."""
    url = URL.build(scheme="http", host="10.0.0.100").human_repr()[:-1]

    info.async_update.side_effect = exception

    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: url}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    info.async_update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: url}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data).to_equal({CONF_URL: url})
