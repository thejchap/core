"""Test select entity."""

from tryke import Depends, fixture, test

from homeassistant.components.assist_pipeline import DOMAIN, Pipeline
from homeassistant.components.assist_pipeline.pipeline import (
    AssistDevice,
    PipelineData,
    PipelineStorageCollection,
)
from homeassistant.components.assist_pipeline.select import (
    AssistPipelineSelect,
    VadSensitivitySelect,
)
from homeassistant.components.assist_pipeline.vad import VadSensitivity
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from ._fixtures import init_components

from tests.common import MockConfigEntry, MockPlatform, mock_platform
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
)


class SelectPlatform(MockPlatform):
    """Fake select platform."""

    async def async_setup_entry(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up fake select platform."""
        pipeline_entity = AssistPipelineSelect(hass, "test-domain", "test-prefix")
        pipeline_entity._attr_device_info = DeviceInfo(
            identifiers={("test", "test")},
        )
        sensitivity_entity = VadSensitivitySelect(hass, "test")
        sensitivity_entity._attr_device_info = DeviceInfo(
            identifiers={("test", "test")},
        )
        async_add_entities([pipeline_entity, sensitivity_entity])


@fixture
def pipeline_data(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_components),
) -> PipelineData:
    """Return pipeline data."""
    return hass.data[DOMAIN]


@fixture
def pipeline_storage(
    pipeline_data: PipelineData = Depends(pipeline_data),
) -> PipelineStorageCollection:
    """Return pipeline storage collection."""
    return pipeline_data.pipeline_store


@fixture
async def init_select(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_components),
) -> ConfigEntry:
    """Initialize select entity."""
    mock_platform(hass, "assist_pipeline.select", SelectPlatform())
    config_entry = MockConfigEntry(
        domain="assist_pipeline", state=ConfigEntryState.LOADED
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_forward_entry_setups(
        config_entry, [Platform.SELECT]
    )
    return config_entry


@fixture
async def pipeline_1(
    _init_select: ConfigEntry = Depends(init_select),
    pipeline_storage: PipelineStorageCollection = Depends(pipeline_storage),
) -> Pipeline:
    """Create a pipeline."""
    return await pipeline_storage.async_create_item(
        {
            "name": "Test 1",
            "language": "en-US",
            "conversation_engine": None,
            "conversation_language": "en-US",
            "tts_engine": None,
            "tts_language": None,
            "tts_voice": None,
            "stt_engine": None,
            "stt_language": None,
            "wake_word_entity": None,
            "wake_word_id": None,
        }
    )


@fixture
async def pipeline_2(
    _init_select: ConfigEntry = Depends(init_select),
    pipeline_storage: PipelineStorageCollection = Depends(pipeline_storage),
) -> Pipeline:
    """Create a pipeline."""
    return await pipeline_storage.async_create_item(
        {
            "name": "Test 2",
            "language": "en-US",
            "conversation_engine": None,
            "conversation_language": "en-US",
            "tts_engine": None,
            "tts_language": None,
            "tts_voice": None,
            "stt_engine": None,
            "stt_language": None,
            "wake_word_entity": None,
            "wake_word_id": None,
        }
    )


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_components),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves hass before the test body."""
    return hass


@test
async def select_entity_registering_device(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_select: ConfigEntry = Depends(init_select),
    pipeline_data: PipelineData = Depends(pipeline_data),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test entity registering as an assist device."""
    device = device_registry.async_get_device(identifiers={("test", "test")})
    assert device is not None

    # Test device is registered
    assert pipeline_data.pipeline_devices == {
        device.id: AssistDevice("test-domain", "test-prefix")
    }

    await hass.config_entries.async_remove(init_select.entry_id)
    await hass.async_block_till_done()

    # Test device is removed
    assert pipeline_data.pipeline_devices == {}


@test
async def select_entity_changing_pipelines(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_select: ConfigEntry = Depends(init_select),
    pipeline_1: Pipeline = Depends(pipeline_1),
    pipeline_2: Pipeline = Depends(pipeline_2),
    pipeline_storage: PipelineStorageCollection = Depends(pipeline_storage),
) -> None:
    """Test entity tracking pipeline changes."""
    config_entry = init_select  # nicer naming
    config_entry.mock_state(hass, ConfigEntryState.LOADED)

    state = hass.states.get("select.assist_pipeline_test_prefix_pipeline")
    assert state is not None
    assert state.state == "preferred"
    assert state.attributes["options"] == [
        "preferred",
        "Home Assistant",
        pipeline_1.name,
        pipeline_2.name,
    ]

    # Change select to new pipeline
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.assist_pipeline_test_prefix_pipeline",
            "option": pipeline_2.name,
        },
        blocking=True,
    )

    state = hass.states.get("select.assist_pipeline_test_prefix_pipeline")
    assert state is not None
    assert state.state == pipeline_2.name

    # Reload config entry to test selected option persists
    assert await hass.config_entries.async_forward_entry_unload(
        config_entry, Platform.SELECT
    )
    await hass.config_entries.async_forward_entry_setups(
        config_entry, [Platform.SELECT]
    )

    state = hass.states.get("select.assist_pipeline_test_prefix_pipeline")
    assert state is not None
    assert state.state == pipeline_2.name

    # Remove selected pipeline
    await pipeline_storage.async_delete_item(pipeline_2.id)

    state = hass.states.get("select.assist_pipeline_test_prefix_pipeline")
    assert state is not None
    assert state.state == "preferred"
    assert state.attributes["options"] == [
        "preferred",
        "Home Assistant",
        pipeline_1.name,
    ]


@test
async def select_entity_changing_vad_sensitivity(
    hass: HomeAssistant = Depends(_trigger_executor),
    init_select: ConfigEntry = Depends(init_select),
) -> None:
    """Test entity tracking vad sensitivity changes."""
    config_entry = init_select  # nicer naming
    config_entry.mock_state(hass, ConfigEntryState.LOADED)

    state = hass.states.get("select.assist_pipeline_test_vad_sensitivity")
    assert state is not None
    assert state.state == VadSensitivity.DEFAULT.value

    # Change select to new sensitivity
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.assist_pipeline_test_vad_sensitivity",
            "option": VadSensitivity.AGGRESSIVE.value,
        },
        blocking=True,
    )

    state = hass.states.get("select.assist_pipeline_test_vad_sensitivity")
    assert state is not None
    assert state.state == VadSensitivity.AGGRESSIVE.value

    # Reload config entry to test selected option persists
    assert await hass.config_entries.async_forward_entry_unload(
        config_entry, Platform.SELECT
    )
    await hass.config_entries.async_forward_entry_setups(
        config_entry, [Platform.SELECT]
    )

    state = hass.states.get("select.assist_pipeline_test_vad_sensitivity")
    assert state is not None
    assert state.state == VadSensitivity.AGGRESSIVE.value
