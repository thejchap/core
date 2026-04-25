"""Test the Trafikverket Camera config flow."""

from __future__ import annotations

from unittest.mock import patch

from pytrafikverket import (
    CameraInfoModel,
    InvalidAuthentication,
    NoCameraFound,
    UnknownError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.trafikverket_camera.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_ID, CONF_LOCATION
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    get_camera,
    get_camera2,
    get_camera_no_location,
    get_cameras,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    camera: CameraInfoModel = Depends(get_camera),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
            return_value=[camera],
        ),
        patch(
            "homeassistant.components.trafikverket_camera.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_LOCATION: "Test loc",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Test Camera")
    expect(result2["data"]).to_equal(
        {
            "api_key": "1234567890",
            "id": "1234",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(result2["result"].unique_id).to_equal("trafikverket_camera-1234")


@test
async def form_multiple_cameras(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cameras: list[CameraInfoModel] = Depends(get_cameras),
    camera2: CameraInfoModel = Depends(get_camera2),
) -> None:
    """Test we get the form with multiple cameras."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
        return_value=cameras,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_LOCATION: "Test loc",
            },
        )
        await hass.async_block_till_done()

    with (
        patch(
            "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
            return_value=[camera2],
        ),
        patch(
            "homeassistant.components.trafikverket_camera.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID: "5678",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Camera2")
    expect(result["data"]).to_equal(
        {
            "api_key": "1234567890",
            "id": "5678",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(result["result"].unique_id).to_equal("trafikverket_camera-5678")


@test
async def form_no_location_data(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    camera_no_location: CameraInfoModel = Depends(get_camera_no_location),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
            return_value=[camera_no_location],
        ),
        patch(
            "homeassistant.components.trafikverket_camera.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_LOCATION: "Test Cam",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Test Camera")
    expect(result2["data"]).to_equal(
        {
            "api_key": "1234567890",
            "id": "1234",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(result2["result"].unique_id).to_equal("trafikverket_camera-1234")


@test.cases(
    test.case(
        "invalid_auth",
        side_effect=InvalidAuthentication,
        error_key="base",
        base_error="invalid_auth",
    ),
    test.case(
        "no_camera_found",
        side_effect=NoCameraFound,
        error_key="location",
        base_error="invalid_location",
    ),
    test.case(
        "unknown",
        side_effect=UnknownError,
        error_key="base",
        base_error="cannot_connect",
    ),
)
async def flow_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    error_key: str,
    base_error: str,
) -> None:
    """Test config flow errors."""
    result4 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result4["type"]).to_be(FlowResultType.FORM)
    expect(result4["step_id"]).to_equal(config_entries.SOURCE_USER)

    with patch(
        "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
        side_effect=side_effect,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result4["flow_id"],
            user_input={
                CONF_API_KEY: "1234567890",
                CONF_LOCATION: "incorrect",
            },
        )

    expect(result4["errors"]).to_equal({error_key: base_error})


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_ID: "1234",
        },
        unique_id="1234",
        version=3,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
        ),
        patch(
            "homeassistant.components.trafikverket_camera.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            "api_key": "1234567891",
            "id": "1234",
        }
    )


@test.cases(
    test.case(
        "invalid_auth",
        side_effect=InvalidAuthentication,
        error_key="base",
        p_error="invalid_auth",
    ),
    test.case(
        "no_camera_found",
        side_effect=NoCameraFound,
        error_key="location",
        p_error="invalid_location",
    ),
    test.case(
        "unknown",
        side_effect=UnknownError,
        error_key="base",
        p_error="cannot_connect",
    ),
)
async def reauth_flow_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    error_key: str,
    p_error: str,
) -> None:
    """Test a reauthentication flow with error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_ID: "1234",
        },
        unique_id="1234",
        version=3,
    )
    entry.add_to_hass(hass)
    await hass.async_block_till_done()

    result = await entry.start_reauth_flow(hass)

    with patch(
        "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
        side_effect=side_effect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567890"},
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({error_key: p_error})

    with (
        patch(
            "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
        ),
        patch(
            "homeassistant.components.trafikverket_camera.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(
        {
            "api_key": "1234567891",
            "id": "1234",
        }
    )


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cameras: list[CameraInfoModel] = Depends(get_cameras),
    camera2: CameraInfoModel = Depends(get_camera2),
) -> None:
    """Test a reconfigure flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_ID: "1234",
        },
        unique_id="1234",
        version=3,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
        return_value=cameras,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_LOCATION: "Test loc",
            },
        )
        await hass.async_block_till_done()

    with (
        patch(
            "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
            return_value=[camera2],
        ),
        patch(
            "homeassistant.components.trafikverket_camera.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID: "5678",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            "api_key": "1234567890",
            "id": "5678",
        }
    )


@test.cases(
    test.case(
        "invalid_auth",
        side_effect=InvalidAuthentication,
        error_key="base",
        p_error="invalid_auth",
    ),
    test.case(
        "no_camera_found",
        side_effect=NoCameraFound,
        error_key="location",
        p_error="invalid_location",
    ),
    test.case(
        "unknown",
        side_effect=UnknownError,
        error_key="base",
        p_error="cannot_connect",
    ),
)
async def reconfigure_flow_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    camera: CameraInfoModel = Depends(get_camera),
    *,
    side_effect: type[Exception],
    error_key: str,
    p_error: str,
) -> None:
    """Test a reauthentication flow with error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_ID: "1234",
        },
        unique_id="1234",
        version=3,
    )
    entry.add_to_hass(hass)
    await hass.async_block_till_done()

    result = await entry.start_reconfigure_flow(hass)

    with patch(
        "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
        side_effect=side_effect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_LOCATION: "Test loc",
            },
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reconfigure")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({error_key: p_error})

    with (
        patch(
            "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
            return_value=[camera],
        ),
        patch(
            "homeassistant.components.trafikverket_camera.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567891",
                CONF_LOCATION: "Test loc",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal(
        {
            CONF_ID: "1234",
            CONF_API_KEY: "1234567891",
        }
    )
