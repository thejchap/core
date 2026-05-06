"""Test the Snooz config flow."""

from __future__ import annotations

from asyncio import Event, sleep
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.snooz.const import DOMAIN
from homeassistant.config_entries import SOURCE_IGNORE
from homeassistant.const import CONF_ADDRESS, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    NOT_SNOOZ_SERVICE_INFO,
    SNOOZ_SERVICE_INFO_NOT_PAIRING,
    SNOOZ_SERVICE_INFO_PAIRING,
    TEST_ADDRESS,
    TEST_PAIRING_TOKEN,
    TEST_SNOOZ_DISPLAY_NAME,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _test_pairs(
    hass: HomeAssistant, flow_id: str, user_input: dict | None = None
) -> None:
    pairing_mode_entered = Event()

    async def _async_process_advertisements(
        _hass, _callback, _matcher, _mode, _timeout
    ):
        await pairing_mode_entered.wait()
        service_info = SNOOZ_SERVICE_INFO_PAIRING
        expect(bool(_callback(service_info))).to_be(True)
        return service_info

    with patch(
        "homeassistant.components.snooz.config_flow.async_process_advertisements",
        _async_process_advertisements,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_input or {},
        )
        expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
        expect(result["step_id"]).to_equal("wait_for_pairing_mode")

        pairing_mode_entered.set()
        await hass.async_block_till_done()

    await _test_setup_entry(hass, result["flow_id"], user_input)


async def _test_pairs_timeout(
    hass: HomeAssistant, flow_id: str, user_input: dict | None = None
) -> str:
    async def _async_process_advertisements(
        _hass, _callback, _matcher, _mode, _timeout
    ):
        """Simulate a timeout waiting for pairing mode."""
        await sleep(0)
        raise TimeoutError

    with patch(
        "homeassistant.components.snooz.config_flow.async_process_advertisements",
        _async_process_advertisements,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id, user_input=user_input or {}
        )
        expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
        expect(result["step_id"]).to_equal("wait_for_pairing_mode")
        await hass.async_block_till_done()

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("pairing_timeout")

    return result2["flow_id"]


async def _test_setup_entry(
    hass: HomeAssistant, flow_id: str, user_input: dict | None = None
) -> None:
    with patch("homeassistant.components.snooz.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_input or {},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: TEST_ADDRESS,
            CONF_TOKEN: TEST_PAIRING_TOKEN,
        }
    )
    expect(result["result"].unique_id).to_equal(TEST_ADDRESS)


@test
async def async_step_bluetooth_valid_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SNOOZ_SERVICE_INFO_PAIRING,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")
    await _test_setup_entry(hass, result["flow_id"])


@test
async def async_step_bluetooth_waits_to_pair(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a device that's not in pairing mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SNOOZ_SERVICE_INFO_NOT_PAIRING,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    await _test_pairs(hass, result["flow_id"])


@test
async def async_step_bluetooth_retries_pairing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth with a device that's not in pairing mode, times out, then completes."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SNOOZ_SERVICE_INFO_NOT_PAIRING,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    retry_id = await _test_pairs_timeout(hass, result["flow_id"])
    await _test_pairs(hass, retry_id)


@test
async def async_step_bluetooth_not_snooz(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery via bluetooth not Snooz."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=NOT_SNOOZ_SERVICE_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_supported")


@test
async def async_step_user_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with no devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def async_step_user_with_found_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found."""
    with patch(
        "homeassistant.components.snooz.config_flow.async_discovered_service_info",
        return_value=[SNOOZ_SERVICE_INFO_PAIRING],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["data_schema"])).to_be(True)
    expect(result["data_schema"].schema["name"].container).to_equal(
        [TEST_SNOOZ_DISPLAY_NAME]
    )
    await _test_setup_entry(
        hass, result["flow_id"], {CONF_NAME: TEST_SNOOZ_DISPLAY_NAME}
    )


@test
async def async_step_user_with_found_devices_waits_to_pair(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found that require pairing mode."""
    with patch(
        "homeassistant.components.snooz.config_flow.async_discovered_service_info",
        return_value=[SNOOZ_SERVICE_INFO_NOT_PAIRING],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    await _test_pairs(hass, result["flow_id"], {CONF_NAME: TEST_SNOOZ_DISPLAY_NAME})


@test
async def async_step_user_with_found_devices_retries_pairing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test pairing retry."""
    with patch(
        "homeassistant.components.snooz.config_flow.async_discovered_service_info",
        return_value=[SNOOZ_SERVICE_INFO_NOT_PAIRING],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    user_input = {CONF_NAME: TEST_SNOOZ_DISPLAY_NAME}

    retry_id = await _test_pairs_timeout(hass, result["flow_id"], user_input)
    await _test_pairs(hass, retry_id, user_input)


@test
async def async_step_user_device_added_between_steps(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the device gets added via another flow between steps."""
    with patch(
        "homeassistant.components.snooz.config_flow.async_discovered_service_info",
        return_value=[SNOOZ_SERVICE_INFO_PAIRING],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_ADDRESS,
        data={CONF_NAME: TEST_SNOOZ_DISPLAY_NAME, CONF_TOKEN: TEST_PAIRING_TOKEN},
    )
    entry.add_to_hass(hass)

    with patch("homeassistant.components.snooz.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_NAME: TEST_SNOOZ_DISPLAY_NAME},
        )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def async_step_user_with_found_devices_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache with devices found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_ADDRESS,
        data={CONF_NAME: TEST_SNOOZ_DISPLAY_NAME, CONF_TOKEN: TEST_PAIRING_TOKEN},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.snooz.config_flow.async_discovered_service_info",
        return_value=[SNOOZ_SERVICE_INFO_PAIRING],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def async_step_bluetooth_devices_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow if there is already a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_ADDRESS,
        data={CONF_NAME: TEST_SNOOZ_DISPLAY_NAME, CONF_TOKEN: TEST_PAIRING_TOKEN},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SNOOZ_SERVICE_INFO_PAIRING,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def async_step_bluetooth_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow for the same device twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SNOOZ_SERVICE_INFO_PAIRING,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SNOOZ_SERVICE_INFO_PAIRING,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def async_step_user_takes_precedence_over_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SNOOZ_SERVICE_INFO_PAIRING,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("bluetooth_confirm")

    with patch(
        "homeassistant.components.snooz.config_flow.async_discovered_service_info",
        return_value=[SNOOZ_SERVICE_INFO_PAIRING],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

    await _test_setup_entry(
        hass, result["flow_id"], {CONF_NAME: TEST_SNOOZ_DISPLAY_NAME}
    )

    expect(bool(hass.config_entries.flow.async_progress())).to_be(False)


@test
async def user_setup_replaces_ignored_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_ADDRESS,
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.snooz.config_flow.async_discovered_service_info",
        return_value=[SNOOZ_SERVICE_INFO_PAIRING],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    expect(result["data_schema"].schema["name"].container).to_equal(
        [TEST_SNOOZ_DISPLAY_NAME]
    )

    await _test_setup_entry(
        hass, result["flow_id"], {CONF_NAME: TEST_SNOOZ_DISPLAY_NAME}
    )
