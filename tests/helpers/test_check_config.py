"""Test check_config helper."""

import logging
from unittest.mock import Mock, patch

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.config import YAML_CONFIG_FILE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.check_config import (
    CheckConfigError,
    HomeAssistantConfig,
    async_check_ha_config_file,
)
from homeassistant.helpers.condition import CONDITIONS
from homeassistant.helpers.trigger import TRIGGERS
from homeassistant.requirements import RequirementsNotFound

from tests.common import (
    MockModule,
    MockPlatform,
    mock_integration,
    mock_platform,
    patch_yaml_files,
)
from tests.hass_fixtures import hass

_LOGGER = logging.getLogger(__name__)

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


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


def log_ha_config(conf: HomeAssistantConfig) -> None:
    """Log the returned config."""
    _LOGGER.debug("CONFIG - %s lines - %s errors", len(conf), len(conf.errors))
    for cnt, (key, val) in enumerate(conf.items()):
        _LOGGER.debug("#%s - %s: %s", cnt + 1, key, val)
    for cnt, err in enumerate(conf.errors):
        _LOGGER.debug("error[%s] = %s", cnt, err)


def _assert_warnings_errors(
    res: HomeAssistantConfig,
    expected_warnings: list[CheckConfigError],
    expected_errors: list[CheckConfigError],
) -> None:
    expect(len(res.warnings)).to_equal(len(expected_warnings))
    expect(len(res.errors)).to_equal(len(expected_errors))

    expected_warning_str = ""
    expected_error_str = ""

    for idx, expected_warning in enumerate(expected_warnings):
        expect(res.warnings[idx]).to_equal(expected_warning)
        expected_warning_str += expected_warning.message
    expect(res.warning_str).to_equal(expected_warning_str)

    for idx, expected_error in enumerate(expected_errors):
        expect(res.errors[idx]).to_equal(expected_error)
        expected_error_str += expected_error.message
    expect(res.error_str).to_equal(expected_error_str)


@test
async def bad_core_config(hass: HomeAssistant = Depends(hass)) -> None:
    """Test a bad core config setup."""
    files = {YAML_CONFIG_FILE: BAD_CORE_CONFIG}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        error = CheckConfigError(
            (
                f"Invalid config for 'homeassistant' at {YAML_CONFIG_FILE}, line 2:"
                " not a valid value for dictionary value 'unit_system', got 'bad'"
            ),
            "homeassistant",
            {"unit_system": "bad"},
        )
        _assert_warnings_errors(res, [], [error])


@test
async def config_platform_valid(hass: HomeAssistant = Depends(hass)) -> None:
    """Test a valid platform setup."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "light:\n  platform: demo"}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant", "light"})
        expect(res["light"]).to_equal([{"platform": "demo"}])
        _assert_warnings_errors(res, [], [])


@test
async def integration_not_found(hass: HomeAssistant = Depends(hass)) -> None:
    """Test errors if integration not found."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "beer:"}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})
        warning = CheckConfigError(
            "Integration error: beer - Integration 'beer' not found.", None, None
        )
        _assert_warnings_errors(res, [warning], [])


@test
async def integrationt_requirement_not_found(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test errors if integration with a requirement not found not found."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "test_custom_component:"}
    with (
        patch(
            "homeassistant.helpers.check_config.async_get_integration_with_requirements",
            side_effect=RequirementsNotFound("test_custom_component", ["any"]),
        ),
        patch("os.path.isfile", return_value=True),
        patch_yaml_files(files),
    ):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})
        warning = CheckConfigError(
            (
                "Integration error: test_custom_component - Requirements for"
                " test_custom_component not found: ['any']."
            ),
            None,
            None,
        )
        _assert_warnings_errors(res, [warning], [])


@test
async def integration_not_found_recovery_mode(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test no errors if integration not found in recovery mode."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "beer:"}
    hass.config.recovery_mode = True
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})
        _assert_warnings_errors(res, [], [])


@test
async def integration_not_found_safe_mode(hass: HomeAssistant = Depends(hass)) -> None:
    """Test no errors if integration not found in safe mode."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "beer:"}
    hass.config.safe_mode = True
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})
        _assert_warnings_errors(res, [], [])


@test
async def integration_import_error(hass: HomeAssistant = Depends(hass)) -> None:
    """Test errors if integration with a requirement not found not found."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "light:"}
    with (
        patch(
            "homeassistant.loader.Integration.async_get_component",
            side_effect=ImportError("blablabla"),
        ),
        patch("os.path.isfile", return_value=True),
        patch_yaml_files(files),
    ):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})
        warning = CheckConfigError(
            "Component error: light - blablabla",
            None,
            None,
        )
        _assert_warnings_errors(res, [warning], [])


@test.cases(
    test.case(
        "frontend",
        integration="frontend",
        errors=1,
        warnings=0,
        message="'blah' is an invalid option for 'frontend'",
    ),
    test.case(
        "http",
        integration="http",
        errors=1,
        warnings=0,
        message="'blah' is an invalid option for 'http'",
    ),
    test.case(
        "logger",
        integration="logger",
        errors=0,
        warnings=1,
        message="'blah' is an invalid option for 'logger'",
    ),
)
async def integration_schema_error(
    integration: str,
    errors: int,
    warnings: int,
    message: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test schema error in integration."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + f"frontend:\n{integration}:\n    blah:"}
    hass.config.safe_mode = True
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(len(res.errors)).to_equal(errors)
        expect(len(res.warnings)).to_equal(warnings)

        for err in res.errors:
            expect(err.message).to_contain(message)
        for warn in res.warnings:
            expect(warn.message).to_contain(message)


@test
async def platform_not_found(hass: HomeAssistant = Depends(hass)) -> None:
    """Test errors if platform not found."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "light:\n  platform: beer"}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant", "light"})
        expect(res["light"]).to_equal([])

        warning = CheckConfigError(
            (
                "Platform error 'light' from integration 'beer' - "
                "Integration 'beer' not found."
            ),
            None,
            None,
        )
        _assert_warnings_errors(res, [warning], [])


@test
async def platform_not_found_recovery_mode(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test no errors if platform not found in recovery mode."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "light:\n  platform: beer"}
    hass.config.recovery_mode = True
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant", "light"})
        expect(res["light"]).to_equal([])

        _assert_warnings_errors(res, [], [])


@test
async def platform_not_found_safe_mode(hass: HomeAssistant = Depends(hass)) -> None:
    """Test no errors if platform not found in safe mode."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "light:\n  platform: beer"}
    hass.config.safe_mode = True
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant", "light"})
        expect(res["light"]).to_equal([])

        _assert_warnings_errors(res, [], [])


@test.cases(
    test.case(
        "valid-option",
        extra_config="blah:\n  - platform: test\n    option1: abc",
        warnings=0,
        message=None,
        config=None,
    ),
    test.case(
        "wrong-type",
        extra_config="blah:\n  - platform: test\n    option1: 123",
        warnings=1,
        message="expected str for dictionary value",
        config={"option1": 123, "platform": "test"},
    ),
    test.case(
        "attached-config-unvalidated",
        extra_config="blah:\n  - platform: test\n    old: blah\n    option1: 123",
        warnings=1,
        message="expected str for dictionary value",
        config={"old": "blah", "option1": 123, "platform": "test"},
    ),
    test.case(
        "base-platform-config-error",
        extra_config="blah:\n  - paltfrom: test\n",
        warnings=1,
        message="required key 'platform' not provided",
        config={"paltfrom": "test"},
    ),
)
async def platform_schema_error(
    extra_config: str,
    warnings: int,
    message: str | None,
    config: dict | None,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test schema error in platform."""
    comp_platform_schema = cv.PLATFORM_SCHEMA.extend({vol.Remove("old"): str})
    comp_platform_schema_base = comp_platform_schema.extend({}, extra=vol.ALLOW_EXTRA)
    mock_integration(
        hass,
        MockModule("blah", platform_schema_base=comp_platform_schema_base),
    )
    test_platform_schema = comp_platform_schema.extend({"option1": str})
    mock_platform(
        hass,
        "test.blah",
        MockPlatform(platform_schema=test_platform_schema),
    )

    files = {YAML_CONFIG_FILE: BASE_CONFIG + extra_config}
    hass.config.safe_mode = True
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(len(res.errors)).to_equal(0)
        expect(len(res.warnings)).to_equal(warnings)

        for warn in res.warnings:
            expect(warn.message).to_contain(message)
            expect(warn.config).to_equal(config)


@test
async def config_platform_import_error(hass: HomeAssistant = Depends(hass)) -> None:
    """Test errors if config platform fails to import."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "light:\n  platform: beer"}
    with (
        patch(
            "homeassistant.loader.Integration.async_get_platform",
            side_effect=ImportError("blablabla"),
        ),
        patch("os.path.isfile", return_value=True),
        patch("homeassistant.loader.Integration.platforms_exists", return_value=True),
        patch_yaml_files(files),
    ):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})
        error = CheckConfigError(
            "Error importing config platform light: blablabla",
            None,
            None,
        )
        _assert_warnings_errors(res, [], [error])


@test
async def platform_import_error(hass: HomeAssistant = Depends(hass)) -> None:
    """Test errors if platform not found."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "light:\n  platform: demo"}
    with (
        patch(
            "homeassistant.loader.Integration.async_get_platform",
            side_effect=[None, ImportError("blablabla")],
        ),
        patch("homeassistant.loader.Integration.platforms_exists", return_value=True),
        patch("os.path.isfile", return_value=True),
        patch_yaml_files(files),
    ):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant", "light"})
        warning = CheckConfigError(
            "Platform error 'light' from integration 'demo' - blablabla",
            None,
            None,
        )
        _assert_warnings_errors(res, [warning], [])


@test
async def package_invalid(hass: HomeAssistant = Depends(hass)) -> None:
    """Test a platform setup with an invalid package config."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + '  packages:\n    p1:\n      group: ["a"]'}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})

        warning = CheckConfigError(
            (
                "Setup of package 'p1' failed: integration 'group' cannot be merged"
                ", expected a dict"
            ),
            "homeassistant.packages.p1.group",
            {"group": ["a"]},
        )
        _assert_warnings_errors(res, [warning], [])


@test
async def package_definition_invalid_slug_keys(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test a platform setup with a broken package: keys must be slugs."""
    files = {
        YAML_CONFIG_FILE: BASE_CONFIG
        + '  packages:\n    not a slug:\n      group: ["a"]'
    }
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})

        warning = CheckConfigError(
            (
                "Setup of package 'not a slug' failed: Invalid package definition 'not a slug': invalid slug not a "
                "slug (try not_a_slug). Package will not be initialized"
            ),
            "homeassistant.packages.not a slug",
            {"group": ["a"]},
        )
        _assert_warnings_errors(res, [warning], [])


@test
async def package_definition_invalid_dict(hass: HomeAssistant = Depends(hass)) -> None:
    """Test a platform setup with a broken package: packages must be dicts."""
    files = {
        YAML_CONFIG_FILE: BASE_CONFIG
        + '  packages:\n    not_a_dict:\n      - group: ["a"]'
    }
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})

        warning = CheckConfigError(
            (
                "Setup of package 'not_a_dict' failed: Invalid package definition 'not_a_dict': expected a "
                "dictionary. Package will not be initialized"
            ),
            "homeassistant.packages.not_a_dict",
            [{"group": ["a"]}],
        )
        _assert_warnings_errors(res, [warning], [])


@test
async def package_schema_invalid(hass: HomeAssistant = Depends(hass)) -> None:
    """Test an invalid platform config because of severely broken packages section."""
    files = {
        YAML_CONFIG_FILE: "homeassistant:\n  packages:\n    - must\n    - not\n    - be\n    - a\n    - list"
    }
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        error = CheckConfigError(
            (
                f"Invalid config for 'homeassistant' at {YAML_CONFIG_FILE}, line 2:"
                " expected a dictionary for dictionary value 'packages', got ['must', 'not', 'be', 'a', 'list']"
            ),
            "homeassistant",
            {"packages": ["must", "not", "be", "a", "list"]},
        )
        _assert_warnings_errors(res, [], [error])


@test
async def missing_included_file(hass: HomeAssistant = Depends(hass)) -> None:
    """Test missing included file."""
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "automation: !include no.yaml"}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(len(res.errors)).to_equal(1)
        expect(len(res.warnings)).to_equal(0)

        expect(res.errors[0].message.startswith("Error loading")).to_be_truthy()
        expect(res.errors[0].domain).to_be_none()
        expect(res.errors[0].config).to_be_none()


@test
async def automation_config_platform(hass: HomeAssistant = Depends(hass)) -> None:
    """Test automation async config."""
    # Remove keys pre-populated by the test fixture to simulate
    # the check_config script which doesn't run bootstrap.
    del hass.data[TRIGGERS]
    del hass.data[CONDITIONS]

    files = {
        YAML_CONFIG_FILE: BASE_CONFIG
        + """
automation:
  use_blueprint:
    path: test_event_service.yaml
    input:
      trigger_event: blueprint_event
      service_to_call: test.automation
input_datetime:
""",
        hass.config.path("blueprints/automation/test_event_service.yaml"): """
blueprint:
  name: "Call service based on event"
  domain: automation
  input:
    trigger_event:
    service_to_call:
trigger:
  platform: event
  event_type: !input trigger_event
condition:
  condition: template
  value_template: "{{ true }}"
action:
  service: !input service_to_call
""",
    }
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        expect(len(res.get("automation", []))).to_equal(1)
        expect(len(res.errors)).to_equal(0)
        expect(len(res.warnings)).to_equal(0)
        expect(res).to_contain("input_datetime")


@test.cases(
    test.case(
        "unexpected",
        exception=Exception("Broken"),
        errors=1,
        warnings=0,
        message="Unexpected error calling config validator: Broken",
    ),
    test.case(
        "hass-error",
        exception=HomeAssistantError("Broken"),
        errors=0,
        warnings=1,
        message="Invalid config for 'bla' at configuration.yaml, line 11: Broken",
    ),
)
async def config_platform_raise(
    exception: Exception,
    errors: int,
    warnings: int,
    message: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test bad config validation platform."""
    mock_platform(
        hass,
        "bla.config",
        Mock(async_validate_config=Mock(side_effect=exception)),
    )
    files = {
        YAML_CONFIG_FILE: BASE_CONFIG
        + """
bla:
  value: 1
""",
    }
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        error = CheckConfigError(
            message,
            "bla",
            {"value": 1},
        )
        _assert_warnings_errors(res, [error] * warnings, [error] * errors)


@test
async def removed_yaml_support(hass: HomeAssistant = Depends(hass)) -> None:
    """Test config validation check with removed CONFIG_SCHEMA without raise if present."""
    mock_integration(
        hass,
        MockModule(
            domain="bla", config_schema=cv.removed("bla", raise_if_present=False)
        ),
        False,
    )
    files = {YAML_CONFIG_FILE: BASE_CONFIG + "bla:\n  platform: demo"}
    with patch("os.path.isfile", return_value=True), patch_yaml_files(files):
        res = await async_check_ha_config_file(hass)
        log_ha_config(res)

        expect(res.keys()).to_equal({"homeassistant"})
        _assert_warnings_errors(res, [], [])
