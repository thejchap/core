"""Tests for the Crownstone integration config flow."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from crownstone_cloud.cloud_models.spheres import Spheres
from crownstone_cloud.exceptions import (
    CrownstoneAuthenticationError,
    CrownstoneUnknownError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.crownstone.const import (
    CONF_USB_PATH,
    CONF_USB_SPHERE,
    DOMAIN,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def crownstone_setup() -> Generator[MagicMock | AsyncMock]:
    """Mock Crownstone entry setup."""
    with patch(
        "homeassistant.components.crownstone.async_setup_entry", return_value=True
    ) as setup_mock:
        yield setup_mock


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


def get_mocked_crownstone_cloud(spheres: dict[str, MagicMock] | None = None) -> MagicMock:
    """Return a mocked Crownstone Cloud instance."""
    mock_cloud = MagicMock()
    mock_cloud.async_initialize = AsyncMock()
    mock_cloud.cloud_data = Spheres(MagicMock(), "account_id")
    mock_cloud.cloud_data.data = spheres
    return mock_cloud


def create_mocked_entry_data_conf(email: str, password: str) -> dict:
    """Set a result for the entry data for comparison."""
    return {CONF_EMAIL: email, CONF_PASSWORD: password}


def create_mocked_entry_options_conf(
    usb_path: str | None, usb_sphere: str | None
) -> dict:
    """Set a result for the entry options for comparison."""
    return {CONF_USB_PATH: usb_path, CONF_USB_SPHERE: usb_sphere}


async def start_config_flow(hass: HomeAssistant, mocked_cloud: MagicMock):
    """Patch Crownstone Cloud and start the flow."""
    mocked_login_input = {
        CONF_EMAIL: "example@homeassistant.com",
        CONF_PASSWORD: "homeassistantisawesome",
    }

    with patch(
        "homeassistant.components.crownstone.config_flow.CrownstoneCloud",
        return_value=mocked_cloud,
    ):
        return await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=mocked_login_input
        )


@test
async def no_user_input(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(crownstone_setup),
) -> None:
    """Test the flow done in the correct way."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(setup.call_count).to_equal(0)


@test
async def abort_if_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(crownstone_setup),
) -> None:
    """Test flow with correct login input and abort if sphere already configured."""
    configured_entry_data = create_mocked_entry_data_conf(
        email="example@homeassistant.com",
        password="homeassistantisawesome",
    )
    configured_entry_options = create_mocked_entry_options_conf(
        usb_path="/dev/serial/by-id/crownstone-usb",
        usb_sphere="sphere_id",
    )

    MockConfigEntry(
        domain=DOMAIN,
        data=configured_entry_data,
        options=configured_entry_options,
        unique_id="account_id",
    ).add_to_hass(hass)

    result = await start_config_flow(hass, get_mocked_crownstone_cloud())

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(setup.call_count).to_equal(0)


@test
async def authentication_errors(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(crownstone_setup),
) -> None:
    """Test flow with wrong auth errors."""
    cloud = get_mocked_crownstone_cloud()
    cloud.async_initialize.side_effect = CrownstoneAuthenticationError(
        exception_type="LOGIN_FAILED"
    )

    result = await start_config_flow(hass, cloud)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    cloud.async_initialize.side_effect = CrownstoneAuthenticationError(
        exception_type="LOGIN_FAILED_EMAIL_NOT_VERIFIED"
    )

    result = await start_config_flow(hass, cloud)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "account_not_verified"})
    expect(setup.call_count).to_equal(0)


@test
async def unknown_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(crownstone_setup),
) -> None:
    """Test flow with unknown error."""
    cloud = get_mocked_crownstone_cloud()
    cloud.async_initialize.side_effect = CrownstoneUnknownError

    result = await start_config_flow(hass, cloud)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})
    expect(setup.call_count).to_equal(0)


@test.skip("USB flow with pyserial_comports needs more setup")
async def successful_login_no_usb(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a successful login without configuring a USB."""


@test.skip("USB flow with pyserial_comports needs more setup")
async def successful_login_with_usb(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a successful login with USB configuration."""


@test.skip("USB manual path flow needs more setup")
async def successful_login_with_manual_usb_path(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a successful login with manual USB path."""
