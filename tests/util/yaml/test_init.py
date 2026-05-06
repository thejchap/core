"""Test Home Assistant yaml loader."""

from collections.abc import Generator, Iterator
from contextlib import contextmanager
import importlib
import io
import os
import pathlib
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test
import voluptuous as vol
import yaml as pyyaml

from homeassistant.config import YAML_CONFIG_FILE, load_yaml_config_file
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import yaml as yaml_util
from homeassistant.util.yaml import loader as yaml_loader

from tests.common import extract_stack_to_frame, patch_yaml_files
from tests.hass_fixtures import LogCapture, caplog, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported `hass` resolves via Depends()."""
    return 0


# These four names mirror the pytest parametrization of the original
# ``try_both_loaders`` / ``try_both_dumpers`` fixtures so the label
# strings passed to ``@test.cases`` round-trip cleanly through the
# parity gate.
_LOADER_VARIANTS = ("enable_c_loader", "disable_c_loader")
_DUMPER_VARIANTS = ("enable_c_dumper", "disable_c_dumper")


@contextmanager
def _loader_variant(variant: str) -> Iterator[None]:
    """Context manager equivalent of the pytest ``try_both_loaders`` fixture."""
    if variant != "disable_c_loader":
        yield
        return
    try:
        cloader = pyyaml.CSafeLoader
    except ImportError:
        yield
        return
    del pyyaml.CSafeLoader
    importlib.reload(yaml_loader)
    try:
        yield
    finally:
        pyyaml.CSafeLoader = cloader
        importlib.reload(yaml_loader)


@contextmanager
def _dumper_variant(variant: str) -> Iterator[None]:
    """Context manager equivalent of the pytest ``try_both_dumpers`` fixture."""
    if variant != "disable_c_dumper":
        yield
        return
    try:
        cdumper = pyyaml.CSafeDumper
    except ImportError:
        yield
        return
    del pyyaml.CSafeDumper
    importlib.reload(yaml_loader)
    try:
        yield
    finally:
        pyyaml.CSafeDumper = cdumper
        importlib.reload(yaml_loader)


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def simple_list(loader_variant: str) -> None:
    """Test simple list."""
    with _loader_variant(loader_variant):
        conf = "config:\n  - simple\n  - list"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
        expect(doc["config"]).to_equal(["simple", "list"])


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def simple_dict(loader_variant: str) -> None:
    """Test simple dict."""
    with _loader_variant(loader_variant):
        conf = "key: value"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
        expect(doc["key"]).to_equal("value")


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def unhashable_key(loader_variant: str) -> None:
    """Test an unhashable key."""
    with (
        _loader_variant(loader_variant),
        patch_yaml_files({YAML_CONFIG_FILE: "message:\n  {{ states.state }}"}),
    ):
        expect(lambda: load_yaml_config_file(YAML_CONFIG_FILE)).to_raise(
            HomeAssistantError
        )


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def no_key(loader_variant: str) -> None:
    """Test item without a key."""
    with (
        _loader_variant(loader_variant),
        patch_yaml_files({YAML_CONFIG_FILE: "a: a\nnokeyhere"}),
    ):
        expect(lambda: yaml_util.load_yaml(YAML_CONFIG_FILE)).to_raise(
            HomeAssistantError
        )


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def environment_variable(loader_variant: str) -> None:
    """Test config file with environment variable."""
    with _loader_variant(loader_variant):
        os.environ["PASSWORD"] = "secret_password"
        conf = "password: !env_var PASSWORD"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
        expect(doc["password"]).to_equal("secret_password")
        del os.environ["PASSWORD"]


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def environment_variable_default(loader_variant: str) -> None:
    """Test config file with default value for environment variable."""
    with _loader_variant(loader_variant):
        conf = "password: !env_var PASSWORD secret_password"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
        expect(doc["password"]).to_equal("secret_password")


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def invalid_environment_variable(loader_variant: str) -> None:
    """Test config file with no environment variable sat."""
    with _loader_variant(loader_variant):
        conf = "password: !env_var PASSWORD"

        def _parse() -> None:
            with io.StringIO(conf) as file:
                yaml_loader.parse_yaml(file)

        expect(_parse).to_raise(HomeAssistantError)


@test.cases(
    test.case(
        "enable_c_loader-value",
        loader_variant="enable_c_loader",
        files={"test.yaml": "value"},
        value="value",
    ),
    test.case(
        "enable_c_loader-empty",
        loader_variant="enable_c_loader",
        files={"test.yaml": None},
        value={},
    ),
    test.case(
        "enable_c_loader-int",
        loader_variant="enable_c_loader",
        files={"test.yaml": "123"},
        value=123,
    ),
    test.case(
        "disable_c_loader-value",
        loader_variant="disable_c_loader",
        files={"test.yaml": "value"},
        value="value",
    ),
    test.case(
        "disable_c_loader-empty",
        loader_variant="disable_c_loader",
        files={"test.yaml": None},
        value={},
    ),
    test.case(
        "disable_c_loader-int",
        loader_variant="disable_c_loader",
        files={"test.yaml": "123"},
        value=123,
    ),
)
def include_yaml(loader_variant: str, files: dict[str, Any], value: Any) -> None:
    """Test include yaml."""
    with _loader_variant(loader_variant), patch_yaml_files(files):
        conf = "key: !include test.yaml"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
            expect(doc["key"]).to_equal(value)


@test.cases(
    test.case(
        "enable_c_loader-strings",
        loader_variant="enable_c_loader",
        files={"/test/one.yaml": "one", "/test/two.yaml": "two"},
        value=["one", "two"],
    ),
    test.case(
        "enable_c_loader-ints",
        loader_variant="enable_c_loader",
        files={"/test/one.yaml": "1", "/test/two.yaml": "2"},
        value=[1, 2],
    ),
    test.case(
        "enable_c_loader-skip-none",
        loader_variant="enable_c_loader",
        files={"/test/one.yaml": "1", "/test/two.yaml": None},
        value=[1],
    ),
    test.case(
        "disable_c_loader-strings",
        loader_variant="disable_c_loader",
        files={"/test/one.yaml": "one", "/test/two.yaml": "two"},
        value=["one", "two"],
    ),
    test.case(
        "disable_c_loader-ints",
        loader_variant="disable_c_loader",
        files={"/test/one.yaml": "1", "/test/two.yaml": "2"},
        value=[1, 2],
    ),
    test.case(
        "disable_c_loader-skip-none",
        loader_variant="disable_c_loader",
        files={"/test/one.yaml": "1", "/test/two.yaml": None},
        value=[1],
    ),
)
def include_dir_list(
    loader_variant: str, files: dict[str, Any], value: list[Any]
) -> None:
    """Test include dir list yaml."""
    with (
        _loader_variant(loader_variant),
        patch_yaml_files(files),
        patch("homeassistant.util.yaml.loader.os.walk") as mock_walk,
    ):
        mock_walk.return_value = [["/test", [], ["two.yaml", "one.yaml"]]]
        conf = "key: !include_dir_list /test"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
            expect(sorted(doc["key"])).to_equal(sorted(value))


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def include_dir_list_recursive(loader_variant: str) -> None:
    """Test include dir recursive list yaml."""
    files = {
        "/test/zero.yaml": "zero",
        "/test/tmp2/one.yaml": "one",
        "/test/tmp2/two.yaml": "two",
    }
    with (
        _loader_variant(loader_variant),
        patch_yaml_files(files),
        patch("homeassistant.util.yaml.loader.os.walk") as mock_walk,
    ):
        mock_walk.return_value = [
            ["/test", ["tmp2", ".ignore", "ignore"], ["zero.yaml"]],
            ["/test/tmp2", [], ["one.yaml", "two.yaml"]],
            ["/test/ignore", [], [".ignore.yaml"]],
        ]

        conf = "key: !include_dir_list /test"
        with io.StringIO(conf) as file:
            expect(".ignore" in mock_walk.return_value[0][1]).to_be(True)
            doc = yaml_loader.parse_yaml(file)
            expect("tmp2" in mock_walk.return_value[0][1]).to_be(True)
            expect(".ignore" not in mock_walk.return_value[0][1]).to_be(True)
            expect(sorted(doc["key"])).to_equal(sorted(["zero", "one", "two"]))


@test.cases(
    test.case(
        "enable_c_loader-strings",
        loader_variant="enable_c_loader",
        files={"/test/first.yaml": "one", "/test/second.yaml": "two"},
        value={"first": "one", "second": "two"},
    ),
    test.case(
        "enable_c_loader-ints",
        loader_variant="enable_c_loader",
        files={"/test/first.yaml": "1", "/test/second.yaml": "2"},
        value={"first": 1, "second": 2},
    ),
    test.case(
        "enable_c_loader-skip-none",
        loader_variant="enable_c_loader",
        files={"/test/first.yaml": "1", "/test/second.yaml": None},
        value={"first": 1, "second": {}},
    ),
    test.case(
        "disable_c_loader-strings",
        loader_variant="disable_c_loader",
        files={"/test/first.yaml": "one", "/test/second.yaml": "two"},
        value={"first": "one", "second": "two"},
    ),
    test.case(
        "disable_c_loader-ints",
        loader_variant="disable_c_loader",
        files={"/test/first.yaml": "1", "/test/second.yaml": "2"},
        value={"first": 1, "second": 2},
    ),
    test.case(
        "disable_c_loader-skip-none",
        loader_variant="disable_c_loader",
        files={"/test/first.yaml": "1", "/test/second.yaml": None},
        value={"first": 1, "second": {}},
    ),
)
def include_dir_named(
    loader_variant: str, files: dict[str, Any], value: dict[str, Any]
) -> None:
    """Test include dir named yaml."""
    with (
        _loader_variant(loader_variant),
        patch_yaml_files(files),
        patch("homeassistant.util.yaml.loader.os.walk") as mock_walk,
    ):
        mock_walk.return_value = [
            ["/test", [], ["first.yaml", "second.yaml", "secrets.yaml"]]
        ]

        conf = "key: !include_dir_named /test"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
            expect(doc["key"]).to_equal(value)


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def include_dir_named_recursive(loader_variant: str) -> None:
    """Test include dir named yaml."""
    files = {
        "/test/first.yaml": "one",
        "/test/tmp2/second.yaml": "two",
        "/test/tmp2/third.yaml": "three",
    }
    with (
        _loader_variant(loader_variant),
        patch_yaml_files(files),
        patch("homeassistant.util.yaml.loader.os.walk") as mock_walk,
    ):
        mock_walk.return_value = [
            ["/test", ["tmp2", ".ignore", "ignore"], ["first.yaml"]],
            ["/test/tmp2", [], ["second.yaml", "third.yaml"]],
            ["/test/ignore", [], [".ignore.yaml"]],
        ]

        conf = "key: !include_dir_named /test"
        correct = {"first": "one", "second": "two", "third": "three"}
        with io.StringIO(conf) as file:
            expect(".ignore" in mock_walk.return_value[0][1]).to_be(True)
            doc = yaml_loader.parse_yaml(file)
            expect("tmp2" in mock_walk.return_value[0][1]).to_be(True)
            expect(".ignore" not in mock_walk.return_value[0][1]).to_be(True)
            expect(doc["key"]).to_equal(correct)


@test.cases(
    test.case(
        "enable_c_loader-strings",
        loader_variant="enable_c_loader",
        files={"/test/first.yaml": "- one", "/test/second.yaml": "- two\n- three"},
        value=["one", "two", "three"],
    ),
    test.case(
        "enable_c_loader-ints",
        loader_variant="enable_c_loader",
        files={"/test/first.yaml": "- 1", "/test/second.yaml": "- 2\n- 3"},
        value=[1, 2, 3],
    ),
    test.case(
        "enable_c_loader-skip-none",
        loader_variant="enable_c_loader",
        files={"/test/first.yaml": "- 1", "/test/second.yaml": None},
        value=[1],
    ),
    test.case(
        "disable_c_loader-strings",
        loader_variant="disable_c_loader",
        files={"/test/first.yaml": "- one", "/test/second.yaml": "- two\n- three"},
        value=["one", "two", "three"],
    ),
    test.case(
        "disable_c_loader-ints",
        loader_variant="disable_c_loader",
        files={"/test/first.yaml": "- 1", "/test/second.yaml": "- 2\n- 3"},
        value=[1, 2, 3],
    ),
    test.case(
        "disable_c_loader-skip-none",
        loader_variant="disable_c_loader",
        files={"/test/first.yaml": "- 1", "/test/second.yaml": None},
        value=[1],
    ),
)
def include_dir_merge_list(
    loader_variant: str, files: dict[str, Any], value: list[Any]
) -> None:
    """Test include dir merge list yaml."""
    with (
        _loader_variant(loader_variant),
        patch_yaml_files(files),
        patch("homeassistant.util.yaml.loader.os.walk") as mock_walk,
    ):
        mock_walk.return_value = [["/test", [], ["first.yaml", "second.yaml"]]]

        conf = "key: !include_dir_merge_list /test"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
            expect(sorted(doc["key"])).to_equal(sorted(value))


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def include_dir_merge_list_recursive(loader_variant: str) -> None:
    """Test include dir merge list yaml."""
    files = {
        "/test/first.yaml": "- one",
        "/test/tmp2/second.yaml": "- two",
        "/test/tmp2/third.yaml": "- three\n- four",
    }
    with (
        _loader_variant(loader_variant),
        patch_yaml_files(files),
        patch("homeassistant.util.yaml.loader.os.walk") as mock_walk,
    ):
        mock_walk.return_value = [
            ["/test", ["tmp2", ".ignore", "ignore"], ["first.yaml"]],
            ["/test/tmp2", [], ["second.yaml", "third.yaml"]],
            ["/test/ignore", [], [".ignore.yaml"]],
        ]

        conf = "key: !include_dir_merge_list /test"
        with io.StringIO(conf) as file:
            expect(".ignore" in mock_walk.return_value[0][1]).to_be(True)
            doc = yaml_loader.parse_yaml(file)
            expect("tmp2" in mock_walk.return_value[0][1]).to_be(True)
            expect(".ignore" not in mock_walk.return_value[0][1]).to_be(True)
            expect(sorted(doc["key"])).to_equal(sorted(["one", "two", "three", "four"]))


@test.cases(
    test.case(
        "enable_c_loader-strings",
        loader_variant="enable_c_loader",
        files={
            "/test/first.yaml": "key1: one",
            "/test/second.yaml": "key2: two\nkey3: three",
        },
        value={"key1": "one", "key2": "two", "key3": "three"},
    ),
    test.case(
        "enable_c_loader-ints",
        loader_variant="enable_c_loader",
        files={
            "/test/first.yaml": "key1: 1",
            "/test/second.yaml": "key2: 2\nkey3: 3",
        },
        value={"key1": 1, "key2": 2, "key3": 3},
    ),
    test.case(
        "enable_c_loader-skip-none",
        loader_variant="enable_c_loader",
        files={
            "/test/first.yaml": "key1: 1",
            "/test/second.yaml": None,
        },
        value={"key1": 1},
    ),
    test.case(
        "disable_c_loader-strings",
        loader_variant="disable_c_loader",
        files={
            "/test/first.yaml": "key1: one",
            "/test/second.yaml": "key2: two\nkey3: three",
        },
        value={"key1": "one", "key2": "two", "key3": "three"},
    ),
    test.case(
        "disable_c_loader-ints",
        loader_variant="disable_c_loader",
        files={
            "/test/first.yaml": "key1: 1",
            "/test/second.yaml": "key2: 2\nkey3: 3",
        },
        value={"key1": 1, "key2": 2, "key3": 3},
    ),
    test.case(
        "disable_c_loader-skip-none",
        loader_variant="disable_c_loader",
        files={
            "/test/first.yaml": "key1: 1",
            "/test/second.yaml": None,
        },
        value={"key1": 1},
    ),
)
def include_dir_merge_named(
    loader_variant: str, files: dict[str, Any], value: dict[str, Any]
) -> None:
    """Test include dir merge named yaml."""
    with (
        _loader_variant(loader_variant),
        patch_yaml_files(files),
        patch("homeassistant.util.yaml.loader.os.walk") as mock_walk,
    ):
        mock_walk.return_value = [["/test", [], ["first.yaml", "second.yaml"]]]

        conf = "key: !include_dir_merge_named /test"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
            expect(doc["key"]).to_equal(value)


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def include_dir_merge_named_recursive(loader_variant: str) -> None:
    """Test include dir merge named yaml."""
    files = {
        "/test/first.yaml": "key1: one",
        "/test/tmp2/second.yaml": "key2: two",
        "/test/tmp2/third.yaml": "key3: three\nkey4: four",
    }
    with (
        _loader_variant(loader_variant),
        patch_yaml_files(files),
        patch("homeassistant.util.yaml.loader.os.walk") as mock_walk,
    ):
        mock_walk.return_value = [
            ["/test", ["tmp2", ".ignore", "ignore"], ["first.yaml"]],
            ["/test/tmp2", [], ["second.yaml", "third.yaml"]],
            ["/test/ignore", [], [".ignore.yaml"]],
        ]

        conf = "key: !include_dir_merge_named /test"
        with io.StringIO(conf) as file:
            expect(".ignore" in mock_walk.return_value[0][1]).to_be(True)
            doc = yaml_loader.parse_yaml(file)
            expect("tmp2" in mock_walk.return_value[0][1]).to_be(True)
            expect(".ignore" not in mock_walk.return_value[0][1]).to_be(True)
            expect(doc["key"]).to_equal(
                {
                    "key1": "one",
                    "key2": "two",
                    "key3": "three",
                    "key4": "four",
                }
            )


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def load_yaml_encoding_error(loader_variant: str) -> None:
    """Test raising a UnicodeDecodeError."""
    with (
        _loader_variant(loader_variant),
        patch("annotatedyaml.loader.open", create=True) as mock_open,
    ):
        mock_open.side_effect = UnicodeDecodeError("", b"", 1, 0, "")
        expect(lambda: yaml_loader.load_yaml("test")).to_raise(HomeAssistantError)


@test.cases(
    test.case("enable_c_dumper", dumper_variant="enable_c_dumper"),
    test.case("disable_c_dumper", dumper_variant="disable_c_dumper"),
)
def dump(dumper_variant: str) -> None:
    """The that the dump method returns empty None values."""
    with _dumper_variant(dumper_variant):
        expect(yaml_util.dump({"a": None, "b": "b"})).to_equal("a:\nb: b\n")


@test.cases(
    test.case("enable_c_dumper", dumper_variant="enable_c_dumper"),
    test.case("disable_c_dumper", dumper_variant="disable_c_dumper"),
)
def dump_unicode(dumper_variant: str) -> None:
    """The that the dump method returns empty None values."""
    with _dumper_variant(dumper_variant):
        expect(yaml_util.dump({"a": None, "b": "привет"})).to_equal("a:\nb: привет\n")


@test.cases(
    test.case("enable_c_dumper", dumper_variant="enable_c_dumper"),
    test.case("disable_c_dumper", dumper_variant="disable_c_dumper"),
)
def representing_yaml_loaded_data(dumper_variant: str) -> None:
    """Test we can represent YAML loaded data."""
    with (
        _dumper_variant(dumper_variant),
        patch_yaml_files({YAML_CONFIG_FILE: 'key: [1, "2", 3]'}),
    ):
        data = load_yaml_config_file(YAML_CONFIG_FILE)
        expect(yaml_util.dump(data)).to_equal("key:\n- 1\n- '2'\n- 3\n")


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def duplicate_key(
    loader_variant: str,
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test duplicate dict keys."""
    with (
        _loader_variant(loader_variant),
        patch_yaml_files({YAML_CONFIG_FILE: "key: thing1\nkey: thing2"}),
    ):
        load_yaml_config_file(YAML_CONFIG_FILE)
        expect("contains duplicate key" in caplog.text).to_be(True)


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def no_recursive_secrets(loader_variant: str) -> None:
    """Test that loading of secrets from the secrets file fails correctly."""
    with (
        _loader_variant(loader_variant),
        patch_yaml_files(
            {
                YAML_CONFIG_FILE: "key: !secret a",
                yaml_util.SECRET_YAML: "a: 1\nb: !secret a",
            }
        ),
    ):
        try:
            load_yaml_config_file(YAML_CONFIG_FILE)
        except HomeAssistantError as exc:
            expect(exc.args).to_equal(("Secrets not supported in this YAML file",))
        else:
            raise AssertionError("did not raise HomeAssistantError")


@test
def input_class() -> None:
    """Test input class."""
    yaml_input = yaml_util.Input("hello")
    yaml_input2 = yaml_util.Input("hello")

    expect(yaml_input.name).to_equal("hello")
    expect(yaml_input).to_equal(yaml_input2)

    expect(len({yaml_input, yaml_input2})).to_equal(1)


@test.cases(
    test.case(
        "enable_c_loader-enable_c_dumper",
        loader_variant="enable_c_loader",
        dumper_variant="enable_c_dumper",
    ),
    test.case(
        "enable_c_loader-disable_c_dumper",
        loader_variant="enable_c_loader",
        dumper_variant="disable_c_dumper",
    ),
    test.case(
        "disable_c_loader-enable_c_dumper",
        loader_variant="disable_c_loader",
        dumper_variant="enable_c_dumper",
    ),
    test.case(
        "disable_c_loader-disable_c_dumper",
        loader_variant="disable_c_loader",
        dumper_variant="disable_c_dumper",
    ),
)
def input_(loader_variant: str, dumper_variant: str) -> None:
    """Test loading inputs."""
    with _loader_variant(loader_variant), _dumper_variant(dumper_variant):
        data = {"hello": yaml_util.Input("test_name")}
        expect(yaml_util.parse_yaml(yaml_util.dump(data))).to_equal(data)


@test.skip_if(
    not os.environ.get("HASS_CI"),
    reason="This test validates that the CI has the C loader available",
)
def c_loader_is_available_in_ci() -> None:
    """Verify we are testing the C loader in the CI."""
    expect(yaml_util.loader.HAS_C_LOADER).to_be(True)


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
async def loading_actual_file_with_syntax_error(
    loader_variant: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test loading a real file with syntax errors."""
    with _loader_variant(loader_variant):
        fixture_path = pathlib.Path(__file__).parent.joinpath(
            "fixtures", "bad.yaml.txt"
        )

        try:
            await hass.async_add_executor_job(load_yaml_config_file, fixture_path)
        except HomeAssistantError:
            return
        raise AssertionError("did not raise HomeAssistantError")


@fixture
def mock_integration_frame() -> Generator[Mock]:
    """Mock as if we're calling code from inside an integration."""
    correct_frame = Mock(
        filename="/home/paulus/homeassistant/components/hue/light.py",
        lineno="23",
        line="self.light.is_on",
    )
    with (
        patch(
            "homeassistant.helpers.frame.linecache.getline",
            return_value=correct_frame.line,
        ),
        patch(
            "homeassistant.helpers.frame.get_current_frame",
            return_value=extract_stack_to_frame(
                [
                    Mock(
                        filename="/home/paulus/homeassistant/core.py",
                        lineno="23",
                        line="do_something()",
                    ),
                    correct_frame,
                    Mock(
                        filename="/home/paulus/aiohue/lights.py",
                        lineno="2",
                        line="something()",
                    ),
                ]
            ),
        ),
    ):
        yield correct_frame


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def string_annotated(loader_variant: str) -> None:
    """Test strings are annotated with file + line."""
    with _loader_variant(loader_variant):
        conf = (
            "key1: str\n"
            "key2:\n"
            "  blah: blah\n"
            "key3:\n"
            " - 1\n"
            " - 2\n"
            " - 3\n"
            "key4: yes\n"
            "key5: 1\n"
            "key6: 1.0\n"
        )
        expected_annotations = {
            "key1": [("<file>", 1), ("<file>", 1)],
            "key2": [("<file>", 2), ("<file>", 3)],
            "key3": [("<file>", 4), ("<file>", 5)],
            "key4": [("<file>", 8), (None, None)],
            "key5": [("<file>", 9), (None, None)],
            "key6": [("<file>", 10), (None, None)],
        }
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)
        for key, value in doc.items():
            expect(getattr(key, "__config_file__", None)).to_equal(
                expected_annotations[key][0][0]
            )
            expect(getattr(key, "__line__", None)).to_equal(
                expected_annotations[key][0][1]
            )
            expect(getattr(value, "__config_file__", None)).to_equal(
                expected_annotations[key][1][0]
            )
            expect(getattr(value, "__line__", None)).to_equal(
                expected_annotations[key][1][1]
            )


@test.cases(
    test.case("enable_c_loader", loader_variant="enable_c_loader"),
    test.case("disable_c_loader", loader_variant="disable_c_loader"),
)
def string_used_as_vol_schema(loader_variant: str) -> None:
    """Test the subclassed strings can be used in voluptuous schemas."""
    with _loader_variant(loader_variant):
        conf = "wanted_data:\n  key_1: value_1\n  key_2: value_2\n"
        with io.StringIO(conf) as file:
            doc = yaml_loader.parse_yaml(file)

        # Test using the subclassed strings in a schema.
        schema = vol.Schema(
            {vol.Required(key): value for key, value in doc["wanted_data"].items()},
        )
        # Test using the subclassed strings when validating a schema.
        schema(doc["wanted_data"])
        schema({"key_1": "value_1", "key_2": "value_2"})
        expect(lambda: schema({"key_1": "value_2", "key_2": "value_1"})).to_raise(
            vol.Invalid
        )


@test.cases(
    test.case(
        "enable_c_loader-empty",
        loader_variant="enable_c_loader",
        hass_config_yaml="",
        expected_data={},
    ),
    test.case(
        "enable_c_loader-bla",
        loader_variant="enable_c_loader",
        hass_config_yaml="bla:",
        expected_data={"bla": None},
    ),
    test.case(
        "disable_c_loader-empty",
        loader_variant="disable_c_loader",
        hass_config_yaml="",
        expected_data={},
    ),
    test.case(
        "disable_c_loader-bla",
        loader_variant="disable_c_loader",
        hass_config_yaml="bla:",
        expected_data={"bla": None},
    ),
)
def load_yaml_dict(
    loader_variant: str, hass_config_yaml: str, expected_data: Any
) -> None:
    """Test item without a key."""
    with (
        _loader_variant(loader_variant),
        patch_yaml_files({YAML_CONFIG_FILE: hass_config_yaml}),
    ):
        expect(yaml_util.load_yaml_dict(YAML_CONFIG_FILE)).to_equal(expected_data)


@test.cases(
    test.case(
        "enable_c_loader-abc", loader_variant="enable_c_loader", hass_config_yaml="abc"
    ),
    test.case(
        "enable_c_loader-123", loader_variant="enable_c_loader", hass_config_yaml="123"
    ),
    test.case(
        "enable_c_loader-list", loader_variant="enable_c_loader", hass_config_yaml="[]"
    ),
    test.case(
        "disable_c_loader-abc",
        loader_variant="disable_c_loader",
        hass_config_yaml="abc",
    ),
    test.case(
        "disable_c_loader-123",
        loader_variant="disable_c_loader",
        hass_config_yaml="123",
    ),
    test.case(
        "disable_c_loader-list",
        loader_variant="disable_c_loader",
        hass_config_yaml="[]",
    ),
)
def load_yaml_dict_fail(loader_variant: str, hass_config_yaml: str) -> None:
    """Test item without a key."""
    # Make sure we raise a subclass of HomeAssistantError, not
    # annotated_yaml.YAMLException.
    expect(issubclass(yaml_loader.YamlTypeError, HomeAssistantError)).to_be(True)

    with (
        _loader_variant(loader_variant),
        patch_yaml_files({YAML_CONFIG_FILE: hass_config_yaml}),
    ):
        expect(lambda: yaml_loader.load_yaml_dict(YAML_CONFIG_FILE)).to_raise(
            yaml_loader.YamlTypeError
        )


@test.cases(
    test.case(
        "enable_c_loader-include", loader_variant="enable_c_loader", tag="!include"
    ),
    test.case(
        "enable_c_loader-include_dir_named",
        loader_variant="enable_c_loader",
        tag="!include_dir_named",
    ),
    test.case(
        "enable_c_loader-include_dir_merge_named",
        loader_variant="enable_c_loader",
        tag="!include_dir_merge_named",
    ),
    test.case(
        "enable_c_loader-include_dir_list",
        loader_variant="enable_c_loader",
        tag="!include_dir_list",
    ),
    test.case(
        "enable_c_loader-include_dir_merge_list",
        loader_variant="enable_c_loader",
        tag="!include_dir_merge_list",
    ),
    test.case(
        "disable_c_loader-include", loader_variant="disable_c_loader", tag="!include"
    ),
    test.case(
        "disable_c_loader-include_dir_named",
        loader_variant="disable_c_loader",
        tag="!include_dir_named",
    ),
    test.case(
        "disable_c_loader-include_dir_merge_named",
        loader_variant="disable_c_loader",
        tag="!include_dir_merge_named",
    ),
    test.case(
        "disable_c_loader-include_dir_list",
        loader_variant="disable_c_loader",
        tag="!include_dir_list",
    ),
    test.case(
        "disable_c_loader-include_dir_merge_list",
        loader_variant="disable_c_loader",
        tag="!include_dir_merge_list",
    ),
)
def include_without_parameter(loader_variant: str, tag: str) -> None:
    """Test include extensions without parameters."""
    with _loader_variant(loader_variant):

        def _parse() -> None:
            with io.StringIO(f"key: {tag}") as file:
                yaml_loader.parse_yaml(file)

        expect(_parse).to_raise(HomeAssistantError, match=f"{tag} needs an argument")


@test.cases(
    test.case(
        "enable_c_loader-FileNotFoundError",
        loader_variant="enable_c_loader",
        open_exception=FileNotFoundError,
        load_yaml_exception=OSError,
    ),
    test.case(
        "enable_c_loader-NotADirectoryError",
        loader_variant="enable_c_loader",
        open_exception=NotADirectoryError,
        load_yaml_exception=HomeAssistantError,
    ),
    test.case(
        "enable_c_loader-PermissionError",
        loader_variant="enable_c_loader",
        open_exception=PermissionError,
        load_yaml_exception=HomeAssistantError,
    ),
    test.case(
        "disable_c_loader-FileNotFoundError",
        loader_variant="disable_c_loader",
        open_exception=FileNotFoundError,
        load_yaml_exception=OSError,
    ),
    test.case(
        "disable_c_loader-NotADirectoryError",
        loader_variant="disable_c_loader",
        open_exception=NotADirectoryError,
        load_yaml_exception=HomeAssistantError,
    ),
    test.case(
        "disable_c_loader-PermissionError",
        loader_variant="disable_c_loader",
        open_exception=PermissionError,
        load_yaml_exception=HomeAssistantError,
    ),
)
def load_yaml_wrap_oserror(
    loader_variant: str,
    open_exception: type[BaseException],
    load_yaml_exception: type[BaseException],
) -> None:
    """Test load_yaml wraps OSError in HomeAssistantError."""
    with (
        _loader_variant(loader_variant),
        patch("annotatedyaml.loader.open", side_effect=open_exception),
    ):
        expect(lambda: yaml_loader.load_yaml("bla")).to_raise(load_yaml_exception)
