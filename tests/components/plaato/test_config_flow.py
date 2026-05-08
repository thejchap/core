"""Test the Plaato config flow."""

from unittest.mock import patch

from pyplaato.models.device import PlaatoDeviceType
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.plaato.const import (
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    CONF_USE_WEBHOOK,
    DOMAIN,
)
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_TOKEN, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from ._fixtures import webhook_id

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

WEBHOOK_ID = "webhook_id"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor to force tryke fixture resolution."""


@test
async def show_config_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def show_config_form_device_type_airlock(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show configuration form for Airlock."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")
    expect(result["data_schema"].schema.get(CONF_TOKEN) is str).to_be(True)
    expect(result["data_schema"].schema.get(CONF_USE_WEBHOOK) is bool).to_be(True)


@test
async def show_config_form_device_type_keg(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show configuration form for Keg."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_DEVICE_TYPE: PlaatoDeviceType.Keg, CONF_DEVICE_NAME: "device_name"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")
    expect(result["data_schema"].schema.get(CONF_TOKEN) is str).to_be(True)
    expect(result["data_schema"].schema.get(CONF_USE_WEBHOOK) is None).to_be(True)


@test.skip("requires cloud component setup which pulls supervisor / nabucasa chain")
async def show_config_form_validate_webhook(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _webhook_id: None = Depends(webhook_id),
) -> None:
    """Test webhook validation flow."""


@test.skip("requires cloud component setup which pulls supervisor / nabucasa chain")
async def show_config_form_validate_webhook_not_connected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _webhook_id: None = Depends(webhook_id),
) -> None:
    """Test webhook validation aborts when cloud not connected."""


@test
async def show_config_form_validate_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test token-based config flow completes successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Keg,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")

    with patch("homeassistant.components.plaato.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_TOKEN: "valid_token"}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(PlaatoDeviceType.Keg.name)
    expect(result["data"]).to_equal(
        {
            CONF_USE_WEBHOOK: False,
            CONF_TOKEN: "valid_token",
            CONF_DEVICE_TYPE: PlaatoDeviceType.Keg,
            CONF_DEVICE_NAME: "device_name",
        }
    )


@test
async def show_config_form_no_cloud_webhook(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _webhook_id: None = Depends(webhook_id),
) -> None:
    """Test webhook step when cloud is not active."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USE_WEBHOOK: True,
            CONF_TOKEN: "",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("webhook")
    expect(result["errors"] is None).to_be(True)


@test
async def show_config_form_api_method_no_auth_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _webhook_id: None = Depends(webhook_id),
) -> None:
    """Test api_method step error when no auth token / webhook supplied."""
    # Using Keg
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Keg,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOKEN: ""}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")
    expect(len(result["errors"])).to_equal(1)
    expect(result["errors"]["base"]).to_equal("no_auth_token")

    # Using Airlock
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOKEN: ""}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")
    expect(len(result["errors"])).to_equal(1)
    expect(result["errors"]["base"]).to_equal("no_api_method")


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="NAME",
        data={},
        options={CONF_SCAN_INTERVAL: 5},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.plaato.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_SCAN_INTERVAL: 10},
        )

        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"][CONF_SCAN_INTERVAL]).to_equal(10)
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def options_webhook(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _webhook_id: None = Depends(webhook_id),
) -> None:
    """Test updating options for a webhook entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="NAME",
        data={CONF_USE_WEBHOOK: True, CONF_WEBHOOK_ID: None},
        options={CONF_SCAN_INTERVAL: 5},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.plaato.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("webhook")
        expect(result["description_placeholders"]).to_equal({"webhook_url": ""})

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_WEBHOOK_ID: WEBHOOK_ID},
        )

        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"][CONF_WEBHOOK_ID]).to_equal(CONF_WEBHOOK_ID)
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)
