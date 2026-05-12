"""Tryke fixtures for OctoPrint tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

from pyoctoprintapi import (
    DiscoverySettings,
    OctoprintJobInfo,
    OctoprintPrinterInfo,
    TrackingSetting,
    WebcamSettings,
)
from tryke import Depends, fixture

from homeassistant.components.octoprint import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import DEFAULT_JOB, DEFAULT_PRINTER

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


async def setup_octoprint_integration(
    hass: HomeAssistant,
    platform: Platform,
    printer: dict[str, Any] | None = None,
    job: dict[str, Any] | None = None,
    webcam: dict[str, Any] | None = None,
) -> AsyncGenerator[MockConfigEntry]:
    """Set up the OctoPrint integration in HA for tryke tests."""
    if printer is None:
        printer = DEFAULT_PRINTER
    if job is None:
        job = DEFAULT_JOB
    printer_info: OctoprintPrinterInfo | None = None
    if printer is not None:
        printer_info = OctoprintPrinterInfo(printer)
    webcam_info: WebcamSettings | None = None
    if webcam is not None:
        webcam_info = WebcamSettings(**webcam)
    with (
        patch("homeassistant.components.octoprint.PLATFORMS", [platform]),
        patch("pyoctoprintapi.OctoprintClient.get_server_info", return_value={}),
        patch(
            "pyoctoprintapi.OctoprintClient.get_printer_info",
            return_value=printer_info,
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_job_info",
            return_value=OctoprintJobInfo(job),
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_tracking_info",
            return_value=TrackingSetting({"unique_id": "uuid"}),
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_discovery_info",
            return_value=DiscoverySettings({"upnpUuid": "uuid"}),
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_webcam_info",
            return_value=webcam_info,
        ),
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={
                "host": "1.1.1.1",
                "api_key": "test-key",
                "name": "OctoPrint",
                "port": 81,
                "ssl": True,
                "path": "/",
            },
            title="OctoPrint",
        )
        config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.state is ConfigEntryState.LOADED
        yield config_entry


@fixture
async def init_integration_button(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[MockConfigEntry]:
    """Set up OctoPrint with the button platform for tryke."""
    async for entry in setup_octoprint_integration(hass, Platform.BUTTON):
        yield entry


STANDARD_JOB = {
    "job": {
        "averagePrintTime": 6500,
        "estimatedPrintTime": 6000,
        "filament": {"tool0": {"length": 3000, "volume": 7}},
        "file": {
            "date": 1577836800,
            "display": "Test File Name",
            "name": "Test_File_Name.gcode",
            "origin": "local",
            "path": "Folder1/Folder2/Test_File_Name.gcode",
            "size": 123456789,
        },
        "lastPrintTime": 12345.678,
        "user": "testUser",
    },
    "progress": {"completion": 50, "printTime": 600, "printTimeLeft": 6000},
    "state": "Printing",
}
