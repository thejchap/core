"""Test the Imeon Inverter config flow."""

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.imeon_inverter.const import DOMAIN
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import ATTR_UPNP_SERIAL

from tests.common import MockConfigEntry
from tests.components.imeon_inverter._fixtures import (
    TEST_DISCOVER,
    TEST_SERIAL,
    TEST_USER_INPUT,
    mock_async_setup_entry,
    mock_config_entry,
    mock_imeon_inverter,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form_valid(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_async_setup_entry: AsyncMock = Depends(mock_async_setup_entry),
    _mock_imeon_inverter: MagicMock = Depends(mock_imeon_inverter),
) -> None:
    """Test we get the form and the config is created with the good entries."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Imeon {TEST_SERIAL}")
    expect(result["data"]).to_equal(TEST_USER_INPUT)
    expect(result["result"].unique_id).to_equal(TEST_SERIAL)
    expect(mock_async_setup_entry.call_count).to_equal(1)


@test
async def form_invalid_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_imeon_inverter: MagicMock = Depends(mock_imeon_inverter),
    _mock_async_setup_entry: AsyncMock = Depends(mock_async_setup_entry),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    mock_imeon_inverter.login.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    mock_imeon_inverter.login.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("timeout", error=TimeoutError, expected="cannot_connect"),
    test.case(
        "invalid_host", error=ValueError("Host invalid"), expected="invalid_host"
    ),
    test.case(
        "invalid_route", error=ValueError("Route invalid"), expected="invalid_route"
    ),
    test.case("unknown", error=ValueError, expected="unknown"),
)
async def form_exception(
    error: type[Exception] | Exception,
    expected: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_imeon_inverter: MagicMock = Depends(mock_imeon_inverter),
    _mock_async_setup_entry: AsyncMock = Depends(mock_async_setup_entry),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    mock_imeon_inverter.login.side_effect = error

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected})

    mock_imeon_inverter.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def manual_setup_already_exists(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_async_setup_entry: AsyncMock = Depends(mock_async_setup_entry),
    _mock_imeon_inverter: MagicMock = Depends(mock_imeon_inverter),
) -> None:
    """Test that a flow with an existing id aborts."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def get_serial_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_imeon_inverter: MagicMock = Depends(mock_imeon_inverter),
    _mock_async_setup_entry: AsyncMock = Depends(mock_async_setup_entry),
) -> None:
    """Test the timeout error handling of getting the serial number."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    mock_imeon_inverter.get_serial.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_imeon_inverter.get_serial.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def ssdp(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_async_setup_entry: AsyncMock = Depends(mock_async_setup_entry),
    _mock_imeon_inverter: MagicMock = Depends(mock_imeon_inverter),
) -> None:
    """Test a ssdp discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=TEST_DISCOVER,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    user_input = TEST_USER_INPUT.copy()
    user_input.pop(CONF_HOST)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Imeon {TEST_SERIAL}")
    expect(result["data"]).to_equal(TEST_USER_INPUT)


@test
async def ssdp_already_exist(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_async_setup_entry: AsyncMock = Depends(mock_async_setup_entry),
    _mock_imeon_inverter: MagicMock = Depends(mock_imeon_inverter),
) -> None:
    """Test that a ssdp discovery flow with an existing id aborts."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=TEST_DISCOVER,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_async_setup_entry: AsyncMock = Depends(mock_async_setup_entry),
    _mock_imeon_inverter: MagicMock = Depends(mock_imeon_inverter),
) -> None:
    """Test that a ssdp discovery aborts if serial is unknown."""
    data = deepcopy(TEST_DISCOVER)
    data.upnp.pop(ATTR_UPNP_SERIAL, None)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=data,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")
