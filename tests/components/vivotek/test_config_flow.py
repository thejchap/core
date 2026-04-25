"""Tests for the Vivotek config flow."""

from unittest.mock import AsyncMock

from libpyvivotek.vivotek import VivotekCameraError
from tryke import Depends, expect, fixture, test

from homeassistant.components.vivotek.camera import DEFAULT_FRAMERATE, DEFAULT_NAME
from homeassistant.components.vivotek.const import (
    CONF_FRAMERATE,
    CONF_SECURITY_LEVEL,
    CONF_STREAM_PATH,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_setup_entry, mock_vivotek_camera

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


USER_DATA = {
    CONF_IP_ADDRESS: "1.2.3.4",
    CONF_PORT: 80,
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "pass1234",
    CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
    CONF_SSL: False,
    CONF_VERIFY_SSL: True,
    CONF_SECURITY_LEVEL: "admin",
    CONF_STREAM_PATH: "/live.sdp",
}

IMPORT_DATA = {
    CONF_IP_ADDRESS: "1.2.3.4",
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "pass1234",
    CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
    CONF_SSL: False,
    CONF_VERIFY_SSL: True,
    CONF_SECURITY_LEVEL: "admin",
    CONF_STREAM_PATH: "/live.sdp",
    CONF_FRAMERATE: DEFAULT_FRAMERATE,
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_setup_entry),
    _camera: AsyncMock = Depends(mock_vivotek_camera),
) -> None:
    """Test full user initiated flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_DATA
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(USER_DATA)
    expect(result["options"]).to_equal({CONF_FRAMERATE: DEFAULT_FRAMERATE})
    expect(result["result"].unique_id).to_equal("11:22:33:44:55:66")


@test.cases(
    test.case("cannot_connect", exception=VivotekCameraError, error="cannot_connect"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def user_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_setup_entry),
    camera: AsyncMock = Depends(mock_vivotek_camera),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test user initiated flow with exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    camera.get_mac.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_DATA
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    camera.get_mac.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_DATA
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test flow abort on duplicate entry."""
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def duplicate_entry_mac(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _camera: AsyncMock = Depends(mock_vivotek_camera),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test flow abort on duplicate MAC address."""
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_DATA, CONF_IP_ADDRESS: "1.1.1.1"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def import_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_setup_entry),
    _camera: AsyncMock = Depends(mock_vivotek_camera),
) -> None:
    """Test import initiated flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=IMPORT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(USER_DATA)
    expect(result["options"]).to_equal({CONF_FRAMERATE: DEFAULT_FRAMERATE})
    expect(result["result"].unique_id).to_equal("11:22:33:44:55:66")


@test.cases(
    test.case("cannot_connect", exception=VivotekCameraError, reason="cannot_connect"),
    test.case("unknown", exception=Exception, reason="unknown"),
)
async def import_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_setup_entry),
    camera: AsyncMock = Depends(mock_vivotek_camera),
    *,
    exception: type[Exception],
    reason: str,
) -> None:
    """Test import initiated flow with exceptions."""
    camera.get_mac.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=IMPORT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def import_flow_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test import initiated flow with duplicate entry."""
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=IMPORT_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def import_flow_duplicate_mac(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _camera: AsyncMock = Depends(mock_vivotek_camera),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test import initiated flow with duplicate MAC."""
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={**IMPORT_DATA, CONF_IP_ADDRESS: "1.1.1.1"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _camera: AsyncMock = Depends(mock_vivotek_camera),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test options flow."""
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_FRAMERATE: 15},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(entry.options[CONF_FRAMERATE]).to_equal(15)
