"""Test check_config script."""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from unittest.mock import patch

from tryke import expect, test

from homeassistant.config import YAML_CONFIG_FILE
from homeassistant.scripts import check_config

from tests.common import get_test_config_dir, patch_yaml_files

BASE_CONFIG = (
    "homeassistant:\n"
    "  name: Home\n"
    "  latitude: -26.107361\n"
    "  longitude: 28.054500\n"
    "  elevation: 1600\n"
    "  unit_system: metric\n"
    "  time_zone: GMT\n"
    "\n\n"
)

BAD_CORE_CONFIG = "homeassistant:\n  unit_system: bad\n\n\n"


def _patch_yaml(content: str) -> Any:
    """Return a context manager patching configuration.yaml content."""
    return patch_yaml_files({YAML_CONFIG_FILE: content})


def _patch_yaml_files(files: dict[str, str]) -> Any:
    """Return a context manager patching multiple yaml files."""
    return patch_yaml_files(files)


def normalize_yaml_files(check_dict: dict[str, Any]) -> list[str]:
    """Remove configuration path from ['yaml_files']."""
    root = get_test_config_dir()
    return [key.replace(root, "...") for key in sorted(check_dict["yaml_files"].keys())]


@test
def bad_core_config() -> None:
    """Test a bad core config setup."""
    with mock_is_file_cm(), _patch_yaml(BAD_CORE_CONFIG):
        res = check_config.check(get_test_config_dir())
    expect(set(res["except"].keys())).to_equal({"homeassistant"})
    expect(res["except"]["homeassistant"][1]).to_equal({"unit_system": "bad"})
    expect(res["warn"]).to_equal({})


def mock_is_file_cm() -> Any:
    """Context manager equivalent of the ``mock_is_file`` fixture."""
    return patch(
        "os.path.isfile", lambda path: not str(path).endswith("entity_registry.yaml")
    )


def reset_log_level_cm() -> Any:
    """Context manager equivalent of the ``reset_log_level`` fixture."""

    class _Reset:
        def __enter__(self) -> None:
            self._logger = logging.getLogger("homeassistant.loader")
            self._orig = self._logger.level

        def __exit__(self, *exc: object) -> None:
            self._logger.setLevel(self._orig)

    return _Reset()


@test
def config_platform_valid() -> None:
    """Test a valid platform setup."""
    with (
        reset_log_level_cm(),
        mock_is_file_cm(),
        _patch_yaml(BASE_CONFIG + "light:\n  platform: demo"),
    ):
        res = check_config.check(get_test_config_dir())
    expect(set(res["components"].keys())).to_equal({"homeassistant", "light"})
    expect(res["components"]["light"]).to_equal([{"platform": "demo"}])
    expect(res["except"]).to_equal({})
    expect(res["secret_cache"]).to_equal({})
    expect(res["secrets"]).to_equal({})
    expect(res["warn"]).to_equal({})
    expect(len(res["yaml_files"])).to_equal(1)


@test.cases(
    test.case(
        "missing-component",
        yaml=BASE_CONFIG + "beer:",
        platforms={"homeassistant"},
        error="Integration error: beer - Integration 'beer' not found.",
    ),
    test.case(
        "missing-platform",
        yaml=BASE_CONFIG + "light:\n  platform: beer",
        platforms={"homeassistant", "light"},
        error=(
            "Platform error 'light' from integration 'beer' - "
            "Integration 'beer' not found."
        ),
    ),
)
def component_platform_not_found(
    yaml: str, platforms: set[str], error: str
) -> None:
    """Test errors if component or platform not found."""
    with reset_log_level_cm(), mock_is_file_cm(), _patch_yaml(yaml):
        res = check_config.check(get_test_config_dir())
    expect(set(res["components"].keys())).to_equal(platforms)
    expect(res["except"]).to_equal({})
    expect(res["secret_cache"]).to_equal({})
    expect(res["secrets"]).to_equal({})
    expect(res["warn"]).to_equal({check_config.WARNING_STR: [error]})
    expect(len(res["yaml_files"])).to_equal(1)


@test
def secrets() -> None:
    """Test secrets config checking method."""
    files = {
        get_test_config_dir(YAML_CONFIG_FILE): BASE_CONFIG
        + "http:\n  cors_allowed_origins: !secret http_pw",
        get_test_config_dir("secrets.yaml"): (
            "logger: debug\nhttp_pw: http://google.com"
        ),
    }
    with reset_log_level_cm(), mock_is_file_cm(), _patch_yaml_files(files):
        res = check_config.check(get_test_config_dir(), True)

    expect(res["except"]).to_equal({})
    expect(set(res["components"].keys())).to_equal({"homeassistant", "http"})
    expect(res["components"]["http"]).to_equal(
        {
            "cors_allowed_origins": ["http://google.com"],
            "ip_ban_enabled": True,
            "login_attempts_threshold": -1,
            "server_port": 8123,
            "ssl_profile": "modern",
            "use_x_frame_options": True,
        }
    )
    expect(res["secret_cache"]).to_equal(
        {get_test_config_dir("secrets.yaml"): {"http_pw": "http://google.com"}}
    )
    expect(res["secrets"]).to_equal({"http_pw": "http://google.com"})
    expect(res["warn"]).to_equal({})
    expect(normalize_yaml_files(res)).to_equal(
        [".../configuration.yaml", ".../secrets.yaml"]
    )


@test
def package_invalid() -> None:
    """Test an invalid package."""
    with (
        reset_log_level_cm(),
        mock_is_file_cm(),
        _patch_yaml(BASE_CONFIG + '  packages:\n    p1:\n      group: ["a"]'),
    ):
        res = check_config.check(get_test_config_dir())

    expect(res["except"]).to_equal({})
    expect(set(res["components"].keys())).to_equal({"homeassistant"})
    expect(res["secret_cache"]).to_equal({})
    expect(res["secrets"]).to_equal({})
    expect(set(res["warn"].keys())).to_equal({"homeassistant.packages.p1.group"})
    expect(res["warn"]["homeassistant.packages.p1.group"][1]).to_equal(
        {"group": ["a"]}
    )
    expect(len(res["yaml_files"])).to_equal(1)


@test
def bootstrap_error() -> None:
    """Test a valid platform setup."""
    with (
        reset_log_level_cm(),
        _patch_yaml(BASE_CONFIG + "automation: !include no.yaml"),
    ):
        res = check_config.check(get_test_config_dir(YAML_CONFIG_FILE))
    err = res["except"].pop(check_config.ERROR_STR)
    expect(len(err)).to_equal(1)
    expect(res["except"]).to_equal({})
    expect(res["components"]).to_equal({})  # No components, load failed
    expect(res["secret_cache"]).to_equal({})
    expect(res["secrets"]).to_equal({})
    expect(res["warn"]).to_equal({})
    expect(res["yaml_files"]).to_equal({})


@test
def run_json_flag_only() -> None:
    """Test that --json flag works independently."""
    with (
        reset_log_level_cm(),
        mock_is_file_cm(),
        _patch_yaml(BASE_CONFIG),
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", "--json"]),
    ):
        mock_check.return_value = {
            "except": {"domain1": ["error1", "error2"]},
            "warn": {"domain2": ["warning1"]},
            "components": {"homeassistant": {}, "light": {}, "http": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        exit_code = check_config.run(None)

        # Should exit with code 1 (1 domain with errors)
        expect(exit_code).to_equal(1)

        # Should have printed JSON
        expect(mock_print.call_count).to_equal(1)
        json_output = mock_print.call_args[0][0]

        parsed_json = json.loads(json_output)

        expect("config_dir" in parsed_json).to_be(True)
        expect("total_errors" in parsed_json).to_be(True)
        expect("total_warnings" in parsed_json).to_be(True)
        expect("errors" in parsed_json).to_be(True)
        expect("warnings" in parsed_json).to_be(True)
        expect("components" in parsed_json).to_be(True)

        expect(parsed_json["total_errors"]).to_equal(2)
        expect(parsed_json["total_warnings"]).to_equal(1)
        expect(parsed_json["errors"]).to_equal({"domain1": ["error1", "error2"]})
        expect(parsed_json["warnings"]).to_equal({"domain2": ["warning1"]})
        expect(set(parsed_json["components"])).to_equal(
            {"homeassistant", "light", "http"}
        )


@test
def run_fail_on_warnings_flag_only() -> None:
    """Test that --fail-on-warnings flag works independently."""
    # Test with warnings only
    with (
        reset_log_level_cm(),
        mock_is_file_cm(),
        _patch_yaml(BASE_CONFIG),
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", "--fail-on-warnings"]),
    ):
        mock_check.return_value = {
            "except": {},
            "warn": {"light": ["warning message"]},
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        exit_code = check_config.run(None)
        expect(exit_code).to_equal(1)  # Should exit non-zero due to warnings

    # Test with no warnings or errors
    with patch.object(check_config, "check") as mock_check:
        mock_check.return_value = {
            "except": {},
            "warn": {},
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        exit_code = check_config.run(["--fail-on-warnings"])
        expect(exit_code).to_equal(0)

    # Test with both errors and warnings
    with patch.object(check_config, "check") as mock_check:
        mock_check.return_value = {
            "except": {"domain1": ["error"]},
            "warn": {"domain2": ["warning"]},
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        exit_code = check_config.run(["--fail-on-warnings"])
        expect(exit_code).to_equal(1)


@test
def run_json_output_structure() -> None:
    """Test JSON output contains all required fields with correct types."""
    with (
        reset_log_level_cm(),
        mock_is_file_cm(),
        _patch_yaml(BASE_CONFIG),
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", "--json", "--config", "/test/path"]),
    ):
        mock_check.return_value = {
            "except": {"domain1": ["error1", {"config": "bad"}]},
            "warn": {"domain2": ["warning1", {"config": "deprecated"}]},
            "components": {"homeassistant": {}, "light": {}, "automation": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        exit_code = check_config.run(None)

        json_output = mock_print.call_args[0][0]
        parsed_json = json.loads(json_output)

        expect(exit_code).to_equal(1)

        for field in (
            "config_dir",
            "total_errors",
            "total_warnings",
            "errors",
            "warnings",
            "components",
        ):
            expect(field in parsed_json).to_be(True)

        expect(isinstance(parsed_json["config_dir"], str)).to_be(True)
        expect(isinstance(parsed_json["total_errors"], int)).to_be(True)
        expect(isinstance(parsed_json["total_warnings"], int)).to_be(True)
        expect(isinstance(parsed_json["errors"], dict)).to_be(True)
        expect(isinstance(parsed_json["warnings"], dict)).to_be(True)
        expect(isinstance(parsed_json["components"], list)).to_be(True)

        expect(parsed_json["total_errors"]).to_equal(2)
        expect(parsed_json["total_warnings"]).to_equal(2)

        expect(all(isinstance(comp, str) for comp in parsed_json["components"])).to_be(
            True
        )
        expect(set(parsed_json["components"])).to_equal(
            {"homeassistant", "light", "automation"}
        )


@test.cases(
    test.case("no-errors-no-warnings-no-flags", errors={}, warnings={}, flags=[], expected=0),
    test.case("no-errors-no-warnings-json", errors={}, warnings={}, flags=["--json"], expected=0),
    test.case(
        "no-errors-no-warnings-fow",
        errors={},
        warnings={},
        flags=["--fail-on-warnings"],
        expected=0,
    ),
    test.case(
        "no-errors-no-warnings-both",
        errors={},
        warnings={},
        flags=["--json", "--fail-on-warnings"],
        expected=0,
    ),
    test.case(
        "warnings-only-no-flags",
        errors={},
        warnings={"domain": ["warning"]},
        flags=[],
        expected=0,
    ),
    test.case(
        "warnings-only-json",
        errors={},
        warnings={"domain": ["warning"]},
        flags=["--json"],
        expected=0,
    ),
    test.case(
        "warnings-only-fow",
        errors={},
        warnings={"domain": ["warning"]},
        flags=["--fail-on-warnings"],
        expected=1,
    ),
    test.case(
        "warnings-only-both",
        errors={},
        warnings={"domain": ["warning"]},
        flags=["--json", "--fail-on-warnings"],
        expected=1,
    ),
    test.case(
        "errors-only-no-flags",
        errors={"domain": ["error"]},
        warnings={},
        flags=[],
        expected=1,
    ),
    test.case(
        "errors-only-json",
        errors={"domain": ["error"]},
        warnings={},
        flags=["--json"],
        expected=1,
    ),
    test.case(
        "errors-only-fow",
        errors={"domain": ["error"]},
        warnings={},
        flags=["--fail-on-warnings"],
        expected=1,
    ),
    test.case(
        "errors-only-both",
        errors={"domain": ["error"]},
        warnings={},
        flags=["--json", "--fail-on-warnings"],
        expected=1,
    ),
    test.case(
        "both-no-flags",
        errors={"domain": ["error"]},
        warnings={"domain2": ["warning"]},
        flags=[],
        expected=1,
    ),
    test.case(
        "both-json",
        errors={"domain": ["error"]},
        warnings={"domain2": ["warning"]},
        flags=["--json"],
        expected=1,
    ),
    test.case(
        "both-fow",
        errors={"domain": ["error"]},
        warnings={"domain2": ["warning"]},
        flags=["--fail-on-warnings"],
        expected=1,
    ),
    test.case(
        "both-both",
        errors={"domain": ["error"]},
        warnings={"domain2": ["warning"]},
        flags=["--json", "--fail-on-warnings"],
        expected=1,
    ),
    test.case(
        "multi-error-domains-no-flags",
        errors={"d1": ["e1"], "d2": ["e2"]},
        warnings={},
        flags=[],
        expected=1,
    ),
    test.case(
        "multi-errors-and-warnings-fow",
        errors={"d1": ["e1"], "d2": ["e2"]},
        warnings={"d3": ["w1"]},
        flags=["--fail-on-warnings"],
        expected=1,
    ),
)
def run_exit_code_logic(
    errors: dict[str, list[str]],
    warnings: dict[str, list[str]],
    flags: list[str],
    expected: int,
) -> None:
    """Test exit code logic for all flag combinations."""
    with (
        patch("builtins.print"),
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", *flags]),
    ):
        mock_check.return_value = {
            "except": errors,
            "warn": warnings,
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        exit_code = check_config.run(None)
        expect(exit_code).to_equal(expected)


@test
def run_human_readable_still_works() -> None:
    """Test that human-readable output still works without JSON flag."""
    with (
        reset_log_level_cm(),
        mock_is_file_cm(),
        _patch_yaml(BASE_CONFIG),
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
    ):
        mock_check.return_value = {
            "except": {},
            "warn": {},
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        check_config.run(None)

        printed_outputs = [
            call[0][0] if call[0] else "" for call in mock_print.call_args_list
        ]
        testing_message_found = any(
            "Testing configuration at" in output for output in printed_outputs
        )
        expect(testing_message_found).to_be(True)


@test
def run_with_config_path() -> None:
    """Test that config path is correctly included in JSON output."""
    test_config_path = "/custom/config/path"
    with (
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", "--json", "--config", test_config_path]),
    ):
        mock_check.return_value = {
            "except": {},
            "warn": {},
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        check_config.run(None)

        json_output = mock_print.call_args[0][0]
        parsed_json = json.loads(json_output)

        expected_path = os.path.join(os.getcwd(), test_config_path)
        expect(parsed_json["config_dir"]).to_equal(expected_path)


# Flag Interaction Tests


@test
def unknown_arguments_with_json() -> None:
    """Test that unknown arguments are handled properly with JSON flag."""
    with (
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", "--json", "--unknown-flag", "value"]),
    ):
        mock_check.return_value = {
            "except": {},
            "warn": {},
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        check_config.run(None)

        # Should still print unknown argument warning AND JSON
        expect(mock_print.call_count).to_equal(2)

        # First call should be the unknown argument warning
        unknown_warning = mock_print.call_args_list[0][0][0]
        expect("Unknown arguments" in unknown_warning).to_be(True)
        expect("unknown-flag" in unknown_warning).to_be(True)

        # Second call should be valid JSON
        json_output = mock_print.call_args_list[1][0][0]
        parsed_json = json.loads(json_output)
        expect("config_dir" in parsed_json).to_be(True)


@test
def info_flag_with_json() -> None:
    """Test how --info flag interacts with --json."""
    with (
        reset_log_level_cm(),
        mock_is_file_cm(),
        _patch_yaml(BASE_CONFIG),
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", "--json", "--info", "light"]),
    ):
        mock_check.return_value = {
            "except": {},
            "warn": {},
            "components": {"homeassistant": {}, "light": {"platform": "demo"}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        # Test --json with --info - JSON should take precedence
        exit_code = check_config.run(None)

        expect(exit_code).to_equal(0)
        expect(mock_print.call_count).to_equal(1)

        # Should be JSON output, not info output
        json_output = json.loads(mock_print.call_args[0][0])
        expect("config_dir" in json_output).to_be(True)
        expect("components" in json_output).to_be(True)
        expect("light" in json_output["components"]).to_be(True)


@test.cases(
    test.case(
        "short-flag",
        flags=["-c", "/test/path"],
        expected_config_part="/test/path",
    ),
    test.case(
        "long-flag",
        flags=["--config", "/test/path"],
        expected_config_part="/test/path",
    ),
    test.case(
        "json-and-short-relative",
        flags=["--json", "-c", "relative/path"],
        expected_config_part="relative/path",
    ),
    test.case(
        "json-and-long-dot",
        flags=["--config", ".", "--json"],
        expected_config_part=".",
    ),
)
def config_flag_variations(flags: list[str], expected_config_part: str) -> None:
    """Test different ways to specify config directory."""
    with (
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", *flags]),
    ):
        mock_check.return_value = {
            "except": {},
            "warn": {},
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        check_config.run(None)

        if "--json" in flags:
            json_output = json.loads(mock_print.call_args[0][0])
            expected_full_path = os.path.join(os.getcwd(), expected_config_part)
            expect(json_output["config_dir"]).to_equal(expected_full_path)


@test
def multiple_config_flags() -> None:
    """Test behavior with multiple config directory specifications."""
    with (
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch(
            "sys.argv",
            ["", "--json", "--config", "/first/path", "--config", "/second/path"],
        ),
    ):
        mock_check.return_value = {
            "except": {},
            "warn": {},
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        # Last config flag should win
        check_config.run(None)

        json_output = json.loads(mock_print.call_args[0][0])
        expected_path = os.path.join(os.getcwd(), "/second/path")
        expect(json_output["config_dir"]).to_equal(expected_path)


@test.cases(
    test.case("no-errors-no-warnings", errors={}, warnings={}, expected=0),
    test.case(
        "errors-only",
        errors={"domain1": ["error"]},
        warnings={},
        expected=1,
    ),
    test.case(
        "warnings-only-with-fow",
        errors={},
        warnings={"domain1": ["warning"]},
        expected=1,
    ),
    test.case(
        "errors-take-precedence",
        errors={"d1": ["e1"]},
        warnings={"d2": ["w1"]},
        expected=1,
    ),
    test.case(
        "multi-errors-and-warnings",
        errors={"d1": ["e1"], "d2": ["e2"]},
        warnings={"d3": ["w1"]},
        expected=1,
    ),
)
def fail_on_warnings_with_json_combinations(
    errors: dict[str, list[str]],
    warnings: dict[str, list[str]],
    expected: int,
) -> None:
    """Test --fail-on-warnings with --json in various scenarios."""
    with (
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", "--json", "--fail-on-warnings"]),
    ):
        mock_check.return_value = {
            "except": errors,
            "warn": warnings,
            "components": {"homeassistant": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        exit_code = check_config.run(None)
        expect(exit_code).to_equal(expected)

        # Should still output valid JSON
        json_output = json.loads(mock_print.call_args[0][0])
        expect(json_output["total_errors"]).to_equal(
            sum(len(e) for e in errors.values())
        )
        expect(json_output["total_warnings"]).to_equal(
            sum(len(w) for w in warnings.values())
        )
