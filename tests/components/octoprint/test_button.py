"""Test the OctoPrint buttons."""

from unittest.mock import patch

from freezegun import freeze_time
from pyoctoprintapi import OctoprintPrinterInfo
from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.octoprint import OctoprintDataUpdateCoordinator
from homeassistant.components.octoprint.button import InvalidPrinterState
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration_button as init_integration_button_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def pause_job(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration_button_fixture),
) -> None:
    """Test the pause job button."""
    coordinator: OctoprintDataUpdateCoordinator = init_integration.runtime_data

    with patch("pyoctoprintapi.OctoprintClient.pause_job") as pause_command:
        coordinator.data["printer"] = OctoprintPrinterInfo(
            {"state": {"flags": {"printing": True}}, "temperature": []}
        )
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.octoprint_pause_job"},
            blocking=True,
        )

        expect(len(pause_command.mock_calls)).to_equal(1)

    with patch("pyoctoprintapi.OctoprintClient.pause_job") as pause_command:
        coordinator.data["printer"] = OctoprintPrinterInfo(
            {
                "state": {"flags": {"printing": False, "paused": True}},
                "temperature": [],
            }
        )
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.octoprint_pause_job"},
            blocking=True,
        )

        expect(len(pause_command.mock_calls)).to_equal(0)

    with patch("pyoctoprintapi.OctoprintClient.pause_job"):
        coordinator.data["printer"] = OctoprintPrinterInfo(
            {
                "state": {"flags": {"printing": False, "paused": False}},
                "temperature": [],
            }
        )
        async with expect_raises_async(InvalidPrinterState):
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: "button.octoprint_pause_job"},
                blocking=True,
            )


@test
async def resume_job(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration_button_fixture),
) -> None:
    """Test the resume job button."""
    coordinator: OctoprintDataUpdateCoordinator = init_integration.runtime_data

    with patch("pyoctoprintapi.OctoprintClient.resume_job") as resume_command:
        coordinator.data["printer"] = OctoprintPrinterInfo(
            {
                "state": {"flags": {"printing": False, "paused": True}},
                "temperature": [],
            }
        )
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.octoprint_resume_job"},
            blocking=True,
        )

        expect(len(resume_command.mock_calls)).to_equal(1)

    with patch("pyoctoprintapi.OctoprintClient.resume_job") as resume_command:
        coordinator.data["printer"] = OctoprintPrinterInfo(
            {
                "state": {"flags": {"printing": True, "paused": False}},
                "temperature": [],
            }
        )
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.octoprint_resume_job"},
            blocking=True,
        )

        expect(len(resume_command.mock_calls)).to_equal(0)

    with patch("pyoctoprintapi.OctoprintClient.resume_job"):
        coordinator.data["printer"] = OctoprintPrinterInfo(
            {
                "state": {"flags": {"printing": False, "paused": False}},
                "temperature": [],
            }
        )
        async with expect_raises_async(InvalidPrinterState):
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: "button.octoprint_resume_job"},
                blocking=True,
            )


@test
async def stop_job(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration_button_fixture),
) -> None:
    """Test the stop job button."""
    coordinator: OctoprintDataUpdateCoordinator = init_integration.runtime_data

    with patch("pyoctoprintapi.OctoprintClient.cancel_job") as stop_command:
        coordinator.data["printer"] = OctoprintPrinterInfo(
            {
                "state": {"flags": {"printing": False, "paused": True}},
                "temperature": [],
            }
        )
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.octoprint_stop_job"},
            blocking=True,
        )

        expect(len(stop_command.mock_calls)).to_equal(1)

    with patch("pyoctoprintapi.OctoprintClient.cancel_job") as stop_command:
        coordinator.data["printer"] = OctoprintPrinterInfo(
            {
                "state": {"flags": {"printing": True, "paused": False}},
                "temperature": [],
            }
        )
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.octoprint_stop_job"},
            blocking=True,
        )

        expect(len(stop_command.mock_calls)).to_equal(1)

    with patch("pyoctoprintapi.OctoprintClient.cancel_job") as stop_command:
        coordinator.data["printer"] = OctoprintPrinterInfo(
            {
                "state": {"flags": {"printing": False, "paused": False}},
                "temperature": [],
            }
        )
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.octoprint_stop_job"},
            blocking=True,
        )

        expect(len(stop_command.mock_calls)).to_equal(0)


@test
async def shutdown_system(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration_button_fixture),
) -> None:
    """Test the shutdown system button."""
    entity_id = "button.octoprint_shutdown_system"

    with freeze_time("2023-01-01 00:00"):
        with patch(
            "homeassistant.components.octoprint.coordinator.OctoprintClient.shutdown"
        ) as shutdown_command:
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )

            expect(len(shutdown_command.mock_calls)).to_equal(1)

            state = hass.states.get(entity_id)
            expect(state).not_.to_be(None)
            assert state is not None
            expect(state.state).to_equal("2023-01-01T00:00:00+00:00")


@test
async def reboot_system(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration_button_fixture),
) -> None:
    """Test the reboot system button."""
    entity_id = "button.octoprint_reboot_system"

    with freeze_time("2023-01-01 00:00"):
        with patch(
            "homeassistant.components.octoprint.coordinator.OctoprintClient.reboot_system"
        ) as reboot_command:
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )

            expect(len(reboot_command.mock_calls)).to_equal(1)

            state = hass.states.get(entity_id)
            expect(state).not_.to_be(None)
            assert state is not None
            expect(state.state).to_equal("2023-01-01T00:00:00+00:00")


@test
async def restart_octoprint(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration_button_fixture),
) -> None:
    """Test the restart octoprint button."""
    entity_id = "button.octoprint_restart_octoprint"

    with freeze_time("2023-01-01 00:00"):
        with patch(
            "homeassistant.components.octoprint.coordinator.OctoprintClient.restart"
        ) as restart_command:
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )

            expect(len(restart_command.mock_calls)).to_equal(1)

            state = hass.states.get(entity_id)
            expect(state).not_.to_be(None)
            assert state is not None
            expect(state.state).to_equal("2023-01-01T00:00:00+00:00")
