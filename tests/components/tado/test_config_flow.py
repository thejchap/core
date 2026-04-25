"""Test the Tado config flow."""

from ipaddress import ip_address
import threading
from unittest.mock import AsyncMock, MagicMock, patch

from PyTado.http import DeviceActivationStatus
from tryke import Depends, expect, fixture, test

from homeassistant.components.tado.config_flow import TadoException
from homeassistant.components.tado.const import (
    CONF_FALLBACK,
    CONF_REFRESH_TOKEN,
    CONST_OVERLAY_TADO_DEFAULT,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_HOMEKIT, SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import (
    ATTR_PROPERTIES_ID,
    ZeroconfServiceInfo,
)

from ._fixtures import mock_config_entry, mock_setup_entry, mock_tado_api

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tado_api: MagicMock = Depends(mock_tado_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full flow of the config flow."""
    event = threading.Event()

    def mock_tado_api_device_activation() -> None:
        event.wait(timeout=5)

    tado_api.device_activation = mock_tado_api_device_activation

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("user")

    event.set()
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("home name")
    expect(result["data"]).to_equal({CONF_REFRESH_TOKEN: "refresh"})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def full_flow_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tado_api: MagicMock = Depends(mock_tado_api),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full flow of the config when reauthticating."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="ABC-123-DEF-456",
        data={CONF_REFRESH_TOKEN: "totally_refresh_for_reauth"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    event = threading.Event()

    def mock_tado_api_device_activation() -> None:
        event.wait(timeout=5)

    tado_api.device_activation = mock_tado_api_device_activation

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("user")

    event.set()
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("home name")
    expect(result["data"]).to_equal({CONF_REFRESH_TOKEN: "refresh"})


@test
async def auth_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tado_api: MagicMock = Depends(mock_tado_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the auth timeout."""
    tado_api.device_activation_status.return_value = DeviceActivationStatus.PENDING

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS_DONE)
    expect(result["step_id"]).to_equal("timeout")

    tado_api.device_activation_status.return_value = DeviceActivationStatus.COMPLETED

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("timeout")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("home name")
    expect(result["data"]).to_equal({CONF_REFRESH_TOKEN: "refresh"})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def no_homes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tado_api: MagicMock = Depends(mock_tado_api),
) -> None:
    """Test the full flow of the config flow."""
    tado_api.get_me.return_value["homes"] = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS_DONE)
    expect(result["step_id"]).to_equal("finish_login")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_homes")


@test
async def tado_creation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle Form Exceptions."""
    with patch(
        "homeassistant.components.tado.config_flow.Tado",
        side_effect=TadoException("Test exception"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test.cases(
    test.case("generic", exception=Exception, error="timeout"),
    test.case("tado", exception=TadoException, error="timeout"),
)
async def wait_for_login_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tado_api: MagicMock = Depends(mock_tado_api),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test that an exception in wait for login is handled properly."""
    tado_api.device_activation.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS_DONE)
    expect(result["step_id"]).to_equal(error)


@test
async def wait_for_login_rate_limit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tado_api: MagicMock = Depends(mock_tado_api),
) -> None:
    """Test that a rate limit error in wait_for_login is handled properly."""
    tado_api.device_activation.side_effect = TadoException("rate limited")
    tado_api.rate_limit_info.return_value = {"remaining": "0"}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("api_rate_limit_reached")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tado_api: MagicMock = Depends(mock_tado_api),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow options."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_FALLBACK: CONST_OVERLAY_TADO_DEFAULT},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_FALLBACK: CONST_OVERLAY_TADO_DEFAULT})


@test
async def homekit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tado_api: MagicMock = Depends(mock_tado_api),
) -> None:
    """Test that we abort from homekit if tado is already setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HOMEKIT},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=None,
            properties={ATTR_PROPERTIES_ID: "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("homekit_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal("1")


@test
async def homekit_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tado_api: MagicMock = Depends(mock_tado_api),
) -> None:
    """Test that we abort from homekit if tado is already setup."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_USERNAME: "mock", CONF_PASSWORD: "mock"}
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HOMEKIT},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=None,
            properties={ATTR_PROPERTIES_ID: "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
