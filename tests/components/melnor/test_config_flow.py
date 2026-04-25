"""Test the melnor config flow."""

from unittest.mock import AsyncMock

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.melnor.const import DOMAIN
from homeassistant.config_entries import SOURCE_IGNORE
from homeassistant.const import CONF_ADDRESS, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    FAKE_ADDRESS_1,
    FAKE_SERVICE_INFO_1,
    FAKE_SERVICE_INFO_2,
    mock_setup_entry,
    patch_async_discovered_service_info,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bt: None = Depends(enable_bluetooth),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user_step_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle no devices found."""
    with patch_async_discovered_service_info([]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("no_devices_found")

        setup_entry.assert_not_called()


@test
async def user_step_discovered_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we properly handle device picking."""
    with patch_async_discovered_service_info([FAKE_SERVICE_INFO_1]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("pick_device")

        raised = False
        try:
            await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={CONF_ADDRESS: "wrong_address"}
            )
        except vol.Invalid:
            raised = True
        expect(raised).to_be(True)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: FAKE_ADDRESS_1}
        )

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["data"]).to_equal({CONF_ADDRESS: FAKE_ADDRESS_1})

    setup_entry.assert_called_once()


@test
async def user_step_with_existing_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we properly handle device picking."""
    with patch_async_discovered_service_info(
        [FAKE_SERVICE_INFO_1, FAKE_SERVICE_INFO_2]
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_BLUETOOTH,
                "step_id": "bluetooth_confirm",
                "user_input": {CONF_MAC: FAKE_ADDRESS_1},
            },
            data=FAKE_SERVICE_INFO_1,
        )

        await hass.config_entries.flow.async_configure(result["flow_id"], user_input={})

        setup_entry.reset_mock()

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        expect(result["type"]).to_be(FlowResultType.FORM)

        raised = False
        try:
            await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={CONF_ADDRESS: FAKE_ADDRESS_1}
            )
        except vol.Invalid:
            raised = True
        expect(raised).to_be(True)

        setup_entry.assert_not_called()


@test
async def bluetooth_discovered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we short circuit to config entry creation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=FAKE_SERVICE_INFO_1,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    expect(result["description_placeholders"]).to_equal({"name": FAKE_ADDRESS_1})

    setup_entry.assert_not_called()


@test
async def bluetooth_confirm(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we short circuit to config entry creation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_BLUETOOTH,
            "step_id": "bluetooth_confirm",
            "user_input": {CONF_MAC: FAKE_ADDRESS_1},
        },
        data=FAKE_SERVICE_INFO_1,
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(FAKE_ADDRESS_1)
    expect(result2["data"]).to_equal({CONF_ADDRESS: FAKE_ADDRESS_1})

    setup_entry.assert_called_once()


@test
async def user_setup_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FAKE_ADDRESS_1,
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch_async_discovered_service_info([FAKE_SERVICE_INFO_1]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pick_device")

    expect(FAKE_ADDRESS_1 in result["data_schema"].schema[CONF_ADDRESS].container).to_be(
        True
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ADDRESS: FAKE_ADDRESS_1}
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(FAKE_ADDRESS_1)
    expect(result2["data"]).to_equal({CONF_ADDRESS: FAKE_ADDRESS_1})
    expect(result2["result"].unique_id).to_equal(FAKE_ADDRESS_1)

    setup_entry.assert_called_once()
