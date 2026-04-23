"""Test the Plaato config flow."""

from __future__ import annotations

from collections.abc import Generator
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

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


BASE_URL = "http://example.com"
WEBHOOK_ID = "webhook_id"
UNIQUE_ID = "plaato_unique_id"


@fixture
def webhook_id() -> Generator[None]:
    """Mock webhook_id."""
    with (
        patch(
            "homeassistant.components.webhook.async_generate_id",
            return_value=WEBHOOK_ID,
        ),
        patch(
            "homeassistant.components.webhook.async_generate_url",
            return_value="hook_id",
        ),
    ):
        yield


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def show_config_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def show_config_form_device_type_airlock(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show configuration form."""
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
    expect(result["data_schema"].schema.get(CONF_TOKEN)).to_be(str)
    expect(result["data_schema"].schema.get(CONF_USE_WEBHOOK)).to_be(bool)


@test
async def show_config_form_device_type_keg(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_DEVICE_TYPE: PlaatoDeviceType.Keg, CONF_DEVICE_NAME: "device_name"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")
    expect(result["data_schema"].schema.get(CONF_TOKEN)).to_be(str)
    expect(result["data_schema"].schema.get(CONF_USE_WEBHOOK)).to_be(None)


@test
async def show_config_form_validate_webhook(
    hass: HomeAssistant = Depends(hass_fixture),
    _hook: None = Depends(webhook_id),
) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")

    expect(bool(await async_setup_component(hass, "cloud", {}))).to_be(True)
    with (
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch("homeassistant.components.cloud.async_is_logged_in", return_value=True),
        patch("homeassistant.components.cloud.async_is_connected", return_value=True),
        patch(
            "hass_nabucasa.cloudhooks.Cloudhooks.async_create",
            return_value={"cloudhook_url": "https://hooks.nabu.casa/ABCD"},
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_TOKEN: "",
                CONF_USE_WEBHOOK: True,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("webhook")


@test
async def show_config_form_validate_webhook_not_connected(
    hass: HomeAssistant = Depends(hass_fixture),
    _hook: None = Depends(webhook_id),
) -> None:
    """Test validating webhook when not connected aborts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("api_method")

    expect(bool(await async_setup_component(hass, "cloud", {}))).to_be(True)
    with (
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch("homeassistant.components.cloud.async_is_logged_in", return_value=True),
        patch("homeassistant.components.cloud.async_is_connected", return_value=False),
        patch(
            "hass_nabucasa.cloudhooks.Cloudhooks.async_create",
            return_value={"cloudhook_url": "https://hooks.nabu.casa/ABCD"},
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_TOKEN: "",
                CONF_USE_WEBHOOK: True,
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cloud_not_connected")


@test
async def show_config_form_validate_token(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show configuration form."""
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
    hass: HomeAssistant = Depends(hass_fixture),
    _hook: None = Depends(webhook_id),
) -> None:
    """Test show configuration form."""
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
    expect(result["errors"]).to_be(None)


@test
async def show_config_form_api_method_no_auth_token(
    hass: HomeAssistant = Depends(hass_fixture),
    _hook: None = Depends(webhook_id),
) -> None:
    """Test show configuration form."""
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
async def options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
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
    hass: HomeAssistant = Depends(hass_fixture),
    _hook: None = Depends(webhook_id),
) -> None:
    """Test updating options."""
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
