"""Test the python_script component."""

import logging
from unittest.mock import mock_open, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.python_script import DOMAIN, FOLDER, execute
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.service import async_get_all_descriptions
from homeassistant.setup import async_setup_component

from tests.common import patch_yaml_files
from tests.hass_fixtures import (
    caplog as caplog_fixture,
    hass as hass_fixture,
    LogCapture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Trigger executor for async fixtures."""
    return 0


@test
async def setup(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can discover scripts."""
    scripts = [
        "/some/config/dir/python_scripts/hello.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]
    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts
        ),
    ):
        res = await async_setup_component(hass, "python_script", {})

    expect(res).to_be_truthy()
    expect(hass.services.has_service("python_script", "hello")).to_be_truthy()
    expect(hass.services.has_service("python_script", "world_beer")).to_be_truthy()

    with (
        patch(
            "homeassistant.components.python_script.open",
            mock_open(read_data="fake source"),
            create=True,
        ),
        patch("homeassistant.components.python_script.execute") as mock_ex,
    ):
        await hass.services.async_call(
            "python_script", "hello", {"some": "data"}, blocking=True
        )

    expect(len(mock_ex.mock_calls)).to_be(1)
    test_hass, script, source, data = mock_ex.mock_calls[0][1]

    expect(test_hass).to_be(hass)
    expect(script).to_equal("hello.py")
    expect(source).to_equal("fake source")
    expect(data).to_equal({"some": "data"})


@test
async def setup_fails_on_no_dir(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we fail setup when no dir found."""
    with patch(
        "homeassistant.components.python_script.os.path.isdir", return_value=False
    ):
        res = await async_setup_component(hass, "python_script", {})

    expect(res).to_be_falsy()
    expect(
        "Folder python_scripts not found in configuration folder" in caplog.text
    ).to_be(True)


@test
async def execute_with_data(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test executing a script."""
    caplog.set_level(logging.WARNING)
    source = """
hass.states.set('test.entity', data.get('name', 'not set'))
    """

    hass.async_add_executor_job(execute, hass, "test.py", source, {"name": "paulus"})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(hass.states.is_state("test.entity", "paulus")).to_be(True)

    expect(caplog.text).to_be("")


@test
async def execute_warns_print(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test print triggers warning."""
    caplog.set_level(logging.WARNING)
    source = """
print("This triggers warning.")
    """

    hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect("Don't use print() inside scripts." in caplog.text).to_be(True)


@test
async def execute_logging(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test logging works."""
    caplog.set_level(logging.INFO)
    source = """
logger.info('Logging from inside script')
    """

    hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect("Logging from inside script" in caplog.text).to_be(True)


@test
async def execute_compile_error(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)
    source = """
this is not valid Python
    """

    hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect("Error loading script test.py" in caplog.text).to_be(True)


@test
async def execute_runtime_error(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)
    source = """
raise Exception('boom')
    """

    await hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect("Error executing script" in caplog.text).to_be(True)


@test
async def execute_runtime_error_with_response(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test compile error logs error."""
    source = """
raise Exception('boom')
    """

    task = hass.async_add_executor_job(execute, hass, "test.py", source, {}, True)
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(type(task.exception()) is HomeAssistantError).to_be(True)
    expect(
        "Error executing script (Exception): boom" in str(task.exception())
    ).to_be(True)


@test
async def accessing_async_methods(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)
    source = """
hass.async_stop()
    """

    await hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done()

    expect("Not allowed to access async methods" in caplog.text).to_be(True)


@test
async def accessing_async_methods_with_response(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test compile error logs error."""
    source = """
hass.async_stop()
    """

    task = hass.async_add_executor_job(execute, hass, "test.py", source, {}, True)
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(type(task.exception()) is ServiceValidationError).to_be(True)
    expect("Not allowed to access async methods" in str(task.exception())).to_be(True)


@test
async def using_complex_structures(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that dicts and lists work."""
    caplog.set_level(logging.INFO)
    source = """
mydict = {"a": 1, "b": 2}
mylist = [1, 2, 3, 4]
logger.info('Logging from inside script: %s %s' % (mydict["a"], mylist[2]))
    """

    await hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done()

    expect("Logging from inside script: 1 3" in caplog.text).to_be(True)


@test
async def accessing_forbidden_methods(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)

    cases = {
        "hass.stop()": "HomeAssistant.stop",
        "dt_util.set_default_time_zone()": "module.set_default_time_zone",
        "datetime.non_existing": "module.non_existing",
        "time.tzset()": "TimeWrapper.tzset",
    }
    for source, name in cases.items():
        caplog.clear()
        await hass.async_add_executor_job(execute, hass, "test.py", source, {})
        await hass.async_block_till_done()
        expect(f"Not allowed to access {name}" in caplog.text).to_be(True)


@test
async def accessing_forbidden_methods_with_response(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test compile error logs error."""
    cases = {
        "hass.stop()": "HomeAssistant.stop",
        "dt_util.set_default_time_zone()": "module.set_default_time_zone",
        "datetime.non_existing": "module.non_existing",
        "time.tzset()": "TimeWrapper.tzset",
    }
    for source, name in cases.items():
        task = hass.async_add_executor_job(execute, hass, "test.py", source, {}, True)
        await hass.async_block_till_done(wait_background_tasks=True)

        expect(type(task.exception()) is ServiceValidationError).to_be(True)
        expect(f"Not allowed to access {name}" in str(task.exception())).to_be(True)


@test
async def iterating(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test compile error logs error."""
    source = """
for i in [1, 2]:
    hass.states.set('hello.{}'.format(i), 'world')
    """

    await hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done()

    expect(hass.states.is_state("hello.1", "world")).to_be(True)
    expect(hass.states.is_state("hello.2", "world")).to_be(True)


@test
async def using_enumerate(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that enumerate is accepted and executed."""
    source = """
for index, value in enumerate(["earth", "mars"]):
    hass.states.set('hello.{}'.format(index), value)
    """

    await hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done()

    expect(hass.states.is_state("hello.0", "earth")).to_be(True)
    expect(hass.states.is_state("hello.1", "mars")).to_be(True)


@test
async def unpacking_sequence(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test compile error logs error."""
    caplog.set_level(logging.ERROR)
    source = """
a,b = (1,2)
ab_list = [(a,b) for a,b in [(1, 2), (3, 4)]]
hass.states.set('hello.a', a)
hass.states.set('hello.b', b)
hass.states.set('hello.ab_list', '{}'.format(ab_list))
"""

    hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(hass.states.is_state("hello.a", "1")).to_be(True)
    expect(hass.states.is_state("hello.b", "2")).to_be(True)
    expect(hass.states.is_state("hello.ab_list", "[(1, 2), (3, 4)]")).to_be(True)

    expect(caplog.text).to_be("")


@test
async def execute_sorted(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test sorted() function."""
    caplog.set_level(logging.ERROR)
    source = """
a  = sorted([3,1,2])
assert(a == [1,2,3])
hass.states.set('hello.a', a[0])
hass.states.set('hello.b', a[1])
hass.states.set('hello.c', a[2])
"""
    hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(hass.states.is_state("hello.a", "1")).to_be(True)
    expect(hass.states.is_state("hello.b", "2")).to_be(True)
    expect(hass.states.is_state("hello.c", "3")).to_be(True)
    expect(caplog.text).to_be("")


@test
async def exposed_modules(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test datetime and time modules exposed."""
    caplog.set_level(logging.ERROR)
    source = """
hass.states.set('module.time', time.strftime('%Y', time.gmtime(521276400)))
hass.states.set('module.time_strptime',
                time.strftime('%H:%M', time.strptime('12:34', '%H:%M')))
hass.states.set('module.datetime',
                datetime.timedelta(minutes=1).total_seconds())
"""

    hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(hass.states.is_state("module.time", "1986")).to_be(True)
    expect(hass.states.is_state("module.time_strptime", "12:34")).to_be(True)
    expect(hass.states.is_state("module.datetime", "60.0")).to_be(True)

    expect(caplog.text).to_be("")


@test
async def execute_functions(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test functions defined in script can call one another."""
    caplog.set_level(logging.ERROR)
    source = """
def a():
    hass.states.set('hello.a', 'one')

def b():
    a()
    hass.states.set('hello.b', 'two')

b()
"""
    hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(hass.states.is_state("hello.a", "one")).to_be(True)
    expect(hass.states.is_state("hello.b", "two")).to_be(True)
    expect(caplog.text).to_be("")


@test
async def reload(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can re-discover scripts."""
    scripts = [
        "/some/config/dir/python_scripts/hello.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]
    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts
        ),
    ):
        res = await async_setup_component(hass, "python_script", {})

    expect(res).to_be_truthy()
    expect(hass.services.has_service("python_script", "hello")).to_be_truthy()
    expect(hass.services.has_service("python_script", "world_beer")).to_be_truthy()
    expect(hass.services.has_service("python_script", "reload")).to_be_truthy()

    scripts = [
        "/some/config/dir/python_scripts/hello2.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]
    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts
        ),
    ):
        await hass.services.async_call("python_script", "reload", {}, blocking=True)

    expect(hass.services.has_service("python_script", "hello")).to_be_falsy()
    expect(hass.services.has_service("python_script", "hello2")).to_be_truthy()
    expect(hass.services.has_service("python_script", "world_beer")).to_be_truthy()
    expect(hass.services.has_service("python_script", "reload")).to_be_truthy()


@test
async def service_descriptions(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that service descriptions are loaded and reloaded correctly."""
    scripts1 = [
        "/some/config/dir/python_scripts/hello.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]

    service_descriptions1 = (
        "hello:\n"
        "  name: ABC\n"
        "  description: Description of hello.py.\n"
        "  fields:\n"
        "    fake_param:\n"
        "      description: Parameter used by hello.py.\n"
        "      example: 'This is a test of python_script.hello'"
    )
    services_yaml1 = {
        f"{hass.config.config_dir}/{FOLDER}/services.yaml": service_descriptions1
    }

    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts1
        ),
        patch(
            "homeassistant.components.python_script.os.path.exists", return_value=True
        ),
        patch_yaml_files(
            services_yaml1,
        ),
    ):
        await async_setup_component(hass, DOMAIN, {})

        descriptions = await async_get_all_descriptions(hass)

    expect(len(descriptions)).to_be(1)

    expect(descriptions[DOMAIN]["hello"]["name"]).to_equal("ABC")
    expect(descriptions[DOMAIN]["hello"]["description"]).to_equal(
        "Description of hello.py."
    )
    expect(
        descriptions[DOMAIN]["hello"]["fields"]["fake_param"]["description"]
    ).to_equal("Parameter used by hello.py.")
    expect(
        descriptions[DOMAIN]["hello"]["fields"]["fake_param"]["example"]
    ).to_equal("This is a test of python_script.hello")

    expect(descriptions[DOMAIN]["world_beer"]["name"]).to_equal("world_beer")
    expect(descriptions[DOMAIN]["world_beer"]["description"]).to_equal("")
    expect(bool(descriptions[DOMAIN]["world_beer"]["fields"])).to_be(False)

    scripts2 = [
        "/some/config/dir/python_scripts/hello2.py",
        "/some/config/dir/python_scripts/world_beer.py",
    ]

    service_descriptions2 = (
        "hello2:\n"
        "  description: Description of hello2.py.\n"
        "  fields:\n"
        "    fake_param:\n"
        "      description: Parameter used by hello2.py.\n"
        "      example: 'This is a test of python_script.hello2'"
    )
    services_yaml2 = {
        f"{hass.config.config_dir}/{FOLDER}/services.yaml": service_descriptions2
    }

    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts2
        ),
        patch(
            "homeassistant.components.python_script.os.path.exists", return_value=True
        ),
        patch_yaml_files(
            services_yaml2,
        ),
    ):
        await hass.services.async_call(DOMAIN, "reload", {}, blocking=True)
        descriptions = await async_get_all_descriptions(hass)

    expect(len(descriptions)).to_be(1)

    expect(descriptions[DOMAIN]["hello2"]["description"]).to_equal(
        "Description of hello2.py."
    )
    expect(
        descriptions[DOMAIN]["hello2"]["fields"]["fake_param"]["description"]
    ).to_equal("Parameter used by hello2.py.")
    expect(
        descriptions[DOMAIN]["hello2"]["fields"]["fake_param"]["example"]
    ).to_equal("This is a test of python_script.hello2")


@test
async def sleep_warns_one(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test time.sleep warns once."""
    caplog.set_level(logging.WARNING)
    source = """
time.sleep(2)
time.sleep(5)
"""

    with patch("homeassistant.components.python_script.time.sleep"):
        hass.async_add_executor_job(execute, hass, "test.py", source, {})
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(caplog.text.count("time.sleep")).to_be(1)


@test
async def execute_with_output(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test executing a script with a return value."""
    caplog.set_level(logging.WARNING)

    scripts = [
        "/some/config/dir/python_scripts/hello.py",
    ]
    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts
        ),
    ):
        await async_setup_component(hass, "python_script", {})

    source = """
output = {"result": f"hello {data.get('name', 'World')}"}
    """

    with patch(
        "homeassistant.components.python_script.open",
        mock_open(read_data=source),
        create=True,
    ):
        response = await hass.services.async_call(
            "python_script",
            "hello",
            {"name": "paulus"},
            blocking=True,
            return_response=True,
        )

    expect(isinstance(response, dict)).to_be(True)
    expect(len(response)).to_be(1)
    expect(response["result"]).to_equal("hello paulus")

    expect(caplog.text).to_be("")


@test
async def execute_no_output(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test executing a script without a return value."""
    caplog.set_level(logging.WARNING)

    scripts = [
        "/some/config/dir/python_scripts/hello.py",
    ]
    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts
        ),
    ):
        await async_setup_component(hass, "python_script", {})

    source = """
no_output = {"result": f"hello {data.get('name', 'World')}"}
    """

    with patch(
        "homeassistant.components.python_script.open",
        mock_open(read_data=source),
        create=True,
    ):
        response = await hass.services.async_call(
            "python_script",
            "hello",
            {"name": "paulus"},
            blocking=True,
            return_response=True,
        )

    expect(isinstance(response, dict)).to_be(True)
    expect(len(response)).to_be(0)

    expect(caplog.text).to_be("")


@test
async def execute_wrong_output_type(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test executing a script without a return value."""
    scripts = [
        "/some/config/dir/python_scripts/hello.py",
    ]
    with (
        patch(
            "homeassistant.components.python_script.os.path.isdir", return_value=True
        ),
        patch(
            "homeassistant.components.python_script.glob.iglob", return_value=scripts
        ),
    ):
        await async_setup_component(hass, "python_script", {})

    source = """
output = f"hello {data.get('name', 'World')}"
    """

    with patch(
        "homeassistant.components.python_script.open",
        mock_open(read_data=source),
        create=True,
    ):
        async with expect_raises_async(ServiceValidationError):
            await hass.services.async_call(
                "python_script",
                "hello",
                {"name": "paulus"},
                blocking=True,
                return_response=True,
            )


@test
async def augmented_assignment_operations(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that augmented assignment operations work."""
    source = """
a = 10
a += 20
a *= 5
a -= 8
b = "foo"
b += "bar"
b *= 2
c = []
c += [1, 2, 3]
c *= 2
hass.states.set('hello.a', a)
hass.states.set('hello.b', b)
hass.states.set('hello.c', c)
    """

    hass.async_add_executor_job(execute, hass, "aug_assign.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(hass.states.get("hello.a").state).to_equal(str(((10 + 20) * 5) - 8))
    expect(hass.states.get("hello.b").state).to_equal(("foo" + "bar") * 2)
    expect(hass.states.get("hello.c").state).to_equal(str([1, 2, 3] * 2))


@test.cases(
    test.case(
        "datetime.date",
        case="d = datetime.date(2024, 1, 1); d += 5",
        error="The '+=' operation is not allowed",
    ),
)
@test
async def prohibited_augmented_assignment_operations(
    case: str,
    error: str,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that prohibited augmented assignment operations raise an error."""
    hass.async_add_executor_job(execute, hass, "aug_assign_prohibited.py", case, {})
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(error in caplog.text).to_be(True)


@test
async def import_allow_strptime(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test calling datetime.datetime.strptime works."""
    source = """
test_date = datetime.datetime.strptime('2024-04-01', '%Y-%m-%d')
logger.info(f'Date {test_date}')
    """
    hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(
        "Error executing script: Not allowed to import _strptime" not in caplog.text
    ).to_be(True)
    expect("Date 2024-04-01 00:00:00" in caplog.text).to_be(True)


@test
async def no_other_imports_allowed(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test imports are not allowed."""
    source = "import sys"
    hass.async_add_executor_job(execute, hass, "test.py", source, {})
    await hass.async_block_till_done(wait_background_tasks=True)
    expect("ImportError: Not allowed to import sys" in caplog.text).to_be(True)
