"""Test the flow classes."""

from __future__ import annotations

import asyncio
import dataclasses
import logging
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.util.decorator import Registry

from .common import async_capture_events
from .hass_fixtures import LogCapture, caplog, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


class MockFlowManager(data_entry_flow.FlowManager):
    """Test flow manager."""

    def __init__(self) -> None:
        """Initialize the flow manager."""
        super().__init__(None)
        self._handlers = Registry()
        self.mock_reg_handler = self._handlers.register
        self.mock_created_entries = []

    async def async_create_flow(self, handler_key, *, context, data):
        """Test create flow."""
        handler = self._handlers.get(handler_key)

        if handler is None:
            raise data_entry_flow.UnknownHandler

        flow = handler()
        flow.init_step = context.get("init_step", "init")
        return flow

    async def async_finish_flow(self, flow, result):
        """Test finish flow."""
        if result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY:
            result["source"] = flow.context.get("source")
            self.mock_created_entries.append(result)
        return result


@fixture
def manager() -> MockFlowManager:
    """Return a flow manager."""
    return MockFlowManager()


def _expect_raises_sync(
    exc_type: type[BaseException], fn: Any, *args: Any, **kwargs: Any
) -> BaseException:
    """Call fn and return the caught exception."""
    try:
        fn(*args, **kwargs)
    except exc_type as exc:
        return exc
    raise AssertionError(f"Expected {exc_type.__name__}")


async def _expect_raises_async(
    exc_type: type[BaseException], coro: Any
) -> BaseException:
    """Await coro and return the caught exception."""
    try:
        await coro
    except exc_type as exc:
        return exc
    raise AssertionError(f"Expected {exc_type.__name__}")


@test
async def configure_reuses_handler_instance(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test that we reuse instances."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        handle_count = 0

        async def async_step_init(self, user_input=None):
            self.handle_count += 1
            return self.async_show_form(
                errors={"base": str(self.handle_count)}, step_id="init"
            )

    form = await manager.async_init("test")
    expect(form["errors"]["base"]).to_equal("1")
    form = await manager.async_configure(form["flow_id"])
    expect(form["errors"]["base"]).to_equal("2")
    expect(manager.async_progress()).to_equal(
        [
            {
                "flow_id": form["flow_id"],
                "handler": "test",
                "step_id": "init",
                "context": {},
            }
        ]
    )
    expect(len(manager.mock_created_entries)).to_equal(0)


@test
async def configure_two_steps(manager: MockFlowManager = Depends(manager)) -> None:
    """Test that we reuse instances."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 1

        async def async_step_first(self, user_input=None):
            if user_input is not None:
                return await self.async_step_second()
            return self.async_show_form(step_id="first", data_schema=vol.Schema([str]))

        async def async_step_second(self, user_input=None):
            if user_input is not None:
                return self.async_create_entry(
                    title="Test Entry", data=self.init_data + user_input
                )
            return self.async_show_form(step_id="second", data_schema=vol.Schema([str]))

    form = await manager.async_init(
        "test", context={"init_step": "first"}, data=["INIT-DATA"]
    )

    await _expect_raises_async(
        vol.Invalid, manager.async_configure(form["flow_id"], "INCORRECT-DATA")
    )

    form = await manager.async_configure(form["flow_id"], ["SECOND-DATA"])
    expect(form["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(1)
    result = manager.mock_created_entries[0]
    expect(result["handler"]).to_equal("test")
    expect(result["data"]).to_equal(["INIT-DATA", "SECOND-DATA"])


@test
async def show_form(manager: MockFlowManager = Depends(manager)) -> None:
    """Test that we can show a form."""
    schema = vol.Schema({vol.Required("username"): str, vol.Required("password"): str})

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            return self.async_show_form(
                step_id="init",
                data_schema=schema,
                errors={"username": "Should be unique."},
            )

    form = await manager.async_init("test")
    expect(form["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(form["data_schema"]).to_be(schema)
    expect(form["errors"]).to_equal({"username": "Should be unique."})


@test
async def form_shows_with_added_suggested_values(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test that we can show a form with suggested values."""

    def compare_schemas(schema: vol.Schema, expected_schema: vol.Schema) -> None:
        """Compare two schemas."""
        expect(schema.schema).not_.to_be(expected_schema.schema)

        expect(list(schema.schema)).to_equal(list(expected_schema.schema))

        for key, validator in schema.schema.items():
            if isinstance(validator, data_entry_flow.section):
                expect(validator.schema).to_equal(expected_schema.schema[key].schema)
                continue
            expect(validator).to_equal(expected_schema.schema[key])

    schema = vol.Schema(
        {
            vol.Required("username"): str,
            vol.Required("password"): str,
            vol.Required("section_1"): data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional("full_name"): str,
                    }
                ),
                {"collapsed": False},
            ),
        }
    )

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            data_schema = self.add_suggested_values_to_schema(
                schema,
                user_input,
            )
            return self.async_show_form(
                step_id="init",
                data_schema=data_schema,
            )

    form = await manager.async_init(
        "test",
        data={
            "username": "doej",
            "password": "verySecret1",
            "section_1": {"full_name": "John Doe"},
        },
    )
    expect(form["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(form["data_schema"].schema).not_.to_be(schema.schema)
    expect(form["data_schema"].schema).not_.to_equal(schema.schema)
    compare_schemas(form["data_schema"], schema)
    markers = list(form["data_schema"].schema)
    expect(len(markers)).to_equal(3)
    expect(markers[0]).to_equal("username")
    expect(markers[0].description).to_equal({"suggested_value": "doej"})
    expect(markers[1]).to_equal("password")
    expect(markers[1].description).to_equal({"suggested_value": "verySecret1"})
    expect(markers[2]).to_equal("section_1")
    section_validator = form["data_schema"].schema["section_1"]
    expect(isinstance(section_validator, data_entry_flow.section)).to_be_truthy()
    # The section instance was copied
    expect(section_validator).not_.to_be(schema.schema["section_1"])
    # The section schema instance was copied
    expect(section_validator.schema).not_.to_be(schema.schema["section_1"].schema)
    expect(section_validator.schema).to_equal(schema.schema["section_1"].schema)
    section_markers = list(section_validator.schema.schema)
    expect(len(section_markers)).to_equal(1)
    expect(section_markers[0]).to_equal("full_name")
    expect(section_markers[0].description).to_equal({"suggested_value": "John Doe"})

    # Test again without suggested values to make sure we're not mutating the schema
    form = await manager.async_init(
        "test",
    )
    expect(form["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(form["data_schema"].schema).not_.to_be(schema.schema)
    expect(form["data_schema"].schema).to_equal(schema.schema)
    markers = list(form["data_schema"].schema)
    expect(len(markers)).to_equal(3)
    expect(markers[0]).to_equal("username")
    expect(markers[0].description).to_be(None)
    expect(markers[1]).to_equal("password")
    expect(markers[1].description).to_be(None)
    expect(markers[2]).to_equal("section_1")
    section_validator = form["data_schema"].schema["section_1"]
    expect(isinstance(section_validator, data_entry_flow.section)).to_be_truthy()
    # The section class is not replaced if there is no suggested value for the section
    expect(section_validator).to_be(schema.schema["section_1"])
    # The section schema is not replaced if there is no suggested value for the section
    expect(section_validator.schema).to_be(schema.schema["section_1"].schema)
    section_markers = list(section_validator.schema.schema)
    expect(len(section_markers)).to_equal(1)
    expect(section_markers[0]).to_equal("full_name")
    expect(section_markers[0].description).to_be(None)


@test
async def abort_removes_instance(manager: MockFlowManager = Depends(manager)) -> None:
    """Test that abort removes the flow from progress."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        is_new = True

        async def async_step_init(self, user_input=None):
            old = self.is_new
            self.is_new = False
            return self.async_abort(reason=str(old))

    form = await manager.async_init("test")
    expect(form["reason"]).to_equal("True")
    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(0)
    form = await manager.async_init("test")
    expect(form["reason"]).to_equal("True")
    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(0)


@test
async def abort_aborted_flow(manager: MockFlowManager = Depends(manager)) -> None:
    """Test return abort from aborted flow."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            manager.async_abort(self.flow_id)
            return self.async_abort(reason="blah")

    form = await manager.async_init("test")
    expect(form["reason"]).to_equal("blah")
    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(0)


@test
async def abort_calls_async_remove(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test abort calling the async_remove FlowHandler method."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            return self.async_abort(reason="reason")

        async_remove = Mock()

    await manager.async_init("test")

    TestFlow.async_remove.assert_called_once()

    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(0)


@test
async def abort_calls_async_flow_removed(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test abort calling the async_flow_removed FlowManager method."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            return self.async_abort(reason="reason")

    manager.async_flow_removed = Mock()
    await manager.async_init("test")

    manager.async_flow_removed.assert_called_once()

    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(0)


@test
async def abort_calls_async_remove_with_exception(
    manager: MockFlowManager = Depends(manager),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test abort calling the async_remove FlowHandler method, with an exception."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            return self.async_abort(reason="reason")

        async_remove = Mock(side_effect=[RuntimeError("error")])

    with caplog.at_level(logging.ERROR):
        await manager.async_init("test")

    expect("Error removing test flow" in caplog.text).to_be_truthy()

    TestFlow.async_remove.assert_called_once()

    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(0)


@test
async def create_saves_data(manager: MockFlowManager = Depends(manager)) -> None:
    """Test creating a config entry."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5

        async def async_step_init(self, user_input=None):
            return self.async_create_entry(title="Test Title", data="Test Data")

    await manager.async_init("test")
    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(1)

    entry = manager.mock_created_entries[0]
    expect(entry["handler"]).to_equal("test")
    expect(entry["title"]).to_equal("Test Title")
    expect(entry["data"]).to_equal("Test Data")
    expect(entry["source"]).to_be(None)


@test
async def create_aborted_flow(manager: MockFlowManager = Depends(manager)) -> None:
    """Test return create_entry from aborted flow."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5

        async def async_step_init(self, user_input=None):
            manager.async_abort(self.flow_id)
            return self.async_create_entry(title="Test Title", data="Test Data")

    await _expect_raises_async(data_entry_flow.UnknownFlow, manager.async_init("test"))
    expect(len(manager.async_progress())).to_equal(0)

    # No entry should be created if the flow is aborted
    expect(len(manager.mock_created_entries)).to_equal(0)


@test
async def create_calls_async_flow_removed(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test create calling the async_flow_removed FlowManager method."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            return self.async_create_entry(title="Test Title", data="Test Data")

    manager.async_flow_removed = Mock()
    await manager.async_init("test")

    manager.async_flow_removed.assert_called_once()

    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(1)


@test
async def discovery_init_flow(manager: MockFlowManager = Depends(manager)) -> None:
    """Test a flow initialized by discovery."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5

        async def async_step_init(self, info):
            return self.async_create_entry(title=info["id"], data=info)

    data = {"id": "hello", "token": "secret"}

    await manager.async_init(
        "test", context={"source": config_entries.SOURCE_DISCOVERY}, data=data
    )
    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(1)

    entry = manager.mock_created_entries[0]
    expect(entry["handler"]).to_equal("test")
    expect(entry["title"]).to_equal("hello")
    expect(entry["data"]).to_equal(data)
    expect(entry["source"]).to_equal(config_entries.SOURCE_DISCOVERY)


@test
async def finish_callback_change_result_type(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test finish callback can change result type."""

    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 1

        async def async_step_init(self, input):
            """Return init form with one input field 'count'."""
            if input is not None:
                return self.async_create_entry(title="init", data=input)
            return self.async_show_form(
                step_id="init", data_schema=vol.Schema({"count": int})
            )

    class FlowManager(data_entry_flow.FlowManager):
        async def async_create_flow(self, handler_key, *, context, data):
            """Create a test flow."""
            return TestFlow()

        async def async_finish_flow(self, flow, result):
            """Redirect to init form if count <= 1."""
            if result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY:
                if result["data"] is None or result["data"].get("count", 0) <= 1:
                    return flow.async_show_form(
                        step_id="init", data_schema=vol.Schema({"count": int})
                    )
                result["result"] = result["data"]["count"]
            return result

    manager = FlowManager(hass)

    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await manager.async_configure(result["flow_id"], {"count": 0})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect("result" not in result).to_be_truthy()

    result = await manager.async_configure(result["flow_id"], {"count": 2})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["result"]).to_equal(2)


@test
async def external_step(
    hass: HomeAssistant = Depends(hass),
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test external step logic."""
    manager.hass = hass

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None

        async def async_step_init(self, user_input=None):
            if not user_input:
                return self.async_external_step(
                    step_id="init", url="https://example.com"
                )

            self.data = user_input
            return self.async_external_step_done(next_step_id="finish")

        async def async_step_finish(self, user_input=None):
            return self.async_create_entry(title=self.data["title"], data=self.data)

    events = async_capture_events(
        hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED
    )

    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.EXTERNAL_STEP)
    expect(len(manager.async_progress())).to_equal(1)
    expect(len(manager.async_progress_by_handler("test"))).to_equal(1)
    expect(manager.async_get(result["flow_id"])["handler"]).to_equal("test")

    # Mimic external step
    # Called by integrations: `hass.config_entries.flow.async_configure(…)`
    result = await manager.async_configure(result["flow_id"], {"title": "Hello"})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.EXTERNAL_STEP_DONE)

    await hass.async_block_till_done()
    expect(len(events)).to_equal(1)
    expect(events[0].data).to_equal(
        {
            "handler": "test",
            "flow_id": result["flow_id"],
            "refresh": True,
        }
    )

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Hello")


@test
async def show_progress(
    hass: HomeAssistant = Depends(hass),
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test show progress logic."""
    manager.hass = hass
    events: list[Event] = []
    progress_update_events = async_capture_events(
        hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESS_UPDATE
    )
    task_one_evt = asyncio.Event()
    task_two_evt = asyncio.Event()
    event_received_evt = asyncio.Event()

    @callback
    def capture_events(event: Event) -> None:
        events.append(event)
        event_received_evt.set()

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None
        start_task_two = False
        task_one: asyncio.Task[None] | None = None
        task_two: asyncio.Task[None] | None = None

        async def async_step_init(self, user_input=None):
            async def long_running_job_one() -> None:
                await task_one_evt.wait()

            async def long_running_job_two() -> None:
                self.async_update_progress(0.25)
                await task_two_evt.wait()
                self.async_update_progress(0.75)
                self.data = {"title": "Hello"}

            uncompleted_task: asyncio.Task[None] | None = None
            if not self.task_one:
                self.task_one = hass.async_create_task(long_running_job_one())

            progress_action = None
            if not self.task_one.done():
                progress_action = "task_one"
                uncompleted_task = self.task_one

            if not uncompleted_task:
                if not self.task_two:
                    self.task_two = hass.async_create_task(long_running_job_two())

                if not self.task_two.done():
                    progress_action = "task_two"
                    uncompleted_task = self.task_two

            if uncompleted_task:
                expect(progress_action).to_be_truthy()
                return self.async_show_progress(
                    progress_action=progress_action,
                    progress_task=uncompleted_task,
                )

            return self.async_show_progress_done(next_step_id="finish")

        async def async_step_finish(self, user_input=None):
            return self.async_create_entry(title=self.data["title"], data=self.data)

    hass.bus.async_listen(
        data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED,
        capture_events,
    )

    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS)
    expect(result["progress_action"]).to_equal("task_one")
    expect(len(manager.async_progress())).to_equal(1)
    expect(len(manager.async_progress_by_handler("test"))).to_equal(1)
    expect(manager.async_get(result["flow_id"])["handler"]).to_equal("test")

    # Set task one done and wait for event
    task_one_evt.set()
    await event_received_evt.wait()
    event_received_evt.clear()
    expect(len(events)).to_equal(1)
    expect(events[0].data).to_equal(
        {
            "handler": "test",
            "flow_id": result["flow_id"],
            "refresh": True,
        }
    )

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS)
    expect(result["progress_action"]).to_equal("task_two")
    expect(len(progress_update_events)).to_equal(1)
    expect(progress_update_events[0].data).to_equal(
        {
            "handler": "test",
            "flow_id": result["flow_id"],
            "progress": 0.25,
        }
    )

    # Set task two done and wait for event
    task_two_evt.set()
    await event_received_evt.wait()
    event_received_evt.clear()
    expect(len(events)).to_equal(2)  # 1 for task one and 1 for task two
    expect(events[1].data).to_equal(
        {
            "handler": "test",
            "flow_id": result["flow_id"],
            "refresh": True,
        }
    )
    expect(len(progress_update_events)).to_equal(2)
    expect(progress_update_events[1].data).to_equal(
        {
            "handler": "test",
            "flow_id": result["flow_id"],
            "progress": 0.75,
        }
    )

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Hello")


@test
async def show_progress_error(
    hass: HomeAssistant = Depends(hass),
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test show progress logic."""
    manager.hass = hass
    events: list[Event] = []
    event_received_evt = asyncio.Event()

    @callback
    def capture_events(event: Event) -> None:
        events.append(event)
        event_received_evt.set()

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None
        progress_task: asyncio.Task[None] | None = None

        async def async_step_init(self, user_input=None):
            async def long_running_task() -> None:
                await asyncio.sleep(0)
                raise TypeError

            if not self.progress_task:
                self.progress_task = hass.async_create_task(long_running_task())
            if self.progress_task and self.progress_task.done():
                if self.progress_task.exception():
                    return self.async_show_progress_done(next_step_id="error")
                return self.async_show_progress_done(next_step_id="no_error")
            return self.async_show_progress(
                progress_action="task", progress_task=self.progress_task
            )

        async def async_step_error(self, user_input=None):
            return self.async_abort(reason="error")

    hass.bus.async_listen(
        data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED,
        capture_events,
    )

    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS)
    expect(result["progress_action"]).to_equal("task")
    expect(len(manager.async_progress())).to_equal(1)
    expect(len(manager.async_progress_by_handler("test"))).to_equal(1)
    expect(manager.async_get(result["flow_id"])["handler"]).to_equal("test")

    # Set task one done and wait for event
    await event_received_evt.wait()
    event_received_evt.clear()
    expect(len(events)).to_equal(1)
    expect(events[0].data).to_equal(
        {
            "handler": "test",
            "flow_id": result["flow_id"],
            "refresh": True,
        }
    )

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(result["reason"]).to_equal("error")


@test
async def show_progress_hidden_from_frontend(
    hass: HomeAssistant = Depends(hass),
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test show progress done is not sent to frontend."""
    manager.hass = hass
    async_show_progress_done_called = False
    progress_task: asyncio.Task[None] | None = None

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None

        async def async_step_init(self, user_input=None):
            nonlocal progress_task

            async def long_running_job() -> None:
                await asyncio.sleep(0)

            if not progress_task:
                progress_task = hass.async_create_task(long_running_job())
            if progress_task.done():
                nonlocal async_show_progress_done_called
                async_show_progress_done_called = True
                return self.async_show_progress_done(next_step_id="finish")
            return self.async_show_progress(
                step_id="init",
                progress_action="task",
                # Set to a task which never finishes to simulate flow manager has not
                # yet called when frontend loads
                progress_task=hass.async_create_task(asyncio.Event().wait()),
            )

        async def async_step_finish(self, user_input=None):
            return self.async_create_entry(title=None, data=self.data)

    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS)
    expect(result["progress_action"]).to_equal("task")
    expect(len(manager.async_progress())).to_equal(1)
    expect(len(manager.async_progress_by_handler("test"))).to_equal(1)
    expect(manager.async_get(result["flow_id"])["handler"]).to_equal("test")

    await progress_task
    expect(async_show_progress_done_called).to_be_falsy()

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(async_show_progress_done_called).to_be_truthy()


@test
async def show_progress_legacy(
    hass: HomeAssistant = Depends(hass),
    manager: MockFlowManager = Depends(manager),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test show progress logic.

    This tests the deprecated version where the config flow is responsible for
    resuming the flow.
    """
    manager.hass = hass

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None
        task_one_done = False
        task_two_done = False

        async def async_step_init(self, user_input=None):
            if user_input and "task_finished" in user_input:
                if user_input["task_finished"] == 1:
                    self.task_one_done = True
                elif user_input["task_finished"] == 2:
                    self.task_two_done = True

            if not self.task_one_done:
                progress_action = "task_one"
            elif not self.task_two_done:
                progress_action = "task_two"
            if not self.task_one_done or not self.task_two_done:
                return self.async_show_progress(
                    step_id="init",
                    progress_action=progress_action,
                )

            self.data = user_input
            return self.async_show_progress_done(next_step_id="finish")

        async def async_step_finish(self, user_input=None):
            return self.async_create_entry(title=self.data["title"], data=self.data)

    events = async_capture_events(
        hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED
    )

    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS)
    expect(result["progress_action"]).to_equal("task_one")
    expect(len(manager.async_progress())).to_equal(1)
    expect(len(manager.async_progress_by_handler("test"))).to_equal(1)
    expect(manager.async_get(result["flow_id"])["handler"]).to_equal("test")

    # Mimic task one done and moving to task two
    # Called by integrations: `hass.config_entries.flow.async_configure(…)`
    result = await manager.async_configure(result["flow_id"], {"task_finished": 1})
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS)
    expect(result["progress_action"]).to_equal("task_two")

    await hass.async_block_till_done()
    expect(len(events)).to_equal(1)
    expect(events[0].data).to_equal(
        {
            "handler": "test",
            "flow_id": result["flow_id"],
            "refresh": True,
        }
    )

    # Frontend refreshes the flow
    result = await manager.async_configure(result["flow_id"])
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS)
    expect(result["progress_action"]).to_equal("task_two")

    # Mimic task two done and continuing step
    # Called by integrations: `hass.config_entries.flow.async_configure(…)`
    result = await manager.async_configure(
        result["flow_id"], {"task_finished": 2, "title": "Hello"}
    )
    # Note: The SHOW_PROGRESS_DONE is not hidden from frontend when flows manage
    # the progress tasks themselves
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS_DONE)

    # Frontend refreshes the flow
    result = await manager.async_configure(
        result["flow_id"], {"task_finished": 2, "title": "Hello"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Hello")

    await hass.async_block_till_done()
    expect(len(events)).to_equal(2)  # 1 for task one and 1 for task two
    expect(events[1].data).to_equal(
        {
            "handler": "test",
            "flow_id": result["flow_id"],
            "refresh": True,
        }
    )

    # Check for deprecation warning
    expected = (
        "tests.test_data_entry_flow::TestFlow calls async_show_progress without passing"
        " a progress task, this is not valid and will break in Home Assistant "
        "Core 2024.8."
    )
    expect(expected in caplog.text).to_be_truthy()


@test
async def show_progress_fires_only_when_changed(
    hass: HomeAssistant = Depends(hass),
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test show progress change logic."""
    manager.hass = hass

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None

        async def async_step_init(self, user_input=None):
            if user_input:
                progress_action = user_input["progress_action"]
                description_placeholders = user_input["description_placeholders"]
                return self.async_show_progress(
                    step_id="init",
                    progress_action=progress_action,
                    description_placeholders=description_placeholders,
                )
            return self.async_show_progress(step_id="init", progress_action="task_one")

        async def async_step_finish(self, user_input=None):
            return self.async_create_entry(title=self.data["title"], data=self.data)

    events = async_capture_events(
        hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESSED
    )

    async def assert_change(
        flow_id: str,
        events: list[Event],
        progress_action: str,
        description_placeholders_progress: int,
        number_of_events: int,
        is_change: bool,
    ) -> None:
        # Called by integrations: `hass.config_entries.flow.async_configure(…)`
        result = await manager.async_configure(
            flow_id,
            {
                "progress_action": progress_action,
                "description_placeholders": {
                    "progress": description_placeholders_progress
                },
            },
        )
        expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS)
        expect(result["progress_action"]).to_equal(progress_action)
        expect(result["description_placeholders"]["progress"]).to_equal(
            description_placeholders_progress
        )

        await hass.async_block_till_done()
        expect(len(events)).to_equal(number_of_events)
        if is_change:
            expect(events[number_of_events - 1].data).to_equal(
                {
                    "handler": "test",
                    "flow_id": result["flow_id"],
                    "refresh": True,
                }
            )

    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.SHOW_PROGRESS)
    expect(result["progress_action"]).to_equal("task_one")
    expect(len(manager.async_progress())).to_equal(1)
    expect(len(manager.async_progress_by_handler("test"))).to_equal(1)
    expect(manager.async_get(result["flow_id"])["handler"]).to_equal("test")

    # Mimic task one tests
    await assert_change(
        result["flow_id"], events, "task_one", 0, 1, True
    )  # change (progress action)
    await assert_change(result["flow_id"], events, "task_one", 0, 1, False)  # no change
    await assert_change(
        result["flow_id"], events, "task_one", 25, 2, True
    )  # change (description placeholder)
    await assert_change(
        result["flow_id"], events, "task_two", 50, 3, True
    )  # change (progress action and description placeholder)
    await assert_change(
        result["flow_id"], events, "task_two", 50, 3, False
    )  # no change
    await assert_change(
        result["flow_id"], events, "task_two", 100, 4, True
    )  # change (description placeholder)


@test
async def abort_flow_exception_step(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test that the AbortFlow exception works in a step."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            raise data_entry_flow.AbortFlow("mock-reason", {"placeholder": "yo"})

    form = await manager.async_init("test")
    expect(form["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(form["reason"]).to_equal("mock-reason")
    expect(form["description_placeholders"]).to_equal({"placeholder": "yo"})


@test
async def abort_flow_exception_finish_flow(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that the AbortFlow exception works when finishing a flow."""

    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 1

        async def async_step_init(self, input):
            """Return init form with one input field 'count'."""
            return self.async_create_entry(title="init", data=input)

    class FlowManager(data_entry_flow.FlowManager):
        async def async_create_flow(self, handler_key, *, context, data):
            """Create a test flow."""
            return TestFlow()

        async def async_finish_flow(self, flow, result):
            """Raise AbortFlow."""
            raise data_entry_flow.AbortFlow("mock-reason", {"placeholder": "yo"})

    manager = FlowManager(hass)

    form = await manager.async_init("test")
    expect(form["type"]).to_equal(data_entry_flow.FlowResultType.ABORT)
    expect(form["reason"]).to_equal("mock-reason")
    expect(form["description_placeholders"]).to_equal({"placeholder": "yo"})


@test
async def init_unknown_flow(manager: MockFlowManager = Depends(manager)) -> None:
    """Test that UnknownFlow is raised when async_create_flow returns None."""

    with patch.object(manager, "async_create_flow", return_value=None):
        await _expect_raises_async(
            data_entry_flow.UnknownFlow, manager.async_init("test")
        )


@test
async def async_get_unknown_flow(manager: MockFlowManager = Depends(manager)) -> None:
    """Test that UnknownFlow is raised when async_get is called with a flow_id that does not exist."""

    _expect_raises_sync(
        data_entry_flow.UnknownFlow, manager.async_get, "does_not_exist"
    )


@test
async def move_to_unknown_step_raises_and_removes_from_in_progress(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test that moving to an unknown step raises and removes the flow from in progress."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 1

    await _expect_raises_async(
        data_entry_flow.UnknownStep,
        manager.async_init("test", context={"init_step": "does_not_exist"}),
    )

    expect(manager.async_progress()).to_equal([])


@test.cases(
    test.case(
        "external_step_done",
        result_type="async_external_step_done",
        params={"next_step_id": "does_not_exist"},
    ),
    test.case(
        "external_step",
        result_type="async_external_step",
        params={"step_id": "does_not_exist", "url": "blah"},
    ),
    test.case(
        "show_form",
        result_type="async_show_form",
        params={"step_id": "does_not_exist"},
    ),
    test.case(
        "show_menu",
        result_type="async_show_menu",
        params={"step_id": "does_not_exist", "menu_options": []},
    ),
    test.case(
        "show_progress_done",
        result_type="async_show_progress_done",
        params={"next_step_id": "does_not_exist"},
    ),
    test.case(
        "show_progress",
        result_type="async_show_progress",
        params={"step_id": "does_not_exist", "progress_action": ""},
    ),
)
async def next_step_unknown_step_raises_and_removes_from_in_progress(
    result_type: str,
    params: dict[str, str],
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test that moving to an unknown step raises and removes the flow from in progress."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 1

        async def async_step_init(self, user_input=None):
            return getattr(self, result_type)(**params)

    await _expect_raises_async(
        data_entry_flow.UnknownStep,
        manager.async_init("test", context={"init_step": "init"}),
    )

    expect(manager.async_progress()).to_equal([])


@test
async def configure_raises_unknown_flow_if_not_in_progress(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test configure raises UnknownFlow if the flow is not in progress."""
    await _expect_raises_async(
        data_entry_flow.UnknownFlow, manager.async_configure("wrong_flow_id")
    )


@test
async def manager_abort_raises_unknown_flow_if_not_in_progress(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test abort raises UnknownFlow if the flow is not in progress."""
    _expect_raises_sync(
        data_entry_flow.UnknownFlow, manager.async_abort, "wrong_flow_id"
    )


@test
async def manager_abort_calls_async_flow_removed(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test abort calling the async_flow_removed FlowManager method."""

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        async def async_step_init(self, user_input=None):
            return self.async_show_form(step_id="init")

    manager.async_flow_removed = Mock()
    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    manager.async_flow_removed.assert_not_called()

    manager.async_abort(result["flow_id"])
    manager.async_flow_removed.assert_called_once()

    expect(len(manager.async_progress())).to_equal(0)
    expect(len(manager.mock_created_entries)).to_equal(0)


@test.cases(
    test.case(
        "list_no_sort",
        menu_options=["target1", "target2"],
        sort=None,
        expect_sort=None,
    ),
    test.case(
        "dict_no_sort",
        menu_options={"target1": "Target 1", "target2": "Target 2"},
        sort=False,
        expect_sort=None,
    ),
    test.case(
        "list_sort",
        menu_options=["target2", "target1"],
        sort=True,
        expect_sort=True,
    ),
)
async def show_menu(
    menu_options: list[str] | dict[str, str],
    sort: bool | None,
    expect_sort: bool | None,
    hass: HomeAssistant = Depends(hass),
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test show menu."""
    manager.hass = hass

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 5
        data = None
        task_one_done = False

        async def async_step_init(self, user_input=None):
            return self.async_show_menu(
                step_id="init",
                menu_options=menu_options,
                description_placeholders={"name": "Paulus"},
                sort=sort,
            )

        async def async_step_target1(self, user_input=None):
            return self.async_show_form(step_id="target1")

        async def async_step_target2(self, user_input=None):
            return self.async_show_form(step_id="target2")

    result = await manager.async_init("test")
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.MENU)
    expect(result["menu_options"]).to_equal(menu_options)
    expect(result["description_placeholders"]).to_equal({"name": "Paulus"})
    expect(result.get("sort")).to_equal(expect_sort)
    expect(len(manager.async_progress())).to_equal(1)
    expect(len(manager.async_progress_by_handler("test"))).to_equal(1)
    expect(manager.async_get(result["flow_id"])["handler"]).to_equal("test")

    # Mimic picking a step
    result = await manager.async_configure(
        result["flow_id"], {"next_step_id": "target1"}
    )
    expect(result["type"]).to_equal(data_entry_flow.FlowResultType.FORM)
    expect(result["step_id"]).to_equal("target1")


@test
async def find_flows_by_init_data_type(
    manager: MockFlowManager = Depends(manager),
) -> None:
    """Test we can find flows by init data type."""

    @dataclasses.dataclass
    class BluetoothDiscoveryData:
        """Bluetooth Discovery data."""

        address: str

    @dataclasses.dataclass
    class WiFiDiscoveryData:
        """WiFi Discovery data."""

        address: str

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 1

        async def async_step_first(self, user_input=None):
            if user_input is not None:
                return await self.async_step_second()
            return self.async_show_form(step_id="first", data_schema=vol.Schema([str]))

        async def async_step_second(self, user_input=None):
            if user_input is not None:
                return self.async_create_entry(
                    title="Test Entry",
                    data={"init": self.init_data, "user": user_input},
                )
            return self.async_show_form(step_id="second", data_schema=vol.Schema([str]))

    bluetooth_data = BluetoothDiscoveryData("aa:bb:cc:dd:ee:ff")
    wifi_data = WiFiDiscoveryData("host")

    bluetooth_form = await manager.async_init(
        "test", context={"init_step": "first"}, data=bluetooth_data
    )
    await manager.async_init("test", context={"init_step": "first"}, data=wifi_data)

    expect(
        len(
            manager.async_progress_by_init_data_type(
                BluetoothDiscoveryData, lambda data: True
            )
        )
    ).to_equal(1)
    expect(
        len(
            manager.async_progress_by_init_data_type(
                BluetoothDiscoveryData,
                lambda data: bool(data.address == "aa:bb:cc:dd:ee:ff"),
            )
        )
    ).to_equal(1)
    expect(
        len(
            manager.async_progress_by_init_data_type(
                BluetoothDiscoveryData, lambda data: bool(data.address == "not it")
            )
        )
    ).to_equal(0)

    wifi_flows = manager.async_progress_by_init_data_type(
        WiFiDiscoveryData, lambda data: True
    )
    expect(len(wifi_flows)).to_equal(1)

    bluetooth_result = await manager.async_configure(
        bluetooth_form["flow_id"], ["SECOND-DATA"]
    )
    expect(bluetooth_result["type"]).to_equal(
        data_entry_flow.FlowResultType.CREATE_ENTRY
    )
    expect(len(manager.async_progress())).to_equal(1)
    expect(len(manager.mock_created_entries)).to_equal(1)
    result = manager.mock_created_entries[0]
    expect(result["handler"]).to_equal("test")
    expect(result["data"]).to_equal({"init": bluetooth_data, "user": ["SECOND-DATA"]})

    bluetooth_flows = manager.async_progress_by_init_data_type(
        BluetoothDiscoveryData, lambda data: True
    )
    expect(len(bluetooth_flows)).to_equal(0)

    wifi_flows = manager.async_progress_by_init_data_type(
        WiFiDiscoveryData, lambda data: True
    )
    expect(len(wifi_flows)).to_equal(1)

    manager.async_abort(wifi_flows[0]["flow_id"])

    wifi_flows = manager.async_progress_by_init_data_type(
        WiFiDiscoveryData, lambda data: True
    )
    expect(len(wifi_flows)).to_equal(0)
    expect(len(manager.async_progress())).to_equal(0)


@test
def section_in_serializer() -> None:
    """Test section with custom_serializer."""
    expect(
        cv.custom_serializer(
            data_entry_flow.section(
                vol.Schema(
                    {
                        vol.Optional("option_1", default=False): bool,
                        vol.Required("option_2"): int,
                    }
                ),
                {"collapsed": False},
            )
        )
    ).to_equal(
        {
            "expanded": True,
            "schema": [
                {
                    "default": False,
                    "name": "option_1",
                    "optional": True,
                    "required": False,
                    "type": "boolean",
                },
                {"name": "option_2", "required": True, "type": "integer"},
            ],
            "type": "expandable",
        }
    )


@test
def nested_section_in_serializer() -> None:
    """Test section with custom_serializer."""
    exc = _expect_raises_sync(
        ValueError,
        cv.custom_serializer,
        data_entry_flow.section(
            vol.Schema(
                {
                    vol.Required("section_1"): data_entry_flow.section(
                        vol.Schema(
                            {
                                vol.Optional("option_1", default=False): bool,
                                vol.Required("option_2"): int,
                            }
                        )
                    )
                }
            ),
            {"collapsed": False},
        ),
    )
    expect("Nesting expandable sections is not supported" in str(exc)).to_be_truthy()
