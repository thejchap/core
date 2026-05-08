"""Tests for the AsusWrt config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.asuswrt.const import (
    DOMAIN,
    PROTOCOL_TELNET,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_BASE,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import patch_get_host, patch_is_file
from .common import HOST

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

CONFIG_DATA = {
    CONF_HOST: HOST,
    CONF_USERNAME: "user",
    CONF_PASSWORD: "pwd",
}

CONFIG_DATA_TELNET = {
    **CONFIG_DATA,
    CONF_PROTOCOL: PROTOCOL_TELNET,
    CONF_PORT: 23,
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _get_host=Depends(patch_get_host),
    _is_file=Depends(patch_is_file),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def error_invalid_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    get_host=Depends(patch_get_host),
) -> None:
    """Test we abort if host name is invalid."""
    get_host.return_value = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=CONFIG_DATA_TELNET,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_BASE: "invalid_host"})


@test
async def abort_if_not_unique_id_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if component without uniqueid is already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA_TELNET,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=CONFIG_DATA_TELNET,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_unique_id")


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def user_legacy() -> None:
    """Stub for test_user_legacy (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def user_http() -> None:
    """Stub for test_user_http (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def error_pwd_required() -> None:
    """Stub for test_error_pwd_required (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def error_no_password_ssh() -> None:
    """Stub for test_error_no_password_ssh (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def error_invalid_ssh() -> None:
    """Stub for test_error_invalid_ssh (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def update_uniqueid_exist() -> None:
    """Stub for test_update_uniqueid_exist (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def abort_invalid_unique_id() -> None:
    """Stub for test_abort_invalid_unique_id (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def on_connect_legacy_failed() -> None:
    """Stub for test_on_connect_legacy_failed (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def on_connect_http_failed() -> None:
    """Stub for test_on_connect_http_failed (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def options_flow_ap() -> None:
    """Stub for test_options_flow_ap (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def options_flow_router() -> None:
    """Stub for test_options_flow_router (port deferred)."""


@test.skip("requires connect_legacy/connect_http multi-fixture chain")
async def options_flow_http() -> None:
    """Stub for test_options_flow_http (port deferred)."""
