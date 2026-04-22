"""Test component/platform setup."""

import asyncio
import threading
from typing import Any
from unittest.mock import ANY, AsyncMock, Mock, patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config_entries, loader, setup
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_COMPONENT_LOADED, EVENT_HOMEASSISTANT_START
from homeassistant.core import (
    DOMAIN as HOMEASSISTANT_DOMAIN,
    CoreState,
    HomeAssistant,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, discovery, translation
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.issue_registry import IssueRegistry
from homeassistant.helpers.typing import ConfigType

from .common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    assert_setup_component,
    mock_integration,
    mock_platform,
)
from .hass_fixtures import LogCapture, caplog, freezer, hass, issue_registry


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_handlers() -> Any:
    """Mock config flows."""

    class MockFlowHandler(config_entries.ConfigFlow):
        """Define a mock flow handler."""

        VERSION = 1

    with patch.dict(config_entries.HANDLERS, {"comp": MockFlowHandler}):
        yield


@fixture
def enable_custom_integrations(hass: HomeAssistant = Depends(hass)) -> None:
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS)


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
async def validate_component_config(hass: HomeAssistant = Depends(hass)) -> None:
    """Test validating component configuration."""
    config_schema = vol.Schema({"comp_conf": {"hello": str}}, required=True)
    mock_integration(hass, MockModule("comp_conf", config_schema=config_schema))

    with assert_setup_component(0):
        expect(await setup.async_setup_component(hass, "comp_conf", {})).to_be_falsy()

    hass.data.pop(setup._DATA_SETUP)

    with assert_setup_component(0):
        expect(
            await setup.async_setup_component(hass, "comp_conf", {"comp_conf": None})
        ).to_be_falsy()

    hass.data.pop(setup._DATA_SETUP)

    with assert_setup_component(0):
        expect(
            await setup.async_setup_component(hass, "comp_conf", {"comp_conf": {}})
        ).to_be_falsy()

    hass.data.pop(setup._DATA_SETUP)

    with assert_setup_component(0):
        expect(
            await setup.async_setup_component(
                hass,
                "comp_conf",
                {"comp_conf": {"hello": "world", "invalid": "extra"}},
            )
        ).to_be_falsy()

    hass.data.pop(setup._DATA_SETUP)

    with assert_setup_component(1):
        expect(
            await setup.async_setup_component(
                hass, "comp_conf", {"comp_conf": {"hello": "world"}}
            )
        ).to_be_truthy()


@test
async def validate_platform_config(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test validating platform configuration."""
    platform_schema = cv.PLATFORM_SCHEMA.extend({"hello": str})
    platform_schema_base = cv.PLATFORM_SCHEMA_BASE.extend({})
    mock_integration(
        hass,
        MockModule("platform_conf", platform_schema_base=platform_schema_base),
    )
    mock_platform(
        hass,
        "whatever.platform_conf",
        MockPlatform(platform_schema=platform_schema),
    )

    with assert_setup_component(0):
        expect(
            await setup.async_setup_component(
                hass,
                "platform_conf",
                {"platform_conf": {"platform": "not_existing", "hello": "world"}},
            )
        ).to_be_truthy()

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("platform_conf")

    with assert_setup_component(1):
        expect(
            await setup.async_setup_component(
                hass,
                "platform_conf",
                {"platform_conf": {"platform": "whatever", "hello": "world"}},
            )
        ).to_be_truthy()

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("platform_conf")

    with assert_setup_component(1):
        expect(
            await setup.async_setup_component(
                hass,
                "platform_conf",
                {"platform_conf": [{"platform": "whatever", "hello": "world"}]},
            )
        ).to_be_truthy()

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("platform_conf")

    # Any falsey platform config will be ignored (None, {}, etc)
    with assert_setup_component(0) as config:
        expect(
            await setup.async_setup_component(
                hass, "platform_conf", {"platform_conf": None}
            )
        ).to_be_truthy()
        expect(hass.config.components).to_contain("platform_conf")
        expect(config["platform_conf"]).to_be_falsy()  # Empty

        expect(
            await setup.async_setup_component(
                hass, "platform_conf", {"platform_conf": {}}
            )
        ).to_be_truthy()
        expect(hass.config.components).to_contain("platform_conf")
        expect(config["platform_conf"]).to_be_falsy()  # Empty


@test
async def validate_platform_config_2(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test component PLATFORM_SCHEMA_BASE prio over PLATFORM_SCHEMA."""
    platform_schema = cv.PLATFORM_SCHEMA.extend({"hello": str})
    platform_schema_base = cv.PLATFORM_SCHEMA_BASE.extend({"hello": "world"})
    mock_integration(
        hass,
        MockModule(
            "platform_conf",
            platform_schema=platform_schema,
            platform_schema_base=platform_schema_base,
        ),
    )

    mock_platform(
        hass,
        "whatever.platform_conf",
        MockPlatform(platform_schema=platform_schema),
    )

    with assert_setup_component(1):
        expect(
            await setup.async_setup_component(
                hass,
                "platform_conf",
                {
                    # Pass
                    "platform_conf": {"platform": "whatever", "hello": "world"},
                    # Fail: key hello violates component platform_schema_base
                    "platform_conf 2": {"platform": "whatever", "hello": "there"},
                },
            )
        ).to_be_truthy()


@test
async def validate_platform_config_3(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test fallback to component PLATFORM_SCHEMA."""
    component_schema = cv.PLATFORM_SCHEMA_BASE.extend({"hello": str})
    platform_schema = cv.PLATFORM_SCHEMA.extend({"cheers": str, "hello": "world"})
    mock_integration(
        hass, MockModule("platform_conf", platform_schema=component_schema)
    )

    mock_platform(
        hass,
        "whatever.platform_conf",
        MockPlatform(platform_schema=platform_schema),
    )

    with assert_setup_component(1):
        expect(
            await setup.async_setup_component(
                hass,
                "platform_conf",
                {
                    # Pass
                    "platform_conf": {"platform": "whatever", "hello": "world"},
                    # Fail: key hello violates component platform_schema
                    "platform_conf 2": {"platform": "whatever", "hello": "there"},
                },
            )
        ).to_be_truthy()


@test
async def validate_platform_config_4(hass: HomeAssistant = Depends(hass)) -> None:
    """Test entity_namespace in PLATFORM_SCHEMA."""
    component_schema = cv.PLATFORM_SCHEMA_BASE
    platform_schema = cv.PLATFORM_SCHEMA
    mock_integration(
        hass,
        MockModule("platform_conf", platform_schema_base=component_schema),
    )

    mock_platform(
        hass,
        "whatever.platform_conf",
        MockPlatform(platform_schema=platform_schema),
    )

    with assert_setup_component(1):
        expect(
            await setup.async_setup_component(
                hass,
                "platform_conf",
                {
                    "platform_conf": {
                        # Pass: entity_namespace accepted by PLATFORM_SCHEMA
                        "platform": "whatever",
                        "entity_namespace": "yummy",
                    }
                },
            )
        ).to_be_truthy()

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("platform_conf")


@test
async def component_not_found(
    hass: HomeAssistant = Depends(hass),
    issue_registry: IssueRegistry = Depends(issue_registry),
) -> None:
    """setup_component should raise a repair issue if component doesn't exist."""
    MockConfigEntry(domain="non_existing").add_to_hass(hass)
    expect(await setup.async_setup_component(hass, "non_existing", {})).to_be(False)
    expect(issue_registry.issues).to_have_length(1)
    expect(issue_registry.issues).to_contain(
        (HOMEASSISTANT_DOMAIN, "integration_not_found.non_existing")
    )


@test
async def yaml_component_not_found(
    hass: HomeAssistant = Depends(hass),
    issue_registry: IssueRegistry = Depends(issue_registry),
) -> None:
    """setup_component should only raise an exception for missing config entry integrations."""
    expect(await setup.async_setup_component(hass, "non_existing", {})).to_be(False)
    expect(issue_registry.issues).to_have_length(0)
    expect(issue_registry.issues).not_.to_contain(
        (HOMEASSISTANT_DOMAIN, "integration_not_found.non_existing")
    )


@test
async def component_missing_not_raising_in_safe_mode(
    hass: HomeAssistant = Depends(hass),
    issue_registry: IssueRegistry = Depends(issue_registry),
) -> None:
    """setup_component should not raise an issue if component doesn't exist in safe."""
    MockConfigEntry(domain="non_existing").add_to_hass(hass)
    hass.config.safe_mode = True
    expect(await setup.async_setup_component(hass, "non_existing", {})).to_be(False)
    expect(issue_registry.issues).to_have_length(0)
    expect(issue_registry.issues).not_.to_contain(
        (HOMEASSISTANT_DOMAIN, "integration_not_found.non_existing")
    )


@test
async def component_not_double_initialized(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test we do not set up a component twice."""
    mock_setup = Mock(return_value=True)

    mock_integration(hass, MockModule("comp", setup=mock_setup))

    expect(await setup.async_setup_component(hass, "comp", {})).to_be_truthy()
    expect(mock_setup.called).to_be_truthy()

    mock_setup.reset_mock()

    expect(await setup.async_setup_component(hass, "comp", {})).to_be_truthy()
    expect(mock_setup.called).to_be_falsy()


@test
async def component_not_installed_if_requirement_fails(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Component setup should fail if requirement can't install."""
    hass.config.skip_pip = False
    mock_integration(hass, MockModule("comp", requirements=["package==0.0.1"]))

    with patch("homeassistant.util.package.install_package", return_value=False):
        expect(await setup.async_setup_component(hass, "comp", {})).to_be_falsy()

    expect(hass.config.components).not_.to_contain("comp")


@test
async def component_not_setup_twice_if_loaded_during_other_setup(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test component setup while waiting for lock is not set up twice."""
    result: list[int] = []

    async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Tracking Setup."""
        result.append(1)
        return True

    mock_integration(hass, MockModule("comp", async_setup=async_setup))

    def setup_component() -> None:
        """Set up the component."""
        setup.setup_component(hass, "comp", {})

    thread = threading.Thread(target=setup_component)
    thread.start()
    await setup.async_setup_component(hass, "comp", {})

    await hass.async_add_executor_job(thread.join)

    expect(result).to_have_length(1)


@test
async def component_not_setup_missing_dependencies(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test we do not set up a component if not all dependencies loaded."""
    deps = ["maybe_existing"]
    mock_integration(hass, MockModule("comp", dependencies=deps))

    expect(await setup.async_setup_component(hass, "comp", {})).to_be_falsy()
    expect(hass.config.components).not_.to_contain("comp")

    hass.data.pop(setup._DATA_SETUP)

    mock_integration(hass, MockModule("comp2", dependencies=deps))
    mock_integration(hass, MockModule("maybe_existing"))

    expect(await setup.async_setup_component(hass, "comp2", {})).to_be_truthy()


@test
async def component_not_setup_already_setup_dependencies(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test we do not set up component dependencies if they are already set up."""
    mock_integration(
        hass,
        MockModule(
            "comp",
            dependencies=["dep1"],
            partial_manifest={"after_dependencies": ["dep2"]},
        ),
    )
    mock_integration(hass, MockModule("dep1"))
    mock_integration(hass, MockModule("dep2"))

    setup.async_set_domains_to_be_loaded(hass, {"comp", "dep2"})

    hass.config.components.add("dep1")
    hass.config.components.add("dep2")

    with patch(
        "homeassistant.setup.async_setup_component",
        side_effect=setup.async_setup_component,
    ) as mock_setup:
        await mock_setup(hass, "comp", {})

    expect(mock_setup.call_count).to_equal(1)


@test
async def component_setup_dependencies_with_config_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_handlers: Any = Depends(mock_handlers),
) -> None:
    """Test we wait for a dependency with config entry."""
    calls: list[str] = []

    async def mock_async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        await asyncio.sleep(0)
        calls.append("entry")
        return True

    mock_integration(hass, MockModule("comp", async_setup_entry=mock_async_setup_entry))
    mock_platform(hass, "comp.config_flow", None)
    MockConfigEntry(domain="comp").add_to_hass(hass)

    async def mock_async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        calls.append("comp")
        return True

    mock_integration(
        hass,
        MockModule("comp2", dependencies=["comp"], async_setup=mock_async_setup),
    )
    mock_integration(
        hass,
        MockModule("comp3", dependencies=["comp"], async_setup=mock_async_setup),
    )

    await asyncio.gather(
        setup.async_setup_component(hass, "comp2", {}),
        setup.async_setup_component(hass, "comp3", {}),
    )

    expect(hass.config.components).to_contain("comp")
    expect(hass.config.components).to_contain("comp2")
    expect(hass.config.components).to_contain("comp3")

    expect(calls).to_equal(["entry", "comp", "comp"])


@test
async def component_failing_setup(hass: HomeAssistant = Depends(hass)) -> None:
    """Test component that fails setup."""
    mock_integration(hass, MockModule("comp", setup=lambda hass, config: False))

    expect(await setup.async_setup_component(hass, "comp", {})).to_be_falsy()
    expect(hass.config.components).not_.to_contain("comp")


@test
async def component_exception_setup(hass: HomeAssistant = Depends(hass)) -> None:
    """Test component that raises exception during setup."""
    domain = "comp"
    setup.async_set_domains_to_be_loaded(hass, {domain})

    def exception_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Raise exception."""
        raise Exception("fail!")  # noqa: TRY002

    mock_integration(hass, MockModule(domain, setup=exception_setup))

    expect(await setup.async_setup_component(hass, domain, {})).to_be_falsy()
    expect(hass.data[setup._DATA_SETUP]).to_contain(domain)
    expect(hass.data[setup._DATA_SETUP_DONE]).not_.to_contain(domain)
    expect(hass.config.components).not_.to_contain(domain)


@test
async def component_base_exception_setup(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test component that raises exception during setup."""
    domain = "comp"
    setup.async_set_domains_to_be_loaded(hass, {"comp"})

    def exception_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Raise exception."""
        raise BaseException("fail!")  # noqa: TRY002

    mock_integration(hass, MockModule("comp", setup=exception_setup))

    exc = await _expect_raises_async(
        BaseException, setup.async_setup_component(hass, "comp", {})
    )
    expect(str(exc)).to_equal("fail!")

    expect(hass.data[setup._DATA_SETUP]).to_contain(domain)
    expect(hass.data[setup._DATA_SETUP_DONE]).not_.to_contain(domain)
    expect(hass.config.components).not_.to_contain(domain)


@test
async def set_domains_to_be_loaded(hass: HomeAssistant = Depends(hass)) -> None:
    """Test async_set_domains_to_be_loaded."""
    domain_good = "comp_good"
    domain_bad = "comp_bad"
    domain_base_exception = "comp_base_exception"
    domain_exception = "comp_exception"
    domains = {domain_good, domain_bad, domain_exception, domain_base_exception}
    setup.async_set_domains_to_be_loaded(hass, domains)

    expect(set(hass.data[setup._DATA_SETUP_DONE])).to_equal(domains)
    setup_done = dict(hass.data[setup._DATA_SETUP_DONE])

    # Calling async_set_domains_to_be_loaded again should not create new futures
    setup.async_set_domains_to_be_loaded(hass, domains)
    expect(setup_done).to_equal(hass.data[setup._DATA_SETUP_DONE])

    def good_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Success."""
        return True

    def bad_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Fail."""
        return False

    def base_exception_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Raise exception."""
        raise BaseException("fail!")  # noqa: TRY002

    def exception_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Raise exception."""
        raise Exception("fail!")  # noqa: TRY002

    mock_integration(hass, MockModule(domain_good, setup=good_setup))
    mock_integration(hass, MockModule(domain_bad, setup=bad_setup))
    mock_integration(
        hass, MockModule(domain_base_exception, setup=base_exception_setup)
    )
    mock_integration(hass, MockModule(domain_exception, setup=exception_setup))

    # Set up the four components
    expect(await setup.async_setup_component(hass, domain_good, {})).to_be_truthy()
    expect(await setup.async_setup_component(hass, domain_bad, {})).to_be_falsy()
    expect(await setup.async_setup_component(hass, domain_exception, {})).to_be_falsy()
    await _expect_raises_async(
        BaseException,
        setup.async_setup_component(hass, domain_base_exception, {}),
    )

    # Check the result of the setup
    expect(hass.data[setup._DATA_SETUP_DONE]).to_be_falsy()
    expect(set(hass.data[setup._DATA_SETUP])).to_equal(
        {domain_bad, domain_exception, domain_base_exception}
    )
    expect(set(hass.config.components)).to_equal({domain_good})

    # Calling async_set_domains_to_be_loaded again should not create any new futures
    setup.async_set_domains_to_be_loaded(hass, domains)
    expect(hass.data[setup._DATA_SETUP_DONE]).to_be_falsy()


@test
async def component_setup_after_dependencies(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that after dependencies are set up before the component."""
    mock_integration(hass, MockModule("dep"))
    mock_integration(
        hass, MockModule("comp", partial_manifest={"after_dependencies": ["dep"]})
    )
    mock_integration(
        hass, MockModule("comp2", partial_manifest={"after_dependencies": ["dep"]})
    )

    setup.async_set_domains_to_be_loaded(hass, {"comp"})

    expect(await setup.async_setup_component(hass, "comp", {})).to_be_truthy()
    expect(hass.config.components).to_contain("comp")
    expect(hass.config.components).not_.to_contain("dep")

    setup.async_set_domains_to_be_loaded(hass, {"comp2", "dep"})

    expect(await setup.async_setup_component(hass, "comp2", {})).to_be_truthy()
    expect(hass.config.components).to_contain("comp2")
    expect(hass.config.components).to_contain("dep")


@test
async def component_setup_with_validation_and_dependency(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test all config is passed to dependencies."""

    def config_check_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Test that config is passed in."""
        if config.get("comp_a", {}).get("valid", False):
            return True
        raise Exception(f"Config not passed in: {config}")  # noqa: TRY002

    platform = MockPlatform()

    mock_integration(hass, MockModule("comp_a", setup=config_check_setup))
    mock_integration(
        hass,
        MockModule("platform_a", setup=config_check_setup, dependencies=["comp_a"]),
    )

    mock_platform(hass, "platform_a.switch", platform)

    await setup.async_setup_component(
        hass,
        "switch",
        {"comp_a": {"valid": True}, "switch": {"platform": "platform_a"}},
    )
    await hass.async_block_till_done()
    expect(hass.config.components).to_contain("comp_a")


@test
async def platform_specific_config_validation(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test platform that specifies config."""
    platform_schema = cv.PLATFORM_SCHEMA.extend(
        {"valid": True}, extra=vol.PREVENT_EXTRA
    )

    mock_setup = Mock(spec_set=True)

    mock_platform(
        hass,
        "platform_a.switch",
        MockPlatform(platform_schema=platform_schema, setup_platform=mock_setup),
    )

    with (
        assert_setup_component(0, "switch"),
        patch("homeassistant.setup.async_notify_setup_error") as mock_notify,
    ):
        expect(
            await setup.async_setup_component(
                hass,
                "switch",
                {"switch": {"platform": "platform_a", "invalid": True}},
            )
        ).to_be_truthy()
        await hass.async_block_till_done()
        expect(mock_setup.call_count).to_equal(0)
        expect(mock_notify.mock_calls).to_have_length(1)

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("switch")

    with (
        assert_setup_component(0),
        patch("homeassistant.setup.async_notify_setup_error") as mock_notify,
    ):
        expect(
            await setup.async_setup_component(
                hass,
                "switch",
                {
                    "switch": {
                        "platform": "platform_a",
                        "valid": True,
                        "invalid_extra": True,
                    }
                },
            )
        ).to_be_truthy()
        await hass.async_block_till_done()
        expect(mock_setup.call_count).to_equal(0)
        expect(mock_notify.mock_calls).to_have_length(1)

    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("switch")

    with (
        assert_setup_component(1, "switch"),
        patch("homeassistant.setup.async_notify_setup_error") as mock_notify,
    ):
        expect(
            await setup.async_setup_component(
                hass,
                "switch",
                {"switch": {"platform": "platform_a", "valid": True}},
            )
        ).to_be_truthy()
        await hass.async_block_till_done()
        expect(mock_setup.call_count).to_equal(1)
        expect(mock_notify.mock_calls).to_have_length(0)


@test
async def disable_component_if_invalid_return(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test disabling component if invalid return."""
    mock_integration(
        hass, MockModule("disabled_component", setup=lambda hass, config: None)
    )

    expect(
        await setup.async_setup_component(hass, "disabled_component", {})
    ).to_be_falsy()
    expect(hass.config.components).not_.to_contain("disabled_component")

    hass.data.pop(setup._DATA_SETUP)
    mock_integration(
        hass,
        MockModule("disabled_component", setup=lambda hass, config: False),
    )

    expect(
        await setup.async_setup_component(hass, "disabled_component", {})
    ).to_be_falsy()
    expect(hass.config.components).not_.to_contain("disabled_component")

    hass.data.pop(setup._DATA_SETUP)
    mock_integration(
        hass, MockModule("disabled_component", setup=lambda hass, config: True)
    )

    expect(
        await setup.async_setup_component(hass, "disabled_component", {})
    ).to_be_truthy()
    expect(hass.config.components).to_contain("disabled_component")


@test
async def all_work_done_before_start(hass: HomeAssistant = Depends(hass)) -> None:
    """Test all init work done till start."""
    call_order: list[int] = []

    async def component1_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up mock component."""
        await discovery.async_discover(
            hass, "test_component2", {}, "test_component2", {}
        )
        await discovery.async_discover(
            hass, "test_component3", {}, "test_component3", {}
        )
        return True

    def component_track_setup(hass: HomeAssistant, config: ConfigType) -> bool:
        """Set up mock component."""
        call_order.append(1)
        return True

    mock_integration(hass, MockModule("test_component1", async_setup=component1_setup))

    mock_integration(hass, MockModule("test_component2", setup=component_track_setup))

    mock_integration(hass, MockModule("test_component3", setup=component_track_setup))

    @callback
    def track_start(event):
        """Track start event."""
        call_order.append(2)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, track_start)

    hass.add_job(setup.async_setup_component(hass, "test_component1", {}))
    await hass.async_block_till_done()
    await hass.async_start()
    expect(call_order).to_equal([1, 1, 2])


@test
async def component_warn_slow_setup(hass: HomeAssistant = Depends(hass)) -> None:
    """Warn we log when a component setup takes a long time."""
    mock_integration(hass, MockModule("test_component1"))
    with patch.object(hass.loop, "call_later") as mock_call:
        result = await setup.async_setup_component(hass, "test_component1", {})
        expect(result).to_be_truthy()
        expect(mock_call.called).to_be_truthy()

        expect(mock_call.mock_calls).to_have_length(3)
        timeout, logger_method = mock_call.mock_calls[0][1][:2]

        expect(timeout).to_equal(setup.SLOW_SETUP_WARNING)
        expect(logger_method).to_equal(setup._LOGGER.warning)

        expect(mock_call().cancel.called).to_be_truthy()


@test
async def platform_no_warn_slow(hass: HomeAssistant = Depends(hass)) -> None:
    """Do not warn for long entity setup time."""
    mock_integration(
        hass, MockModule("test_component1", platform_schema=cv.PLATFORM_SCHEMA)
    )
    with patch.object(hass.loop, "call_later") as mock_call:
        result = await setup.async_setup_component(hass, "test_component1", {})
        expect(result).to_be_truthy()
        expect(mock_call.mock_calls).to_have_length(0)


@test
async def platform_error_slow_setup(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Don't block startup more than SLOW_SETUP_MAX_WAIT."""

    with patch.object(setup, "SLOW_SETUP_MAX_WAIT", 0.1):
        called: list[int] = []

        async def async_setup(*args):
            """Tracking Setup."""
            called.append(1)
            await asyncio.sleep(2)

        mock_integration(hass, MockModule("test_component1", async_setup=async_setup))
        result = await setup.async_setup_component(hass, "test_component1", {})
        expect(called).to_have_length(1)
        expect(result).to_be_falsy()
        expect(caplog.text).to_contain(
            "'test_component1' is taking longer than 0.1 seconds"
        )


@test
async def when_setup_already_loaded(hass: HomeAssistant = Depends(hass)) -> None:
    """Test when setup."""
    calls: list[str] = []

    async def mock_callback(hass: HomeAssistant, component: str) -> None:
        """Mock callback."""
        calls.append(component)

    setup.async_when_setup(hass, "test", mock_callback)
    await hass.async_block_till_done()
    expect(calls).to_equal([])

    hass.config.components.add("test")
    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {"component": "test"})
    await hass.async_block_till_done()
    expect(calls).to_equal(["test"])

    # Event listener should be gone
    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {"component": "test"})
    await hass.async_block_till_done()
    expect(calls).to_equal(["test"])

    # Should be called right away
    setup.async_when_setup(hass, "test", mock_callback)
    await hass.async_block_till_done()
    expect(calls).to_equal(["test", "test"])


@test
async def async_when_setup_or_start_already_loaded(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test when setup or start."""
    calls: list[str] = []

    async def mock_callback(hass: HomeAssistant, component: str) -> None:
        """Mock callback."""
        calls.append(component)

    setup.async_when_setup_or_start(hass, "test", mock_callback)
    await hass.async_block_till_done()
    expect(calls).to_equal([])

    hass.config.components.add("test")
    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {"component": "test"})
    await hass.async_block_till_done()
    expect(calls).to_equal(["test"])

    # Event listener should be gone
    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {"component": "test"})
    await hass.async_block_till_done()
    expect(calls).to_equal(["test"])

    # Should be called right away
    setup.async_when_setup_or_start(hass, "test", mock_callback)
    await hass.async_block_till_done()
    expect(calls).to_equal(["test", "test"])

    setup.async_when_setup_or_start(hass, "not_loaded", mock_callback)
    await hass.async_block_till_done()
    expect(calls).to_equal(["test", "test"])
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    expect(calls).to_equal(["test", "test", "not_loaded"])


@test
async def setup_import_blows_up(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that we handle it correctly when importing integration blows up."""
    with patch(
        "homeassistant.loader.Integration.async_get_component", side_effect=ImportError
    ):
        expect(await setup.async_setup_component(hass, "sun", {})).to_be_falsy()


@test
async def parallel_entry_setup(
    hass: HomeAssistant = Depends(hass),
    _mock_handlers: Any = Depends(mock_handlers),
) -> None:
    """Test config entries are set up in parallel."""
    MockConfigEntry(domain="comp", data={"value": 1}).add_to_hass(hass)
    MockConfigEntry(domain="comp", data={"value": 2}).add_to_hass(hass)

    calls: list[int] = []

    async def mock_async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Mock setting up an entry."""
        calls.append(entry.data["value"])
        await asyncio.sleep(0)
        calls.append(entry.data["value"])
        return True

    mock_integration(
        hass,
        MockModule(
            "comp",
            async_setup_entry=mock_async_setup_entry,
        ),
    )
    mock_platform(hass, "comp.config_flow", None)
    await setup.async_setup_component(hass, "comp", {})

    expect(calls).to_equal([1, 2, 1, 2])


@test
async def integration_disabled(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test we can disable an integration."""
    disabled_reason = "Dependency contains code that breaks Home Assistant"
    mock_integration(
        hass,
        MockModule("test_component1", partial_manifest={"disabled": disabled_reason}),
    )
    result = await setup.async_setup_component(hass, "test_component1", {})
    expect(result).to_be_falsy()
    expect(caplog.text).to_contain(disabled_reason)


@test
async def integration_logs_is_custom(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test we highlight it's a custom component when errors happen."""
    mock_integration(
        hass,
        MockModule("test_component1"),
        built_in=False,
    )
    with patch(
        "homeassistant.setup.async_process_deps_reqs",
        side_effect=HomeAssistantError("Boom"),
    ):
        result = await setup.async_setup_component(hass, "test_component1", {})
    expect(result).to_be_falsy()
    expect(caplog.text).to_contain(
        "Setup failed for custom integration 'test_component1': Boom"
    )


@test
async def async_get_loaded_integrations(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we can enumerate loaded integrations."""
    hass.config.components.add("notbase")
    hass.config.components.add("switch")
    hass.config.components.add("notbase.switch")
    hass.config.components.add("myintegration")
    hass.config.components.add("device_tracker")
    hass.config.components.add("other.device_tracker")
    hass.config.components.add("myintegration.light")
    expect(setup.async_get_loaded_integrations(hass)).to_equal(
        {"other", "switch", "notbase", "myintegration", "device_tracker"}
    )


@test
async def integration_no_setup(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test we fail integration setup without setup functions."""
    mock_integration(
        hass,
        MockModule("test_integration_without_setup", setup=False),
    )
    result = await setup.async_setup_component(
        hass, "test_integration_without_setup", {}
    )
    expect(result).to_be_falsy()
    expect(caplog.text).to_contain("No setup or config entry setup function defined")


@test
async def integration_only_setup_entry(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we have an integration with only a setup entry method."""
    mock_integration(
        hass,
        MockModule(
            "test_integration_only_entry",
            setup=False,
            async_setup_entry=AsyncMock(return_value=True),
        ),
    )
    expect(
        await setup.async_setup_component(hass, "test_integration_only_entry", {})
    ).to_be_truthy()


@test
async def async_start_setup_running(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setup started context manager does nothing when running."""
    expect(hass.state).to_be(CoreState.running)
    setup_started = hass.data.setdefault(setup._DATA_SETUP_STARTED, {})

    with setup.async_start_setup(
        hass, integration="august", phase=setup.SetupPhases.SETUP
    ):
        expect(setup_started).to_be_falsy()


@test
async def async_start_setup_config_entry(
    hass: HomeAssistant = Depends(hass),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test setup started keeps track of setup times with a config entry."""
    hass.set_state(CoreState.not_running)
    setup_started = hass.data.setdefault(setup._DATA_SETUP_STARTED, {})
    setup_time = setup._setup_times(hass)

    with setup.async_start_setup(
        hass, integration="august", phase=setup.SetupPhases.SETUP
    ):
        expect(isinstance(setup_started[("august", None)], float)).to_be_truthy()

    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_SETUP,
    ):
        expect(isinstance(setup_started[("august", "entry_id")], float)).to_be_truthy()
        with setup.async_start_setup(
            hass,
            integration="august",
            group="entry_id",
            phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
        ):
            expect(
                isinstance(setup_started[("august", "entry_id")], float)
            ).to_be_truthy()

    # CONFIG_ENTRY_PLATFORM_SETUP inside of CONFIG_ENTRY_SETUP should not be tracked
    expect(setup_time["august"]).to_equal(
        {
            None: {setup.SetupPhases.SETUP: ANY},
            "entry_id": {setup.SetupPhases.CONFIG_ENTRY_SETUP: ANY},
        }
    )
    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
    ):
        expect(isinstance(setup_started[("august", "entry_id")], float)).to_be_truthy()

    # Platforms outside of CONFIG_ENTRY_SETUP should be tracked.
    # This simulates a late platform forward.
    expect(setup_time["august"]).to_equal(
        {
            None: {setup.SetupPhases.SETUP: ANY},
            "entry_id": {
                setup.SetupPhases.CONFIG_ENTRY_SETUP: ANY,
                setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP: ANY,
            },
        }
    )

    shorter_time = setup_time["august"]["entry_id"][
        setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP
    ]
    # Setup another platform, but make it take longer
    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
    ):
        freezer.tick(10)
        expect(isinstance(setup_started[("august", "entry_id")], float)).to_be_truthy()

    longer_time = setup_time["august"]["entry_id"][
        setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP
    ]
    expect(longer_time > shorter_time).to_be_truthy()
    # Setup another platform, but make it take shorter
    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
    ):
        expect(isinstance(setup_started[("august", "entry_id")], float)).to_be_truthy()

    # Ensure we keep the longest time
    expect(
        setup_time["august"]["entry_id"][setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP]
    ).to_equal(longer_time)

    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id2",
        phase=setup.SetupPhases.CONFIG_ENTRY_SETUP,
    ):
        expect(isinstance(setup_started[("august", "entry_id2")], float)).to_be_truthy()
        # We wrap places where we wait for other components
        # or the import of a module with async_freeze_setup
        # so we can subtract the time waited from the total setup time
        with setup.async_pause_setup(hass, setup.SetupPhases.WAIT_BASE_PLATFORM_SETUP):
            await asyncio.sleep(0)

    # Wait time should be added if freeze_setup is used
    expect(setup_time["august"]).to_equal(
        {
            None: {setup.SetupPhases.SETUP: ANY},
            "entry_id": {
                setup.SetupPhases.CONFIG_ENTRY_SETUP: ANY,
                setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP: ANY,
            },
            "entry_id2": {
                setup.SetupPhases.CONFIG_ENTRY_SETUP: ANY,
                setup.SetupPhases.WAIT_BASE_PLATFORM_SETUP: ANY,
            },
        }
    )


@test
async def async_start_setup_config_entry_late_platform(
    hass: HomeAssistant = Depends(hass),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test setup started tracks config entry time with a late platform load."""
    hass.set_state(CoreState.not_running)
    setup_started = hass.data.setdefault(setup._DATA_SETUP_STARTED, {})
    setup_time = setup._setup_times(hass)

    with setup.async_start_setup(
        hass, integration="august", phase=setup.SetupPhases.SETUP
    ):
        freezer.tick(10)
        expect(isinstance(setup_started[("august", None)], float)).to_be_truthy()

    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_SETUP,
    ):
        expect(isinstance(setup_started[("august", "entry_id")], float)).to_be_truthy()

        @callback
        def async_late_platform_load():
            with setup.async_pause_setup(hass, setup.SetupPhases.WAIT_IMPORT_PLATFORMS):
                freezer.tick(100)
            with setup.async_start_setup(
                hass,
                integration="august",
                group="entry_id",
                phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
            ):
                freezer.tick(20)
                expect(
                    isinstance(setup_started[("august", "entry_id")], float)
                ).to_be_truthy()

        disconnect = async_dispatcher_connect(
            hass, "late_platform_load_test", async_late_platform_load
        )

    # Dispatch a late platform load
    async_dispatcher_send(hass, "late_platform_load_test")
    disconnect()

    # CONFIG_ENTRY_PLATFORM_SETUP is late dispatched, so it should be tracked
    # but any waiting time should not be because it's blocking the setup
    expect(setup_time["august"]).to_equal(
        {
            None: {setup.SetupPhases.SETUP: 10.0},
            "entry_id": {
                setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP: 20.0,
                setup.SetupPhases.CONFIG_ENTRY_SETUP: 0.0,
            },
        }
    )


@test
async def async_start_setup_config_entry_platform_wait(
    hass: HomeAssistant = Depends(hass),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Test setup started tracks wait time when a platform loads inside of config entry setup."""
    hass.set_state(CoreState.not_running)
    setup_started = hass.data.setdefault(setup._DATA_SETUP_STARTED, {})
    setup_time = setup._setup_times(hass)

    with setup.async_start_setup(
        hass, integration="august", phase=setup.SetupPhases.SETUP
    ):
        freezer.tick(10)
        expect(isinstance(setup_started[("august", None)], float)).to_be_truthy()

    with setup.async_start_setup(
        hass,
        integration="august",
        group="entry_id",
        phase=setup.SetupPhases.CONFIG_ENTRY_SETUP,
    ):
        expect(isinstance(setup_started[("august", "entry_id")], float)).to_be_truthy()

        with setup.async_pause_setup(hass, setup.SetupPhases.WAIT_IMPORT_PLATFORMS):
            freezer.tick(100)
        with setup.async_start_setup(
            hass,
            integration="august",
            group="entry_id",
            phase=setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP,
        ):
            freezer.tick(20)
            expect(
                isinstance(setup_started[("august", "entry_id")], float)
            ).to_be_truthy()

    # CONFIG_ENTRY_PLATFORM_SETUP is run inside of CONFIG_ENTRY_SETUP, so it should not
    # be tracked, but any wait time should still be tracked because its blocking the setup
    expect(setup_time["august"]).to_equal(
        {
            None: {setup.SetupPhases.SETUP: 10.0},
            "entry_id": {
                setup.SetupPhases.WAIT_IMPORT_PLATFORMS: -100.0,
                setup.SetupPhases.CONFIG_ENTRY_SETUP: 120.0,
            },
        }
    )


@test
async def async_start_setup_top_level_yaml(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test setup started context manager keeps track of setup times with modern yaml."""
    hass.set_state(CoreState.not_running)
    setup_started = hass.data.setdefault(setup._DATA_SETUP_STARTED, {})
    setup_time = setup._setup_times(hass)

    with setup.async_start_setup(
        hass, integration="command_line", phase=setup.SetupPhases.SETUP
    ):
        expect(isinstance(setup_started[("command_line", None)], float)).to_be_truthy()

    expect(setup_time["command_line"]).to_equal({None: {setup.SetupPhases.SETUP: ANY}})


@test
async def async_start_setup_platform_integration(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test setup started keeps track of setup times a platform integration."""
    hass.set_state(CoreState.not_running)
    setup_started = hass.data.setdefault(setup._DATA_SETUP_STARTED, {})
    setup_time = setup._setup_times(hass)

    with setup.async_start_setup(
        hass, integration="sensor", phase=setup.SetupPhases.SETUP
    ):
        expect(isinstance(setup_started[("sensor", None)], float)).to_be_truthy()

    # Platform integration setups happen in another task
    with setup.async_start_setup(
        hass,
        integration="filter",
        group="123456",
        phase=setup.SetupPhases.PLATFORM_SETUP,
    ):
        expect(isinstance(setup_started[("filter", "123456")], float)).to_be_truthy()

    expect(setup_time["sensor"]).to_equal({None: {setup.SetupPhases.SETUP: ANY}})
    expect(setup_time["filter"]).to_equal(
        {"123456": {setup.SetupPhases.PLATFORM_SETUP: ANY}}
    )


@test
async def async_start_setup_legacy_platform_integration(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test setup started keeps track of setup times for a legacy platform integration."""
    hass.set_state(CoreState.not_running)
    setup_started = hass.data.setdefault(setup._DATA_SETUP_STARTED, {})
    setup_time = setup._setup_times(hass)

    with setup.async_start_setup(
        hass, integration="notify", phase=setup.SetupPhases.SETUP
    ):
        expect(isinstance(setup_started[("notify", None)], float)).to_be_truthy()

    with setup.async_start_setup(
        hass,
        integration="legacy_notify_integration",
        group="123456",
        phase=setup.SetupPhases.PLATFORM_SETUP,
    ):
        expect(
            isinstance(setup_started[("legacy_notify_integration", "123456")], float)
        ).to_be_truthy()

    expect(setup_time["notify"]).to_equal({None: {setup.SetupPhases.SETUP: ANY}})
    expect(setup_time["legacy_notify_integration"]).to_equal(
        {"123456": {setup.SetupPhases.PLATFORM_SETUP: ANY}}
    )


@test
async def async_start_setup_simple_integration_end_to_end(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test end to end timings for a simple integration with no platforms."""
    hass.set_state(CoreState.not_running)
    mock_integration(
        hass,
        MockModule(
            "test_integration_no_platforms",
            setup=False,
            async_setup_entry=AsyncMock(return_value=True),
        ),
    )
    expect(
        await setup.async_setup_component(hass, "test_integration_no_platforms", {})
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(setup.async_get_setup_timings(hass)).to_equal(
        {"test_integration_no_platforms": ANY}
    )


@test
async def async_get_setup_timings(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we can get the setup timings from the setup time data."""
    setup_time = setup._setup_times(hass)
    # Mock setup time data
    setup_time.update(
        {
            "august": {
                None: {setup.SetupPhases.SETUP: 1},
                "entry_id": {
                    setup.SetupPhases.CONFIG_ENTRY_SETUP: 1,
                    setup.SetupPhases.CONFIG_ENTRY_PLATFORM_SETUP: 4,
                },
                "entry_id2": {
                    setup.SetupPhases.CONFIG_ENTRY_SETUP: 7,
                    setup.SetupPhases.WAIT_BASE_PLATFORM_SETUP: -5,
                },
            },
            "notify": {
                None: {
                    setup.SetupPhases.SETUP: 2,
                },
            },
            "legacy_notify_integration": {
                "123456": {
                    setup.SetupPhases.PLATFORM_SETUP: 3,
                },
            },
            "sensor": {
                None: {
                    setup.SetupPhases.SETUP: 1,
                },
            },
            "filter": {
                "123456": {
                    setup.SetupPhases.PLATFORM_SETUP: 2,
                },
            },
        }
    )
    expect(setup.async_get_setup_timings(hass)).to_equal(
        {
            "august": 6,
            "notify": 2,
            "legacy_notify_integration": 3,
            "sensor": 1,
            "filter": 2,
        }
    )
    expect(setup.async_get_domain_setup_times(hass, "filter")).to_equal(
        {"123456": {setup.SetupPhases.PLATFORM_SETUP: 2}}
    )


@test
async def setup_config_entry_from_yaml(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test attempting to setup an integration which only supports config_entries."""
    expected_warning = (
        "The 'test_integration_only_entry' integration does not support YAML setup, "
        "please remove it from your configuration"
    )

    mock_integration(
        hass,
        MockModule(
            "test_integration_only_entry",
            setup=False,
            async_setup_entry=AsyncMock(return_value=True),
        ),
    )

    expect(
        await setup.async_setup_component(hass, "test_integration_only_entry", {})
    ).to_be_truthy()
    expect(caplog.text).not_.to_contain(expected_warning)
    caplog.clear()
    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("test_integration_only_entry")

    # There should be a warning, but setup should not fail
    expect(
        await setup.async_setup_component(
            hass, "test_integration_only_entry", {"test_integration_only_entry": None}
        )
    ).to_be_truthy()
    expect(caplog.text).to_contain(expected_warning)
    caplog.clear()
    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("test_integration_only_entry")

    # There should be a warning, but setup should not fail
    expect(
        await setup.async_setup_component(
            hass, "test_integration_only_entry", {"test_integration_only_entry": {}}
        )
    ).to_be_truthy()
    expect(caplog.text).to_contain(expected_warning)
    caplog.clear()
    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("test_integration_only_entry")

    # There should be a warning, but setup should not fail
    expect(
        await setup.async_setup_component(
            hass,
            "test_integration_only_entry",
            {"test_integration_only_entry": {"hello": "world"}},
        )
    ).to_be_truthy()
    expect(caplog.text).to_contain(expected_warning)
    caplog.clear()
    hass.data.pop(setup._DATA_SETUP)
    hass.config.components.remove("test_integration_only_entry")


@test
async def loading_component_loads_translations(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test that loading a component loads translations."""
    expect(translation.async_translations_loaded(hass, {"comp"})).to_be(False)
    mock_setup = Mock(return_value=True)

    mock_integration(hass, MockModule("comp", setup=mock_setup))
    integration = await loader.async_get_integration(hass, "comp")
    with patch.object(integration, "has_translations", True):
        expect(await setup.async_setup_component(hass, "comp", {})).to_be_truthy()
    expect(mock_setup.called).to_be_truthy()
    expect(translation.async_translations_loaded(hass, {"comp"})).to_be(True)


@test
async def importing_integration_in_executor(
    hass: HomeAssistant = Depends(hass),
    _enable_custom_integrations: None = Depends(enable_custom_integrations),
) -> None:
    """Test we can import an integration in an executor."""
    expect(
        await setup.async_setup_component(hass, "test_package_loaded_executor", {})
    ).to_be_truthy()
    expect(
        await setup.async_setup_component(hass, "test_package_loaded_executor", {})
    ).to_be_truthy()
    await hass.async_block_till_done()


@test
async def async_prepare_setup_platform(
    hass: HomeAssistant = Depends(hass),
    caplog: LogCapture = Depends(caplog),
    _enable_custom_integrations: None = Depends(enable_custom_integrations),
) -> None:
    """Test we can prepare a platform setup."""
    integration = await loader.async_get_integration(hass, "test")
    with patch.object(
        integration, "async_get_component", side_effect=ImportError("test is broken")
    ):
        expect(
            await setup.async_prepare_setup_platform(hass, {}, "config", "test")
        ).to_be(None)

    expect(caplog.text).to_contain("test is broken")

    caplog.clear()
    # There is no actual config platform for this integration
    expect(await setup.async_prepare_setup_platform(hass, {}, "config", "test")).to_be(
        None
    )
    expect(caplog.text).to_contain("No module named 'custom_components.test.config'")

    button_platform = (
        await setup.async_prepare_setup_platform(hass, {}, "button", "test") is None
    )
    expect(button_platform).not_.to_be(None)


@test
async def async_wait_component(hass: HomeAssistant = Depends(hass)) -> None:
    """Test async_wait_component."""
    setup_stall = asyncio.Event()
    setup_started = asyncio.Event()

    async def mock_setup(hass: HomeAssistant, _) -> bool:
        setup_started.set()
        await setup_stall.wait()
        return True

    mock_integration(hass, MockModule("test", async_setup=mock_setup))

    # The integration not loaded, and is also not scheduled to load
    expect(await setup.async_wait_component(hass, "test")).to_be(False)

    # Mark the component as scheduled to be loaded
    setup.async_set_domains_to_be_loaded(hass, {"test"})

    # Start loading the component, including its config entries
    hass.async_create_task(setup.async_setup_component(hass, "test", {}))
    await setup_started.wait()

    # The component is not yet loaded
    expect(hass.config.components).not_.to_contain("test")

    # Allow setup to proceed
    setup_stall.set()

    # The component is scheduled to load, this will block until the config entry is loaded
    expect(await setup.async_wait_component(hass, "test")).to_be(True)

    # The component has been loaded
    expect(hass.config.components).to_contain("test")

    # Clear the event, then call again to make sure we don't block
    setup_stall.clear()
    expect(await setup.async_wait_component(hass, "test")).to_be(True)
