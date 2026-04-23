"""Test the Foscam config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.foscam import config_flow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.foscam.conftest import setup_mock_foscam_camera
from tests.components.foscam.const import (
    CAMERA_NAME,
    INVALID_RESPONSE_CONFIG,
    VALID_CONFIG,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user_valid(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test valid config from user input."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.foscam.config_flow.FoscamCamera",
        ) as mock_foscam_camera,
        patch(
            "homeassistant.components.foscam.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        setup_mock_foscam_camera(mock_foscam_camera)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(CAMERA_NAME)
        expect(result["data"]).to_equal(VALID_CONFIG)
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth from user input."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.foscam.config_flow.FoscamCamera",
    ) as mock_foscam_camera:
        setup_mock_foscam_camera(mock_foscam_camera)

        invalid_user = VALID_CONFIG.copy()
        invalid_user[config_flow.CONF_USERNAME] = "invalid"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            invalid_user,
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def user_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error from user input."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.foscam.config_flow.FoscamCamera",
    ) as mock_foscam_camera:
        setup_mock_foscam_camera(mock_foscam_camera)

        invalid_host = VALID_CONFIG.copy()
        invalid_host[config_flow.CONF_HOST] = "127.0.0.1"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            invalid_host,
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_invalid_response(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid response error from user input."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.foscam.config_flow.FoscamCamera",
    ) as mock_foscam_camera:
        setup_mock_foscam_camera(mock_foscam_camera)

        invalid_response = VALID_CONFIG.copy()
        invalid_response[config_flow.CONF_USERNAME] = INVALID_RESPONSE_CONFIG[
            config_flow.CONF_USERNAME
        ]

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            invalid_response,
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "invalid_response"})


@test
async def user_already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle already configured from user input."""
    entry = MockConfigEntry(
        domain=config_flow.DOMAIN,
        data=VALID_CONFIG,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.foscam.config_flow.FoscamCamera",
    ) as mock_foscam_camera:
        setup_mock_foscam_camera(mock_foscam_camera)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def user_unknown_exception(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unknown exceptions from user input."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.foscam.config_flow.FoscamCamera",
    ) as mock_foscam_camera:
        mock_foscam_camera.side_effect = Exception("test")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "unknown"})
