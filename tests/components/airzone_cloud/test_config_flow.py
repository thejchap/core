"""Define tests for the Airzone Cloud config flow."""

from unittest.mock import patch

from aioairzone_cloud.exceptions import AirzoneCloudError, LoginError
from tryke import Depends, expect, fixture, test

from homeassistant.components.airzone_cloud.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_ID, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import airzone_cloud_no_websockets
from .util import (
    CONFIG,
    GET_INSTALLATION_MOCK,
    GET_INSTALLATIONS_MOCK,
    WS_ID,
    mock_get_device_config,
    mock_get_device_status,
    mock_get_webserver,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _no_ws: None = Depends(airzone_cloud_no_websockets),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the form is served with valid input."""

    with (
        patch(
            "homeassistant.components.airzone_cloud.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_get_device_config",
            side_effect=mock_get_device_config,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_get_device_status",
            side_effect=mock_get_device_status,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_get_installation",
            return_value=GET_INSTALLATION_MOCK,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_get_installations",
            return_value=GET_INSTALLATIONS_MOCK,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_get_webserver",
            side_effect=mock_get_webserver,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.login",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: CONFIG[CONF_USERNAME],
                CONF_PASSWORD: CONFIG[CONF_PASSWORD],
            },
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID: CONFIG[CONF_ID],
            },
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        expect(entry.state).to_be(ConfigEntryState.LOADED)

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(f"House {WS_ID} ({CONFIG[CONF_ID]})")
        expect(result["data"][CONF_ID]).to_equal(CONFIG[CONF_ID])
        expect(result["data"][CONF_USERNAME]).to_equal(CONFIG[CONF_USERNAME])
        expect(result["data"][CONF_PASSWORD]).to_equal(CONFIG[CONF_PASSWORD])

        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def installations_list_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connection error."""

    with (
        patch(
            "homeassistant.components.airzone_cloud.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_get_device_config",
            side_effect=mock_get_device_config,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_get_device_status",
            side_effect=mock_get_device_status,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_get_installations",
            side_effect=AirzoneCloudError,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_get_webserver",
            side_effect=mock_get_webserver,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.login",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: CONFIG[CONF_USERNAME],
                CONF_PASSWORD: CONFIG[CONF_PASSWORD],
            },
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def login_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test login error."""

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.login",
        side_effect=LoginError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_USERNAME: CONFIG[CONF_USERNAME],
                CONF_PASSWORD: CONFIG[CONF_PASSWORD],
            },
        )

        expect(result["errors"]).to_equal({"base": "cannot_connect"})
