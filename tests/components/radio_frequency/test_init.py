"""Tests for the Radio Frequency integration setup."""

from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
from rf_protocols import ModulationType
from tryke import Depends, expect, fixture, test

from homeassistant.components.radio_frequency import (
    DATA_COMPONENT,
    DOMAIN,
    async_get_transmitters,
    async_send_command,
)
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import translation as translation_helper
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import ENTITY_ID
from ._fixtures import init_radio_frequency, mock_rf_entity
from .common import MockRadioFrequencyCommand, MockRadioFrequencyEntity

from tests.common import mock_restore_cache
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts test module into Tryke's HookExecutor path."""
    return 0


def _load_translations(hass: HomeAssistant) -> None:
    """Preload radio_frequency strings.json into the translation cache.

    The dev tree lacks ``translations/en.json``, so the real translation
    loader returns no exception messages. Read ``strings.json`` directly and
    seed the cache so ``str(HomeAssistantError(...))`` resolves to the
    human-readable message expected by ``expect_raises_async(..., match=...)``.
    """
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    strings_path = (
        Path(__file__).resolve().parents[3]
        / "homeassistant"
        / "components"
        / DOMAIN
        / "strings.json"
    )
    data: dict = json.loads(strings_path.read_text())
    cache = translation_helper._async_get_translations_cache(hass)
    translation_data = {"en": {DOMAIN: data}}
    cache._build_category_cache("en", {DOMAIN}, translation_data["en"])
    cache.cache_data.loaded.setdefault("en", set()).add(DOMAIN)


@test
async def get_transmitters_component_not_loaded(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting transmitters raises when the component is not loaded."""
    async with expect_raises_async(HomeAssistantError, match="component_not_loaded"):
        async_get_transmitters(hass, 433_920_000, ModulationType.OOK)


@test
async def get_transmitters_no_entities(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _rf: None = Depends(init_radio_frequency),
) -> None:
    """Test getting transmitters raises when none are registered."""
    _load_translations(hass)
    async with expect_raises_async(
        HomeAssistantError,
        match="No Radio Frequency transmitters available",
    ):
        async_get_transmitters(hass, 433_920_000, ModulationType.OOK)


@test
async def get_transmitters_with_frequency_ranges(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
) -> None:
    """Test transmitter with frequency ranges filters correctly."""
    # 433.92 MHz is within 433-434 MHz range
    result = async_get_transmitters(hass, 433_920_000, ModulationType.OOK)
    expect(result).to_equal([ENTITY_ID])

    # 868 MHz is outside the range
    result = async_get_transmitters(hass, 868_000_000, ModulationType.OOK)
    expect(result).to_equal([])


@test
async def get_transmitters_filters_by_modulation(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
) -> None:
    """Test transmitters are filtered by supported modulation."""
    result = async_get_transmitters(hass, 433_920_000, "no_matching_modulation")  # type: ignore[arg-type]
    expect(result).to_equal([])


@test
async def rf_entity_initial_state(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
) -> None:
    """Test radio frequency entity has no state before any command is sent."""
    state = hass.states.get(ENTITY_ID)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def async_send_command_success(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test sending command via async_send_command helper."""
    now = dt_util.utcnow()
    freezer.move_to(now)

    command = MockRadioFrequencyCommand(frequency=433_920_000)
    await async_send_command(hass, ENTITY_ID, command)

    expect(len(mock_rf_entity.send_command_calls)).to_equal(1)
    expect(mock_rf_entity.send_command_calls[0].command is command).to_be(True)

    state = hass.states.get(ENTITY_ID)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(now.isoformat(timespec="milliseconds"))


@test
async def async_send_command_error_does_not_update_state(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
) -> None:
    """Test that state is not updated when async_send_command raises an error."""
    state = hass.states.get(ENTITY_ID)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)

    command = MockRadioFrequencyCommand(frequency=433_920_000)

    mock_rf_entity.async_send_command = AsyncMock(
        side_effect=HomeAssistantError("Transmission failed")
    )

    async with expect_raises_async(HomeAssistantError, match="Transmission failed"):
        await async_send_command(hass, ENTITY_ID, command)

    state = hass.states.get(ENTITY_ID)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def async_send_command_entity_not_found(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _rf: None = Depends(init_radio_frequency),
) -> None:
    """Test async_send_command raises error when entity not found."""
    _load_translations(hass)
    command = MockRadioFrequencyCommand(frequency=433_920_000)

    async with expect_raises_async(
        HomeAssistantError,
        match="Radio Frequency entity `radio_frequency.nonexistent_entity` not found",
    ):
        await async_send_command(hass, "radio_frequency.nonexistent_entity", command)


@test
async def async_send_command_unsupported_frequency(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
) -> None:
    """Test async_send_command raises when the frequency is not supported."""
    _load_translations(hass)
    command = MockRadioFrequencyCommand(frequency=868_000_000)

    async with expect_raises_async(
        HomeAssistantError,
        match=(
            f"Radio Frequency entity `{ENTITY_ID}` "
            "does not support frequency 868000000 Hz"
        ),
    ):
        await async_send_command(hass, ENTITY_ID, command)

    expect(mock_rf_entity.send_command_calls).to_equal([])


@test
async def async_send_command_unsupported_modulation(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
) -> None:
    """Test async_send_command raises when the modulation is not supported."""
    _load_translations(hass)
    command = MockRadioFrequencyCommand(
        frequency=433_920_000,
        modulation="incorrect_modulation",  # type: ignore[arg-type]
    )

    async with expect_raises_async(
        HomeAssistantError,
        match=(
            f"Radio Frequency entity `{ENTITY_ID}` "
            "does not support modulation incorrect_modulation"
        ),
    ):
        await async_send_command(hass, ENTITY_ID, command)

    expect(mock_rf_entity.send_command_calls).to_equal([])


@test
async def async_send_command_component_not_loaded(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_send_command raises error when component not loaded."""
    command = MockRadioFrequencyCommand(frequency=433_920_000)

    async with expect_raises_async(HomeAssistantError, match="component_not_loaded"):
        await async_send_command(hass, "radio_frequency.some_entity", command)


@test.cases(
    test.case(
        "restored_iso",
        restored_value="2026-01-01T12:00:00.000+00:00",
        expected_state="2026-01-01T12:00:00.000+00:00",
    ),
    test.case(
        "restored_unavailable",
        restored_value=STATE_UNAVAILABLE,
        expected_state=STATE_UNKNOWN,
    ),
)
async def rf_entity_state_restore(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    restored_value: str,
    expected_state: str,
) -> None:
    """Test radio frequency entity state restore."""
    mock_restore_cache(hass, [State(ENTITY_ID, restored_value)])

    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    await hass.async_block_till_done()

    component = hass.data[DATA_COMPONENT]
    await component.async_add_entities(
        [MockRadioFrequencyEntity("test_rf_transmitter")]
    )

    state = hass.states.get(ENTITY_ID)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(expected_state)
