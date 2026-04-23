"""Test the Fujitsu HVAC (based on Ayla IOT) config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from ayla_iot_unofficial import AylaAuthError
from tryke import Depends, expect, fixture, test

from homeassistant.components.fujitsu_fglair.const import (
    CONF_REGION,
    DOMAIN,
    REGION_DEFAULT,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType

from tests.common import MockConfigEntry
from tests.components.fujitsu_fglair._fixtures import (
    TEST_PASSWORD,
    TEST_PASSWORD2,
    TEST_USERNAME,
    mock_ayla_api,
    mock_config_entry,
    mock_setup_entry,
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


async def _initial_step(hass: HomeAssistant) -> FlowResult:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_REGION: REGION_DEFAULT,
        },
    )


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ayla_api: AsyncMock = Depends(mock_ayla_api),
) -> None:
    """Test full config flow."""
    result = await _initial_step(hass)
    mock_ayla_api.async_sign_in.assert_called_once()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"FGLair ({TEST_USERNAME})")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_REGION: REGION_DEFAULT,
        }
    )


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ayla_api: AsyncMock = Depends(mock_ayla_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that re-adding the same account fails."""
    mock_config_entry.add_to_hass(hass)
    result = await _initial_step(hass)
    mock_ayla_api.async_sign_in.assert_not_called()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("auth", exception=AylaAuthError, err_msg="invalid_auth"),
    test.case("timeout", exception=TimeoutError, err_msg="cannot_connect"),
    test.case("generic", exception=Exception, err_msg="unknown"),
)
async def form_exceptions(
    exception: type[Exception],
    err_msg: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ayla_api: AsyncMock = Depends(mock_ayla_api),
) -> None:
    """Test we handle exceptions."""
    mock_ayla_api.async_sign_in.side_effect = exception
    result = await _initial_step(hass)
    mock_ayla_api.async_sign_in.assert_called_once()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": err_msg})

    mock_ayla_api.async_sign_in.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_REGION: REGION_DEFAULT,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"FGLair ({TEST_USERNAME})")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_REGION: REGION_DEFAULT,
        }
    )


@test
async def reauth_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_ayla_api: AsyncMock = Depends(mock_ayla_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: TEST_PASSWORD2,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal(TEST_PASSWORD2)


@test.cases(
    test.case("auth", exception=AylaAuthError, err_msg="invalid_auth"),
    test.case("timeout", exception=TimeoutError, err_msg="cannot_connect"),
    test.case("generic", exception=Exception, err_msg="unknown"),
)
async def reauth_exceptions(
    exception: type[Exception],
    err_msg: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ayla_api: AsyncMock = Depends(mock_ayla_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow when an exception occurs."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_ayla_api.async_sign_in.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: TEST_PASSWORD2,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": err_msg})

    mock_ayla_api.async_sign_in.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: TEST_PASSWORD2,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal(TEST_PASSWORD2)
