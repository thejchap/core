"""Define tests for the AirVisual config flow."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from pyairvisual.cloud_api import (
    InvalidKeyError,
    KeyExpiredError,
    NotFoundError,
    UnauthorizedError,
)
from pyairvisual.errors import AirVisualError
from tryke import Depends, expect, fixture, test

from homeassistant.components.airvisual import (
    CONF_CITY,
    CONF_INTEGRATION_TYPE,
    DOMAIN,
    INTEGRATION_TYPE_GEOGRAPHY_COORDS,
    INTEGRATION_TYPE_GEOGRAPHY_NAME,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_SHOW_ON_MAP
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.airvisual._fixtures import (
    COORDS_CONFIG,
    NAME_CONFIG,
    TEST_CITY,
    TEST_COUNTRY,
    TEST_LATITUDE,
    TEST_LONGITUDE,
    TEST_STATE,
    cloud_api,
    config,
    config_entry,
    mock_pyairvisual,
    mock_setup_entry,
    mock_zeroconf,
    setup_config_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "coords_airvisual_error",
        INTEGRATION_TYPE_GEOGRAPHY_COORDS,
        "geography_by_coords",
        "nearest_city",
        COORDS_CONFIG,
        f"Cloud API ({TEST_LATITUDE}, {TEST_LONGITUDE})",
        AirVisualError,
        {"base": "unknown"},
    ),
    test.case(
        "coords_invalid_key",
        INTEGRATION_TYPE_GEOGRAPHY_COORDS,
        "geography_by_coords",
        "nearest_city",
        COORDS_CONFIG,
        f"Cloud API ({TEST_LATITUDE}, {TEST_LONGITUDE})",
        InvalidKeyError,
        {CONF_API_KEY: "invalid_api_key"},
    ),
    test.case(
        "coords_key_expired",
        INTEGRATION_TYPE_GEOGRAPHY_COORDS,
        "geography_by_coords",
        "nearest_city",
        COORDS_CONFIG,
        f"Cloud API ({TEST_LATITUDE}, {TEST_LONGITUDE})",
        KeyExpiredError,
        {CONF_API_KEY: "invalid_api_key"},
    ),
    test.case(
        "coords_not_found",
        INTEGRATION_TYPE_GEOGRAPHY_COORDS,
        "geography_by_coords",
        "nearest_city",
        COORDS_CONFIG,
        f"Cloud API ({TEST_LATITUDE}, {TEST_LONGITUDE})",
        NotFoundError,
        {CONF_CITY: "location_not_found"},
    ),
    test.case(
        "coords_unauthorized",
        INTEGRATION_TYPE_GEOGRAPHY_COORDS,
        "geography_by_coords",
        "nearest_city",
        COORDS_CONFIG,
        f"Cloud API ({TEST_LATITUDE}, {TEST_LONGITUDE})",
        UnauthorizedError,
        {CONF_API_KEY: "invalid_api_key"},
    ),
    test.case(
        "name_airvisual_error",
        INTEGRATION_TYPE_GEOGRAPHY_NAME,
        "geography_by_name",
        "city",
        NAME_CONFIG,
        f"Cloud API ({TEST_CITY}, {TEST_STATE}, {TEST_COUNTRY})",
        AirVisualError,
        {"base": "unknown"},
    ),
    test.case(
        "name_invalid_key",
        INTEGRATION_TYPE_GEOGRAPHY_NAME,
        "geography_by_name",
        "city",
        NAME_CONFIG,
        f"Cloud API ({TEST_CITY}, {TEST_STATE}, {TEST_COUNTRY})",
        InvalidKeyError,
        {CONF_API_KEY: "invalid_api_key"},
    ),
    test.case(
        "name_key_expired",
        INTEGRATION_TYPE_GEOGRAPHY_NAME,
        "geography_by_name",
        "city",
        NAME_CONFIG,
        f"Cloud API ({TEST_CITY}, {TEST_STATE}, {TEST_COUNTRY})",
        KeyExpiredError,
        {CONF_API_KEY: "invalid_api_key"},
    ),
    test.case(
        "name_not_found",
        INTEGRATION_TYPE_GEOGRAPHY_NAME,
        "geography_by_name",
        "city",
        NAME_CONFIG,
        f"Cloud API ({TEST_CITY}, {TEST_STATE}, {TEST_COUNTRY})",
        NotFoundError,
        {CONF_CITY: "location_not_found"},
    ),
    test.case(
        "name_unauthorized",
        INTEGRATION_TYPE_GEOGRAPHY_NAME,
        "geography_by_name",
        "city",
        NAME_CONFIG,
        f"Cloud API ({TEST_CITY}, {TEST_STATE}, {TEST_COUNTRY})",
        UnauthorizedError,
        {CONF_API_KEY: "invalid_api_key"},
    ),
)
async def create_entry(
    integration_type: str,
    input_form_step: str,
    patched_method: str,
    config: dict[str, Any],
    entry_title: str,
    side_effect: type[Exception],
    errors: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    cloud_api: Mock = Depends(cloud_api),
    _mock_pyairvisual: None = Depends(mock_pyairvisual),
) -> None:
    """Test creating a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"type": integration_type}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal(input_form_step)

    response = AsyncMock(side_effect=side_effect)
    with patch.object(cloud_api.air_quality, patched_method, response):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal(errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(entry_title)
    expect(result["data"]).to_equal({**config, CONF_INTEGRATION_TYPE: integration_type})


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    config: dict[str, Any] = Depends(config),
    _setup_config_entry: None = Depends(setup_config_entry),
) -> None:
    """Test that errors are shown when duplicate entries are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={"type": INTEGRATION_TYPE_GEOGRAPHY_COORDS},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("geography_by_coords")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(config_entry),
    _setup_config_entry: None = Depends(setup_config_entry),
) -> None:
    """Test config flow options."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_SHOW_ON_MAP: False}
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(config_entry.options).to_equal({CONF_SHOW_ON_MAP: False})


@test
async def step_reauth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: None = Depends(mock_zeroconf),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(config_entry),
    _setup_config_entry: None = Depends(setup_config_entry),
) -> None:
    """Test that the reauth step works."""
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    new_api_key = "defgh67890"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: new_api_key}
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(len(hass.config_entries.async_entries())).to_equal(1)
    expect(hass.config_entries.async_entries()[0].data[CONF_API_KEY]).to_equal(
        new_api_key
    )
    await hass.async_block_till_done()
