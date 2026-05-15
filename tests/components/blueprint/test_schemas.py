"""Test schemas."""

import logging
from typing import Any

from tryke import expect, test
import voluptuous as vol

from homeassistant.components.blueprint import schemas

_LOGGER = logging.getLogger(__name__)


@test.cases(
    test.case(
        "allow_extra",
        blueprint={
            "trigger": "Test allow extra",
            "blueprint": {"name": "Test Name", "domain": "automation"},
        },
    ),
    test.case(
        "bare_minimum",
        blueprint={"blueprint": {"name": "Test Name", "domain": "automation"}},
    ),
    test.case(
        "empty_input",
        blueprint={
            "blueprint": {"name": "Test Name", "domain": "automation", "input": {}}
        },
    ),
    test.case(
        "no_definition_of_input",
        blueprint={
            "blueprint": {
                "name": "Test Name",
                "domain": "automation",
                "input": {"some_placeholder": None},
            }
        },
    ),
    test.case(
        "with_selector",
        blueprint={
            "blueprint": {
                "name": "Test Name",
                "domain": "automation",
                "input": {
                    "some_placeholder": {"selector": {"entity": {}}},
                },
            }
        },
    ),
    test.case(
        "with_min_version",
        blueprint={
            "blueprint": {
                "name": "Test Name",
                "domain": "automation",
                "homeassistant": {"min_version": "1000000.0.0"},
            }
        },
    ),
    test.case(
        "with_input_sections",
        blueprint={
            "blueprint": {
                "name": "Test Name",
                "domain": "automation",
                "input": {
                    "section_a": {"input": {"some_placeholder": None}},
                    "section_b": {
                        "name": "Section",
                        "description": "A section with no inputs",
                        "input": {},
                    },
                    "some_placeholder_2": None,
                },
            }
        },
    ),
)
def blueprint_schema(blueprint: dict[str, Any]) -> None:
    """Test different schemas."""
    try:
        schemas.BLUEPRINT_SCHEMA(blueprint)
    except vol.Invalid as ex:
        _LOGGER.exception("%s", blueprint)
        raise AssertionError(f"Expected schema to be valid: {ex}") from ex


@test.cases(
    test.case("no_domain", blueprint={"blueprint": {}}),
    test.case(
        "non_existing_key",
        blueprint={
            "blueprint": {
                "name": "Example name",
                "domain": "automation",
                "non_existing": None,
            }
        },
    ),
    test.case(
        "non_existing_key_in_input",
        blueprint={
            "blueprint": {
                "name": "Example name",
                "domain": "automation",
                "input": {"some_placeholder": {"non_existing": "bla"}},
            }
        },
    ),
    test.case(
        "invalid_version",
        blueprint={
            "blueprint": {
                "name": "Test Name",
                "domain": "automation",
                "homeassistant": {"min_version": "1000000.invalid.0"},
            }
        },
    ),
    test.case(
        "duplicate_inputs_in_sections_1",
        blueprint={
            "blueprint": {
                "name": "Test Name",
                "domain": "automation",
                "input": {
                    "section_a": {"input": {"some_placeholder": None}},
                    "section_b": {"input": {"some_placeholder": None}},
                },
            }
        },
    ),
    test.case(
        "duplicate_inputs_in_sections_2",
        blueprint={
            "blueprint": {
                "name": "Test Name",
                "domain": "automation",
                "input": {
                    "section_a": {"input": {"some_placeholder": None}},
                    "some_placeholder": None,
                },
            }
        },
    ),
)
def blueprint_schema_invalid(blueprint: dict[str, Any]) -> None:
    """Test different schemas."""
    expect(lambda: schemas.BLUEPRINT_SCHEMA(blueprint)).to_raise(vol.Invalid)


@test.cases(
    test.case("path_only", bp_instance={"path": "hello.yaml"}),
    test.case("empty_input", bp_instance={"path": "hello.yaml", "input": {}}),
    test.case(
        "with_input",
        bp_instance={"path": "hello.yaml", "input": {"hello": None}},
    ),
)
def blueprint_instance_fields(bp_instance: dict[str, Any]) -> None:
    """Test blueprint instance fields."""
    schemas.BLUEPRINT_INSTANCE_FIELDS({"use_blueprint": bp_instance})
