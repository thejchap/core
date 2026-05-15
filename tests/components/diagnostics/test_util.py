"""Test Diagnostics utils."""

from datetime import datetime

from tryke import expect, test

from homeassistant.components.diagnostics import (
    REDACTED,
    async_redact_data,
    entity_entry_as_dict,
)
from homeassistant.helpers.entity_registry import RegistryEntry


@test
def redact() -> None:
    """Test the async_redact_data helper."""
    data = {
        "key1": "value1",
        "key2": ["value2_a", "value2_b"],
        "key3": [["value_3a", "value_3b"], ["value_3c", "value_3d"]],
        "key4": {
            "key4_1": "value4_1",
            "key4_2": ["value4_2a", "value4_2b"],
            "key4_3": [["value4_3a", "value4_3b"], ["value4_3c", "value4_3d"]],
        },
        "key5": None,
        "key6": "",
        "key7": False,
    }

    to_redact = {"key1", "key3", "key4_1", "key5", "key6", "key7"}

    expect(async_redact_data(data, to_redact)).to_equal(
        {
            "key1": REDACTED,
            "key2": ["value2_a", "value2_b"],
            "key3": REDACTED,
            "key4": {
                "key4_1": REDACTED,
                "key4_2": ["value4_2a", "value4_2b"],
                "key4_3": [["value4_3a", "value4_3b"], ["value4_3c", "value4_3d"]],
            },
            "key5": None,
            "key6": "",
            "key7": REDACTED,
        }
    )


@test
def entity_entry_as_dict_strips_cache() -> None:
    """Test entity_entry_as_dict."""
    created = datetime.fromisoformat("2024-01-01T00:00:00+00:00")
    entry = RegistryEntry(
        entity_id="sensor.test_sensor",
        unique_id="unique123",
        platform="test",
        capabilities=None,
        config_entry_id=None,
        config_subentry_id=None,
        created_at=created,
        device_id=None,
        disabled_by=None,
        entity_category=None,
        has_entity_name=False,
        hidden_by=None,
        id=None,
        options=None,
        original_device_class=None,
        original_icon=None,
        original_name="Test Sensor",
        object_id_base=None,
        suggested_object_id=None,
        supported_features=0,
        translation_key=None,
        unit_of_measurement=None,
    )

    result = entity_entry_as_dict(entry)

    expect(isinstance(result, dict)).to_be(True)
    expect("_cache" not in result).to_be(True)
    expect(result["entity_id"]).to_equal("sensor.test_sensor")
    expect(result["unique_id"]).to_equal("unique123")
    expect(result["platform"]).to_equal("test")
    expect(result["original_name"]).to_equal("Test Sensor")
    expect(result["supported_features"]).to_equal(0)
    expect(result["created_at"]).to_equal(created)
