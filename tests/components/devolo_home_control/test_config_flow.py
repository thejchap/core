"""Test the devolo_home_control config flow."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.devolo_home_control.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_async_zeroconf, mydevolo
from .const import (
    DISCOVERY_INFO,
    DISCOVERY_INFO_WRONG_DEVICE,
    DISCOVERY_INFO_WRONG_DEVOLO_DEVICE,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zeroconf: MagicMock = Depends(mock_async_zeroconf),
    _mydevolo: MagicMock = Depends(mydevolo),
) -> None:
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
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("devolo Home Control")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        }
    )


@test
async def form_invalid_credentials_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mydevolo_mock: MagicMock = Depends(mydevolo),
) -> None:
    """Test if we get the error message on invalid credentials."""
    mydevolo_mock.credentials_valid.return_value = False
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username", CONF_PASSWORD: "wrong-password"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    mydevolo_mock.credentials_valid.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username", CONF_PASSWORD: "correct-password"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "correct-password",
        }
    )


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if we get the error message on already configured."""
    MockConfigEntry(domain=DOMAIN, unique_id="123456", data={}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the zeroconf confirmation form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("devolo Home Control")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        }
    )


@test
async def form_invalid_credentials_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mydevolo_mock: MagicMock = Depends(mydevolo),
) -> None:
    """Test if we get the error message on invalid credentials."""
    mydevolo_mock.credentials_valid.return_value = False
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    mydevolo_mock.credentials_valid.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username", CONF_PASSWORD: "correct-password"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zeroconf_wrong_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the zeroconf ignores wrong devices."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO_WRONG_DEVOLO_DEVICE,
    )
    expect(result["reason"]).to_equal("Not a devolo Home Control gateway.")
    expect(result["type"]).to_be(FlowResultType.ABORT)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO_WRONG_DEVICE,
    )

    expect(result["reason"]).to_equal("Not a devolo Home Control gateway.")
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def form_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the reauth confirmation form is served."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id="123456",
        data={
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username-new", CONF_PASSWORD: "test-password-new"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def form_invalid_credentials_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mydevolo_mock: MagicMock = Depends(mydevolo),
) -> None:
    """Test if we get the error message on invalid credentials."""
    mydevolo_mock.credentials_valid.return_value = False
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id="123456",
        data={
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username", CONF_PASSWORD: "wrong-password"},
    )
    expect(result["errors"]).to_equal({"base": "invalid_auth"})
    expect(result["type"]).to_be(FlowResultType.FORM)

    mydevolo_mock.credentials_valid.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username-new", CONF_PASSWORD: "correct-password"},
    )
    expect(result["reason"]).to_equal("reauth_successful")
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def form_uuid_change_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the reauth confirmation form is served."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id="123457",
        data={
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test-username-new", CONF_PASSWORD: "test-password-new"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "reauth_failed"})
