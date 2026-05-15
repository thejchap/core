"""Test MQTT utils."""

import asyncio
from datetime import timedelta
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import mqtt
from homeassistant.components.mqtt.util import EnsureJobAfterCooldown
from homeassistant.config_entries import ConfigEntryDisabler, ConfigEntryState
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.util.dt import utcnow

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def canceling_debouncer_normal(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cap: LogCapture = Depends(caplog),
) -> None:
    """Test canceling the debouncer before completion."""
    job_started = asyncio.Event()
    job_unblock = asyncio.Event()

    async def _async_myjob() -> None:
        job_started.set()
        await job_unblock.wait()

    debouncer = EnsureJobAfterCooldown(0.0, _async_myjob)
    debouncer.async_schedule()
    await asyncio.wait_for(job_started.wait(), timeout=1)
    expect(debouncer._task is not None).to_be(True)
    await debouncer.async_cleanup()
    expect(debouncer._task is None).to_be(True)


@test
async def canceling_debouncer_throws(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cap: LogCapture = Depends(caplog),
) -> None:
    """Test canceling the debouncer when HA shuts down."""
    job_started = asyncio.Event()
    job_unblock = asyncio.Event()

    async def _async_myjob() -> None:
        job_started.set()
        await job_unblock.wait()

    debouncer = EnsureJobAfterCooldown(0.0, _async_myjob)
    debouncer.async_schedule()
    await asyncio.wait_for(job_started.wait(), timeout=1)
    expect(debouncer._task is not None).to_be(True)
    # let debouncer._task fail by mocking it
    with patch.object(debouncer, "_task") as task:
        task.cancel = MagicMock(return_value=True)
        await debouncer.async_cleanup()
        expect("Error cleaning up task" in cap.text).to_be(True)
        await hass.async_block_till_done()
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=5))
        await hass.async_block_till_done()


@test
async def reading_non_existing_certificate_file(
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test reading a non existing certificate file."""
    expect(
        mqtt.util.migrate_certificate_file_to_content("/home/file_not_exists") is None
    ).to_be(True)


@test
async def waiting_for_client_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test waiting for client with timeout."""
    hass.set_state(CoreState.starting)
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=mqtt.DOMAIN,
        data={"broker": "test-broker"},
        state=ConfigEntryState.NOT_LOADED,
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    entry.add_to_hass(hass)

    expect(entry.state is ConfigEntryState.NOT_LOADED).to_be(True)
    # returns False after timeout
    with patch("homeassistant.components.mqtt.util.AVAILABILITY_TIMEOUT", 0.01):
        expect(await mqtt.async_wait_for_mqtt_client(hass)).to_be(False)


@test
async def waiting_for_client_with_disabled_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test waiting for client with disabled entry."""
    hass.set_state(CoreState.starting)
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=mqtt.DOMAIN,
        data={"broker": "test-broker"},
        state=ConfigEntryState.NOT_LOADED,
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    entry.add_to_hass(hass)

    # Disable MQTT config entry
    await hass.config_entries.async_set_disabled_by(
        entry.entry_id, ConfigEntryDisabler.USER
    )

    expect(entry.state is ConfigEntryState.NOT_LOADED).to_be(True)

    # returns False because entry is disabled
    expect(await mqtt.async_wait_for_mqtt_client(hass)).to_be(False)


@test.skip(
    "requires mqtt_client_mock + setup_with_birth_msg_client_mock fixture chain"
)
async def canceling_debouncer_on_shutdown() -> None:
    """Stub for test_canceling_debouncer_on_shutdown."""


@test.skip("requires mock_temp_dir + tempfile fixture chain")
async def async_create_certificate_temp_files() -> None:
    """Stub for test_async_create_certificate_temp_files."""


@test.skip("requires mock_temp_dir + tempfile fixture chain")
async def certificate_temp_files_with_auto_mode() -> None:
    """Stub for test_certificate_temp_files_with_auto_mode."""


@test.skip("requires mock_temp_dir fixture")
async def return_default_get_file_path() -> None:
    """Stub for test_return_default_get_file_path."""


@test.skip("requires mqtt_client_mock fixture (paho client mock)")
async def waiting_for_client_not_loaded() -> None:
    """Stub for test_waiting_for_client_not_loaded."""


@test.skip("requires mqtt_mock fixture (full mqtt client setup)")
async def waiting_for_client_loaded() -> None:
    """Stub for test_waiting_for_client_loaded."""


@test.skip("requires mqtt_client_mock fixture (paho client mock)")
async def waiting_for_client_entry_fails() -> None:
    """Stub for test_waiting_for_client_entry_fails."""


@test.skip("requires mqtt_client_mock fixture (paho client mock)")
async def waiting_for_client_setup_fails() -> None:
    """Stub for test_waiting_for_client_setup_fails."""
