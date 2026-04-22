"""Tests for hassfest triggers."""

import io
import json
from pathlib import Path
from unittest.mock import patch

from tryke import expect, test

from homeassistant.util.yaml.loader import parse_yaml
from script.hassfest import triggers
from script.hassfest.model import Config, Integration

from . import get_integration

TRIGGER_DESCRIPTION_FILENAME = "triggers.yaml"
TRIGGER_ICONS_FILENAME = "icons.json"
TRIGGER_STRINGS_FILENAME = "strings.json"

TRIGGER_DESCRIPTIONS = {
    "valid": {
        TRIGGER_DESCRIPTION_FILENAME: """
            _:
              fields:
                event:
                  example: sunrise
                  selector:
                    select:
                      options:
                        - sunrise
                        - sunset
                offset:
                  selector:
                    time: null
                offset_no_description:
                  selector:
                    time: null
        """,
        TRIGGER_ICONS_FILENAME: {"triggers": {"_": {"trigger": "mdi:flash"}}},
        TRIGGER_STRINGS_FILENAME: {
            "triggers": {
                "_": {
                    "name": "MQTT",
                    "description": "When a specific message is received on a given MQTT topic.",
                    "fields": {
                        "event": {"name": "Event", "description": "The event."},
                        "offset": {"name": "Offset", "description": "The offset."},
                        "offset_no_description": {"name": "Offset"},
                    },
                }
            }
        },
        "errors": [],
    },
    "yaml_missing_colon": {
        TRIGGER_DESCRIPTION_FILENAME: """
            test:
              fields
                entity:
                  selector:
                    entity:
        """,
        "errors": ["Invalid triggers.yaml"],
    },
    "invalid_triggers_schema": {
        TRIGGER_DESCRIPTION_FILENAME: """
            invalid_trigger:
              fields:
                entity:
                  selector:
                    invalid_selector: null
        """,
        "errors": ["Unknown selector type invalid_selector"],
    },
    "missing_strings_and_icons": {
        TRIGGER_DESCRIPTION_FILENAME: """
            sun:
              fields:
                event:
                  example: sunrise
                  selector:
                    select:
                      options:
                        - sunrise
                        - sunset
                      translation_key: event
                offset:
                  selector:
                    time: null
        """,
        TRIGGER_ICONS_FILENAME: {"triggers": {}},
        TRIGGER_STRINGS_FILENAME: {
            "triggers": {
                "sun": {
                    "fields": {
                        "offset": {},
                    },
                }
            }
        },
        "errors": [
            "has no icon",
            "has no name",
            "has no description",
            "field event with no name",
            "field event with a selector with a translation key",
            "field offset with no name",
        ],
    },
}


@test
def validate() -> None:
    """Test validate version with no key."""
    config = Config(
        root=Path(".").absolute(),
        specific_integrations=None,
        action="validate",
        requirements=True,
    )

    def _load_yaml(fname, secrets=None):
        domain, yaml_file = fname.split("/")
        expect(yaml_file).to_equal(TRIGGER_DESCRIPTION_FILENAME).fatal()

        trigger_descriptions = TRIGGER_DESCRIPTIONS[domain][yaml_file]
        with io.StringIO(trigger_descriptions) as file:
            return parse_yaml(file)

    def _patched_path_read_text(path: Path):
        domain = path.parent.name
        filename = path.name

        return json.dumps(TRIGGER_DESCRIPTIONS[domain][filename])

    with patch.object(Integration, "core", return_value=True):
        integrations = {
            domain: get_integration(domain, config) for domain in TRIGGER_DESCRIPTIONS
        }

        with (
            patch("script.hassfest.triggers.grep_dir", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.read_text", _patched_path_read_text),
            patch("annotatedyaml.loader.load_yaml", side_effect=_load_yaml),
        ):
            triggers.validate(integrations, config)

        expect(bool(config.errors)).to_be(False)

        for domain, description in TRIGGER_DESCRIPTIONS.items():
            expect(len(integrations[domain].errors)).to_equal(
                len(description["errors"])
            )
            for error, expected_error in zip(
                integrations[domain].errors, description["errors"], strict=True
            ):
                expect(expected_error in error.error).to_be(True)
