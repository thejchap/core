"""Test blueprint models."""

import logging
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.blueprint import BLUEPRINT_SCHEMA, errors, models
from homeassistant.core import HomeAssistant
from homeassistant.util.yaml import Input

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@fixture
def blueprint_1() -> models.Blueprint:
    """Blueprint fixture."""
    return models.Blueprint(
        {
            "blueprint": {
                "name": "Hello",
                "domain": "automation",
                "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml",
                "input": {"test-input": {"name": "Name", "description": "Description"}},
            },
            "example": Input("test-input"),
        },
        schema=BLUEPRINT_SCHEMA,
    )


def _build_blueprint_2(in_sections: bool) -> models.Blueprint:
    """Construct the parametrized blueprint_2 with optional sections."""
    blueprint: dict[str, Any] = {
        "blueprint": {
            "name": "Hello",
            "domain": "automation",
            "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml",
            "input": {
                "test-input": {"name": "Name", "description": "Description"},
                "test-input-default": {"default": "test"},
            },
        },
        "example": Input("test-input"),
        "example-default": Input("test-input-default"),
    }
    if in_sections:
        # Replace the inputs with inputs in sections. Test should otherwise behave the same.
        blueprint["blueprint"]["input"] = {
            "section-1": {
                "name": "Section 1",
                "input": {
                    "test-input": {"name": "Name", "description": "Description"},
                },
            },
            "section-2": {
                "input": {
                    "test-input-default": {"default": "test"},
                }
            },
        }
    return models.Blueprint(blueprint, schema=BLUEPRINT_SCHEMA)


@fixture
def domain_bps(
    hass: HomeAssistant = Depends(hass_fixture),
) -> models.DomainBlueprints:
    """Domain blueprints fixture."""
    return models.DomainBlueprints(
        hass,
        "automation",
        logging.getLogger(__name__),
        None,
        AsyncMock(),
        BLUEPRINT_SCHEMA,
    )


@test
def blueprint_model_init() -> None:
    """Test constructor validation."""
    expect(lambda: models.Blueprint({}, schema=BLUEPRINT_SCHEMA)).to_raise(
        errors.InvalidBlueprint
    )

    expect(
        lambda: models.Blueprint(
            {"blueprint": {"name": "Hello", "domain": "automation"}},
            expected_domain="not-automation",
            schema=BLUEPRINT_SCHEMA,
        )
    ).to_raise(errors.InvalidBlueprint)

    expect(
        lambda: models.Blueprint(
            {
                "blueprint": {
                    "name": "Hello",
                    "domain": "automation",
                    "input": {"something": None},
                },
                "trigger": {"platform": Input("non-existing")},
            },
            schema=BLUEPRINT_SCHEMA,
        )
    ).to_raise(errors.InvalidBlueprint)


@test
def blueprint_properties(
    blueprint_1: models.Blueprint = Depends(blueprint_1),
) -> None:
    """Test properties."""
    expect(blueprint_1.metadata).to_equal(
        {
            "name": "Hello",
            "domain": "automation",
            "source_url": "https://github.com/balloob/home-assistant-config/blob/main/blueprints/automation/motion_light.yaml",
            "input": {"test-input": {"name": "Name", "description": "Description"}},
        }
    )
    expect(blueprint_1.domain).to_equal("automation")
    expect(blueprint_1.name).to_equal("Hello")
    expect(blueprint_1.inputs).to_equal(
        {"test-input": {"name": "Name", "description": "Description"}}
    )


@test
def blueprint_update_metadata() -> None:
    """Test update metadata."""
    bp = models.Blueprint(
        {
            "blueprint": {
                "name": "Hello",
                "domain": "automation",
            },
        },
        schema=BLUEPRINT_SCHEMA,
    )

    bp.update_metadata(source_url="http://bla.com")
    expect(bp.metadata["source_url"]).to_equal("http://bla.com")


@test
def blueprint_validate() -> None:
    """Test validate blueprint."""
    expect(
        models.Blueprint(
            {
                "blueprint": {
                    "name": "Hello",
                    "domain": "automation",
                },
            },
            schema=BLUEPRINT_SCHEMA,
        ).validate()
    ).to_be_none()

    expect(
        models.Blueprint(
            {
                "blueprint": {
                    "name": "Hello",
                    "domain": "automation",
                    "homeassistant": {"min_version": "100000.0.0"},
                },
            },
            schema=BLUEPRINT_SCHEMA,
        ).validate()
    ).to_equal(["Requires at least Home Assistant 100000.0.0"])


@test.cases(
    test.case("flat", in_sections=False),
    test.case("sections", in_sections=True),
)
def blueprint_inputs(in_sections: bool) -> None:
    """Test blueprint inputs."""
    blueprint_2 = _build_blueprint_2(in_sections)
    inputs = models.BlueprintInputs(
        blueprint_2,
        {
            "use_blueprint": {
                "path": "bla",
                "input": {"test-input": 1, "test-input-default": 12},
            },
            "example-default": {"overridden": "via-config"},
        },
    )
    inputs.validate()
    expect(inputs.inputs).to_equal({"test-input": 1, "test-input-default": 12})
    expect(inputs.async_substitute()).to_equal(
        {
            "example": 1,
            "example-default": {"overridden": "via-config"},
        }
    )


@test
def blueprint_inputs_validation(
    blueprint_1: models.Blueprint = Depends(blueprint_1),
) -> None:
    """Test blueprint input validation."""
    inputs = models.BlueprintInputs(
        blueprint_1,
        {"use_blueprint": {"path": "bla", "input": {"non-existing-placeholder": 1}}},
    )
    expect(lambda: inputs.validate()).to_raise(errors.MissingInput)


@test.cases(
    test.case("flat", in_sections=False),
    test.case("sections", in_sections=True),
)
def blueprint_inputs_default(in_sections: bool) -> None:
    """Test blueprint inputs."""
    blueprint_2 = _build_blueprint_2(in_sections)
    inputs = models.BlueprintInputs(
        blueprint_2,
        {"use_blueprint": {"path": "bla", "input": {"test-input": 1}}},
    )
    inputs.validate()
    expect(inputs.inputs).to_equal({"test-input": 1})
    expect(inputs.inputs_with_default).to_equal(
        {
            "test-input": 1,
            "test-input-default": "test",
        }
    )
    expect(inputs.async_substitute()).to_equal(
        {"example": 1, "example-default": "test"}
    )


@test.cases(
    test.case("flat", in_sections=False),
    test.case("sections", in_sections=True),
)
def blueprint_inputs_override_default(in_sections: bool) -> None:
    """Test blueprint inputs."""
    blueprint_2 = _build_blueprint_2(in_sections)
    inputs = models.BlueprintInputs(
        blueprint_2,
        {
            "use_blueprint": {
                "path": "bla",
                "input": {"test-input": 1, "test-input-default": "custom"},
            }
        },
    )
    inputs.validate()
    expect(inputs.inputs).to_equal(
        {
            "test-input": 1,
            "test-input-default": "custom",
        }
    )
    expect(inputs.inputs_with_default).to_equal(
        {
            "test-input": 1,
            "test-input-default": "custom",
        }
    )
    expect(inputs.async_substitute()).to_equal(
        {"example": 1, "example-default": "custom"}
    )


@test
async def domain_blueprints_get_blueprint_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    domain_bps: models.DomainBlueprints = Depends(domain_bps),
) -> None:
    """Test domain blueprints."""
    expect(hass.data["blueprint"]["automation"]).to_be(domain_bps)

    with patch("homeassistant.util.yaml.load_yaml", side_effect=FileNotFoundError):
        async with expect_raises_async(errors.FailedToLoad):
            await domain_bps.async_get_blueprint("non-existing-path")

    with patch(
        "homeassistant.util.yaml.load_yaml", return_value={"blueprint": "invalid"}
    ):
        async with expect_raises_async(errors.FailedToLoad):
            await domain_bps.async_get_blueprint("non-existing-path")


@test
async def domain_blueprints_caching(
    domain_bps: models.DomainBlueprints = Depends(domain_bps),
) -> None:
    """Test domain blueprints cache blueprints."""
    obj = object()
    with patch.object(domain_bps, "_load_blueprint", return_value=obj):
        expect(await domain_bps.async_get_blueprint("something")).to_be(obj)

    # Now we hit cache
    expect(await domain_bps.async_get_blueprint("something")).to_be(obj)

    obj_2 = object()
    await domain_bps.async_reset_cache()

    # Now we call this method again.
    with patch.object(domain_bps, "_load_blueprint", return_value=obj_2):
        expect(await domain_bps.async_get_blueprint("something")).to_be(obj_2)


@test
async def domain_blueprints_inputs_from_config(
    domain_bps: models.DomainBlueprints = Depends(domain_bps),
    blueprint_1: models.Blueprint = Depends(blueprint_1),
) -> None:
    """Test DomainBlueprints.async_inputs_from_config."""
    async with expect_raises_async(errors.InvalidBlueprintInputs):
        await domain_bps.async_inputs_from_config({"not-referencing": "use_blueprint"})

    with patch.object(domain_bps, "async_get_blueprint", return_value=blueprint_1):
        async with expect_raises_async(errors.MissingInput):
            await domain_bps.async_inputs_from_config(
                {"use_blueprint": {"path": "bla.yaml", "input": {}}}
            )

    with patch.object(domain_bps, "async_get_blueprint", return_value=blueprint_1):
        inputs = await domain_bps.async_inputs_from_config(
            {"use_blueprint": {"path": "bla.yaml", "input": {"test-input": None}}}
        )
    expect(inputs.blueprint).to_be(blueprint_1)
    expect(inputs.inputs).to_equal({"test-input": None})


@test
async def domain_blueprints_add_blueprint(
    domain_bps: models.DomainBlueprints = Depends(domain_bps),
    blueprint_1: models.Blueprint = Depends(blueprint_1),
) -> None:
    """Test DomainBlueprints.async_add_blueprint."""
    with patch.object(domain_bps, "_create_file") as create_file_mock:
        await domain_bps.async_add_blueprint(blueprint_1, "something.yaml")
        expect(create_file_mock.call_args[0][1]).to_equal("something.yaml")

    # Should be in cache.
    with patch.object(domain_bps, "_load_blueprint") as mock_load:
        expect(await domain_bps.async_get_blueprint("something.yaml")).to_equal(
            blueprint_1
        )
        expect(bool(mock_load.mock_calls)).to_equal(False)


@test
async def inputs_from_config_nonexisting_blueprint(
    domain_bps: models.DomainBlueprints = Depends(domain_bps),
) -> None:
    """Test referring non-existing blueprint."""
    async with expect_raises_async(errors.FailedToLoad):
        await domain_bps.async_inputs_from_config(
            {"use_blueprint": {"path": "non-existing.yaml"}}
        )
