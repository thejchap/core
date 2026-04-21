"""Tests for the schema based data entry flows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
    SchemaFlowMenuStep,
    SchemaOptionsFlowHandler,
    wrapped_entity_config_entry_title,
)
from homeassistant.util.decorator import Registry

from tests.common import MockConfigEntry, MockModule, mock_integration, mock_platform
from tests.hass_fixtures import entity_registry, hass

TEST_DOMAIN = "test"


class MockSchemaConfigFlowHandler(SchemaConfigFlowHandler):
    """Bare minimum SchemaConfigFlowHandler."""

    config_flow = {}

    @callback
    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        return "title"


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


def _make_manager() -> data_entry_flow.FlowManager:
    """Build a fresh FlowManager for tests that need one."""
    handlers = Registry()
    entries = []

    class FlowManager(data_entry_flow.FlowManager):
        def __init__(self) -> None:
            super().__init__(None)
            self.mock_created_entries = entries
            self.mock_reg_handler = handlers.register

        async def async_create_flow(self, handler_key, *, context, data):
            handler = handlers.get(handler_key)
            if handler is None:
                raise data_entry_flow.UnknownHandler
            flow = handler()
            flow.init_step = context.get("init_step", "init")
            return flow

        async def async_finish_flow(self, flow, result):
            if result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY:
                result["source"] = flow.context.get("source")
                entries.append(result)
            return result

    return FlowManager()


@test
async def name(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test the config flow name is copied from registry entry, with fallback to state."""
    entity_id = "switch.ceiling"

    expect(wrapped_entity_config_entry_title(hass, entity_id)).to_equal("ceiling")

    hass.states.async_set(entity_id, "on", {"friendly_name": "State Name"})
    expect(wrapped_entity_config_entry_title(hass, entity_id)).to_equal("State Name")

    hass.states.async_remove(entity_id)
    entry = entity_registry.async_get_or_create(
        "switch",
        "test",
        "unique",
        suggested_object_id="ceiling",
        original_name="Original Name",
    )
    hass.states.async_set(entity_id, "on", {"friendly_name": "State Name"})
    expect(entry.entity_id).to_equal(entity_id)
    expect(wrapped_entity_config_entry_title(hass, entity_id)).to_equal("Original Name")
    expect(wrapped_entity_config_entry_title(hass, entry.id)).to_equal("Original Name")

    entity_registry.async_update_entity("switch.ceiling", name="Custom Name")
    expect(wrapped_entity_config_entry_title(hass, entity_id)).to_equal("Custom Name")
    expect(wrapped_entity_config_entry_title(hass, entry.id)).to_equal("Custom Name")


@test.cases(
    test.case("Required", marker=vol.Required),
    test.case("Optional", marker=vol.Optional),
)
async def config_flow_advanced_option(
    marker,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test handling of advanced options in config flow."""
    manager = _make_manager()
    manager.hass = hass

    CONFIG_SCHEMA = vol.Schema(
        {
            marker("option1"): str,
            marker("advanced_no_default", description={"advanced": True}): str,
            marker(
                "advanced_default",
                default="a very reasonable default",
                description={"advanced": True},
            ): str,
        }
    )

    CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(CONFIG_SCHEMA)
    }

    @manager.mock_reg_handler("test")
    class TestFlow(MockSchemaConfigFlowHandler):
        config_flow = CONFIG_FLOW

    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(list(result["data_schema"].schema.keys())).to_equal(["option1"])

    result = await manager.async_configure(result["flow_id"], {"option1": "blabla"})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "advanced_default": "a very reasonable default",
            "option1": "blabla",
        }
    )
    for option in result["options"]:
        expect(isinstance(option, str)).to_be(True)

    result = await manager.async_init("test", context={"show_advanced_options": True})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(list(result["data_schema"].schema.keys())).to_equal(
        [
            "option1",
            "advanced_no_default",
            "advanced_default",
        ]
    )

    result = await manager.async_configure(
        result["flow_id"], {"advanced_no_default": "abc123", "option1": "blabla"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "advanced_default": "a very reasonable default",
            "advanced_no_default": "abc123",
            "option1": "blabla",
        }
    )
    for option in result["options"]:
        expect(isinstance(option, str)).to_be(True)

    result = await manager.async_init("test", context={"show_advanced_options": True})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(list(result["data_schema"].schema.keys())).to_equal(
        [
            "option1",
            "advanced_no_default",
            "advanced_default",
        ]
    )

    result = await manager.async_configure(
        result["flow_id"],
        {
            "advanced_default": "not default",
            "advanced_no_default": "abc123",
            "option1": "blabla",
        },
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "advanced_default": "not default",
            "advanced_no_default": "abc123",
            "option1": "blabla",
        }
    )
    for option in result["options"]:
        expect(isinstance(option, str)).to_be(True)


@test.cases(
    test.case("Required", marker=vol.Required),
    test.case("Optional", marker=vol.Optional),
)
async def options_flow_advanced_option(
    marker,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test handling of advanced options in options flow."""
    manager = _make_manager()
    manager.hass = hass

    OPTIONS_SCHEMA = vol.Schema(
        {
            marker("option1"): str,
            marker("advanced_no_default", description={"advanced": True}): str,
            marker(
                "advanced_default",
                default="a very reasonable default",
                description={"advanced": True},
            ): str,
        }
    )

    OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(OPTIONS_SCHEMA)
    }

    class TestFlow(MockSchemaConfigFlowHandler, domain="test"):
        config_flow = {}
        options_flow = OPTIONS_FLOW

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.config_flow", None)
    config_entry = MockConfigEntry(
        data={},
        domain="test",
        options={
            "option1": "blabla",
            "advanced_no_default": "abc123",
            "advanced_default": "not default",
        },
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(list(result["data_schema"].schema.keys())).to_equal(["option1"])

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blublu"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "advanced_default": "not default",
            "advanced_no_default": "abc123",
            "option1": "blublu",
        }
    )
    for option in result["data"]:
        expect(isinstance(option, str)).to_be(True)

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(list(result["data_schema"].schema.keys())).to_equal(
        [
            "option1",
            "advanced_no_default",
            "advanced_default",
        ]
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"advanced_no_default": "def456", "option1": "blabla"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "advanced_default": "a very reasonable default",
            "advanced_no_default": "def456",
            "option1": "blabla",
        }
    )
    for option in result["data"]:
        expect(isinstance(option, str)).to_be(True)

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(list(result["data_schema"].schema.keys())).to_equal(
        [
            "option1",
            "advanced_no_default",
            "advanced_default",
        ]
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "advanced_default": "also not default",
            "advanced_no_default": "abc123",
            "option1": "blabla",
        },
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "advanced_default": "also not default",
            "advanced_no_default": "abc123",
            "option1": "blabla",
        }
    )
    for option in result["data"]:
        expect(isinstance(option, str)).to_be(True)


@test
async def menu_step(hass: HomeAssistant = Depends(hass)) -> None:
    """Test menu step."""
    MENU_1 = ["option1", "option2"]

    async def menu_2(handler: SchemaCommonFlowHandler) -> list[str]:
        return ["option3", "option4"]

    async def _option1_next_step(_: dict[str, Any]) -> str:
        return "menu2"

    CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "user": SchemaFlowMenuStep(MENU_1),
        "option1": SchemaFlowFormStep(vol.Schema({}), next_step=_option1_next_step),
        "menu2": SchemaFlowMenuStep(menu_2),
        "option3": SchemaFlowFormStep(vol.Schema({}), next_step="option4"),
        "option4": SchemaFlowFormStep(vol.Schema({})),
    }

    class TestConfigFlow(MockSchemaConfigFlowHandler, domain=TEST_DOMAIN):
        config_flow = CONFIG_FLOW

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    with patch.dict(config_entries.HANDLERS, {TEST_DOMAIN: TestConfigFlow}):
        result = await hass.config_entries.flow.async_init(
            TEST_DOMAIN, context={"source": "user"}
        )
        expect(result["type"]).to_be(FlowResultType.MENU)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "option1"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("option1")

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.MENU)
        expect(result["step_id"]).to_equal("menu2")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "option3"},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("option3")

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("option4")

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def schema_none(hass: HomeAssistant = Depends(hass)) -> None:
    """Test SchemaFlowFormStep with schema set to None."""
    CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "user": SchemaFlowFormStep(next_step="option1"),
        "option1": SchemaFlowFormStep(vol.Schema({}), next_step="pass"),
        "pass": SchemaFlowFormStep(next_step="option3"),
        "option3": SchemaFlowFormStep(vol.Schema({})),
    }

    class TestConfigFlow(MockSchemaConfigFlowHandler, domain=TEST_DOMAIN):
        config_flow = CONFIG_FLOW

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    with patch.dict(config_entries.HANDLERS, {TEST_DOMAIN: TestConfigFlow}):
        result = await hass.config_entries.flow.async_init(
            TEST_DOMAIN, context={"source": "user"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("option1")

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("option3")

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def last_step(hass: HomeAssistant = Depends(hass)) -> None:
    """Test SchemaFlowFormStep last_step tracking."""

    async def _step2_next_step(_: dict[str, Any]) -> str:
        return "step3"

    CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "user": SchemaFlowFormStep(next_step="step1"),
        "step1": SchemaFlowFormStep(vol.Schema({}), next_step="step2"),
        "step2": SchemaFlowFormStep(vol.Schema({}), next_step=_step2_next_step),
        "step3": SchemaFlowFormStep(vol.Schema({}), next_step=None),
    }

    class TestConfigFlow(MockSchemaConfigFlowHandler, domain=TEST_DOMAIN):
        config_flow = CONFIG_FLOW

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    with patch.dict(config_entries.HANDLERS, {TEST_DOMAIN: TestConfigFlow}):
        result = await hass.config_entries.flow.async_init(
            TEST_DOMAIN, context={"source": "user"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("step1")
        expect(result["last_step"]).to_be(False)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("step2")
        expect(result["last_step"]).to_be_none()

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("step3")
        expect(result["last_step"]).to_be(True)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def next_step_function(hass: HomeAssistant = Depends(hass)) -> None:
    """Test SchemaFlowFormStep with a next_step function."""

    async def _step1_next_step(_: dict[str, Any]) -> str:
        return "step2"

    async def _step2_next_step(_: dict[str, Any]) -> None:
        return None

    CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "user": SchemaFlowFormStep(next_step="step1"),
        "step1": SchemaFlowFormStep(vol.Schema({}), next_step=_step1_next_step),
        "step2": SchemaFlowFormStep(vol.Schema({}), next_step=_step2_next_step),
    }

    class TestConfigFlow(MockSchemaConfigFlowHandler, domain=TEST_DOMAIN):
        config_flow = CONFIG_FLOW

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    with patch.dict(config_entries.HANDLERS, {TEST_DOMAIN: TestConfigFlow}):
        result = await hass.config_entries.flow.async_init(
            TEST_DOMAIN, context={"source": "user"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("step1")

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("step2")

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def suggested_values(hass: HomeAssistant = Depends(hass)) -> None:
    """Test suggested_values handling in SchemaFlowFormStep."""
    manager = _make_manager()
    manager.hass = hass

    OPTIONS_SCHEMA = vol.Schema(
        {vol.Optional("option1", default="a very reasonable default"): str}
    )

    async def _validate_user_input(
        handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
    ) -> dict[str, Any]:
        if user_input["option1"] == "not a valid value":
            raise SchemaFlowError("option1 not using a valid value")
        return user_input

    async def _step_2_suggested_values(_: SchemaCommonFlowHandler) -> dict[str, Any]:
        return {"option1": "a random override"}

    OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(OPTIONS_SCHEMA, next_step="step_1"),
        "step_1": SchemaFlowFormStep(OPTIONS_SCHEMA, next_step="step_2"),
        "step_2": SchemaFlowFormStep(
            OPTIONS_SCHEMA,
            suggested_values=_step_2_suggested_values,
            next_step="step_3",
        ),
        "step_3": SchemaFlowFormStep(
            OPTIONS_SCHEMA, suggested_values=None, next_step="step_4"
        ),
        "step_4": SchemaFlowFormStep(
            OPTIONS_SCHEMA, validate_user_input=_validate_user_input
        ),
    }

    class TestFlow(MockSchemaConfigFlowHandler, domain="test"):
        config_flow = {}
        options_flow = OPTIONS_FLOW

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.config_flow", None)
    config_entry = MockConfigEntry(
        data={},
        domain="test",
        options={"option1": "initial value"},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    schema_keys = list(result["data_schema"].schema.keys())
    expect(schema_keys).to_equal(["option1"])
    expect(schema_keys[0].description).to_equal({"suggested_value": "initial value"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blublu"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("step_1")
    schema_keys = list(result["data_schema"].schema.keys())
    expect(schema_keys).to_equal(["option1"])
    expect(schema_keys[0].description).to_equal({"suggested_value": "blublu"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("step_2")
    schema_keys = list(result["data_schema"].schema.keys())
    expect(schema_keys).to_equal(["option1"])
    expect(schema_keys[0].description).to_equal(
        {"suggested_value": "a random override"}
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("step_3")
    schema_keys = list(result["data_schema"].schema.keys())
    expect(schema_keys).to_equal(["option1"])
    expect(schema_keys[0].description).to_be_none()

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("step_4")
    schema_keys = list(result["data_schema"].schema.keys())
    expect(schema_keys).to_equal(["option1"])
    expect(schema_keys[0].description).to_equal({"suggested_value": "blabla"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "not a valid value"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("step_4")
    schema_keys = list(result["data_schema"].schema.keys())
    expect(schema_keys).to_equal(["option1"])
    expect(schema_keys[0].description).to_equal(
        {"suggested_value": "not a valid value"}
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)


@test
async def description_placeholders(hass: HomeAssistant = Depends(hass)) -> None:
    """Test description_placeholders handling in SchemaFlowFormStep."""
    manager = _make_manager()
    manager.hass = hass

    OPTIONS_SCHEMA = vol.Schema(
        {vol.Optional("option1", default="a very reasonable default"): str}
    )

    async def _get_description_placeholders(
        _: SchemaCommonFlowHandler,
    ) -> dict[str, Any]:
        return {"option1": "a dynamic string"}

    OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(
            OPTIONS_SCHEMA,
            next_step="step_1",
            description_placeholders=_get_description_placeholders,
        ),
    }

    class TestFlow(MockSchemaConfigFlowHandler, domain="test"):
        config_flow = {}
        options_flow = OPTIONS_FLOW

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.config_flow", None)
    config_entry = MockConfigEntry(data={}, domain="test")
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(result["description_placeholders"]).to_equal({"option1": "a dynamic string"})


@test
async def options_flow_state(hass: HomeAssistant = Depends(hass)) -> None:
    """Test flow_state handling in SchemaFlowFormStep."""
    OPTIONS_SCHEMA = vol.Schema(
        {vol.Optional("option1", default="a very reasonable default"): str}
    )

    async def _init_schema(handler: SchemaCommonFlowHandler) -> None:
        handler.flow_state["idx"] = None

    async def _validate_step1_input(
        handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
    ) -> dict[str, Any]:
        handler.flow_state["idx"] = user_input["option1"]
        return user_input

    async def _validate_step2_input(
        handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
    ) -> dict[str, Any]:
        user_input["idx_from_flow_state"] = handler.flow_state["idx"]
        return user_input

    OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(_init_schema, next_step="step_1"),
        "step_1": SchemaFlowFormStep(
            OPTIONS_SCHEMA,
            validate_user_input=_validate_step1_input,
            next_step="step_2",
        ),
        "step_2": SchemaFlowFormStep(
            OPTIONS_SCHEMA,
            validate_user_input=_validate_step2_input,
        ),
    }

    class TestFlow(MockSchemaConfigFlowHandler, domain="test"):
        config_flow = {}
        options_flow = OPTIONS_FLOW

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.config_flow", None)
    config_entry = MockConfigEntry(
        data={},
        domain="test",
        options={"option1": "initial value"},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("step_1")

    options_handler: SchemaOptionsFlowHandler
    options_handler = hass.config_entries.options._progress[result["flow_id"]]
    expect(options_handler._common_handler.flow_state).to_equal({"idx": None})

    expect(options_handler.options).to_be(options_handler._common_handler.options)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blublu"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("step_2")

    options_handler = hass.config_entries.options._progress[result["flow_id"]]
    expect(options_handler._common_handler.flow_state).to_equal({"idx": "blublu"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"option1": "blabla"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "idx_from_flow_state": "blublu",
            "option1": "blabla",
        }
    )


@test
async def options_flow_omit_optional_keys(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test handling of advanced options in options flow."""
    manager = _make_manager()
    manager.hass = hass

    OPTIONS_SCHEMA = vol.Schema(
        {
            vol.Optional("optional_no_default"): str,
            vol.Optional("optional_default", default="a very reasonable default"): str,
            vol.Optional("advanced_no_default", description={"advanced": True}): str,
            vol.Optional(
                "advanced_default",
                default="a very reasonable default",
                description={"advanced": True},
            ): str,
        }
    )

    OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(OPTIONS_SCHEMA)
    }

    class TestFlow(MockSchemaConfigFlowHandler, domain="test"):
        config_flow = {}
        options_flow = OPTIONS_FLOW

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.config_flow", None)
    config_entry = MockConfigEntry(
        data={},
        domain="test",
        options={
            "optional_no_default": "abc123",
            "optional_default": "not default",
            "advanced_no_default": "abc123",
            "advanced_default": "not default",
        },
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(list(result["data_schema"].schema.keys())).to_equal(
        [
            "optional_no_default",
            "optional_default",
        ]
    )

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "advanced_default": "not default",
            "advanced_no_default": "abc123",
            "optional_default": "a very reasonable default",
        }
    )

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": True}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(list(result["data_schema"].schema.keys())).to_equal(
        [
            "optional_no_default",
            "optional_default",
            "advanced_no_default",
            "advanced_default",
        ]
    )

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "advanced_default": "a very reasonable default",
            "optional_default": "a very reasonable default",
        }
    )


@test.cases(
    test.case(
        "should_not_reload",
        new_options={},
        expected_loads=1,
        expected_unloads=0,
    ),
    test.case(
        "should_reload",
        new_options={"some_string": "some_value"},
        expected_loads=2,
        expected_unloads=1,
    ),
)
async def options_flow_with_automatic_reload(
    new_options: dict[str, str],
    expected_loads: int,
    expected_unloads: int,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test using options flow with automatic reloading."""
    manager = _make_manager()
    manager.hass = hass

    OPTIONS_SCHEMA = vol.Schema({vol.Optional("some_string"): str})

    OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
        "init": SchemaFlowFormStep(OPTIONS_SCHEMA)
    }

    class TestFlow(MockSchemaConfigFlowHandler, domain="test"):
        config_flow = {}
        options_flow = OPTIONS_FLOW
        options_flow_reloads = True

    load_entry_mock = AsyncMock(return_value=True)
    unload_entry_mock = AsyncMock(return_value=True)
    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=load_entry_mock,
            async_unload_entry=unload_entry_mock,
        ),
    )
    mock_platform(hass, "test.config_flow", None)
    config_entry = MockConfigEntry(
        data={},
        domain="test",
        options={
            "optional_no_default": "abc123",
            "optional_default": "not default",
            "advanced_no_default": "abc123",
            "advanced_default": "not default",
        },
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    expect(len(load_entry_mock.mock_calls)).to_equal(1)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], new_options
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)

    expect(len(load_entry_mock.mock_calls)).to_equal(expected_loads)
    expect(len(unload_entry_mock.mock_calls)).to_equal(expected_unloads)
