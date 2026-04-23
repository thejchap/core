"""Test the IntelliClima config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from pyintelliclima.api import (
    IntelliClimaAPIError,
    IntelliClimaAuthError,
    IntelliClimaDevices,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.intelliclima.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.intelliclima._fixtures import (
    mock_cloud_interface,
    mock_config_entry,
    mock_setup_entry,
    single_eco_device,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

DATA_CONFIG = {
    CONF_USERNAME: "SuperUser",
    CONF_PASSWORD: "hunter2",
}


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
async def user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_cloud_interface: AsyncMock = Depends(mock_cloud_interface),
) -> None:
    """Test the full config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DATA_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("IntelliClima (SuperUser)")
    expect(result["data"]).to_equal(DATA_CONFIG)


@test.cases(
    test.case("invalid_auth", side_effect=IntelliClimaAuthError, error="invalid_auth"),
    test.case(
        "cannot_connect", side_effect=IntelliClimaAPIError, error="cannot_connect"
    ),
    test.case(
        "unknown", side_effect=RuntimeError("Unexpected error"), error="unknown"
    ),
)
async def form_auth_errors(
    side_effect: type[Exception] | Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_cloud_interface: AsyncMock = Depends(mock_cloud_interface),
) -> None:
    """Test we handle authentication-related errors and recover."""
    mock_cloud_interface.authenticate.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DATA_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_cloud_interface.authenticate.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DATA_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("IntelliClima (SuperUser)")
    expect(result["data"]).to_equal(DATA_CONFIG)


@test
async def form_no_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_cloud_interface: AsyncMock = Depends(mock_cloud_interface),
    single_eco_device: IntelliClimaDevices = Depends(single_eco_device),
) -> None:
    """Test we handle no devices found error."""
    mock_cloud_interface.get_all_device_status.return_value = IntelliClimaDevices(
        ecocomfort2_devices={}, c800_devices={}
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DATA_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_devices"})

    mock_cloud_interface.get_all_device_status.return_value = single_eco_device

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DATA_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("IntelliClima (SuperUser)")
    expect(result["data"]).to_equal(DATA_CONFIG)


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_cloud_interface: AsyncMock = Depends(mock_cloud_interface),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test creating a second config for the same account aborts."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DATA_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
