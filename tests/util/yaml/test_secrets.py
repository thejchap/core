"""Test Home Assistant secret substitution in YAML files."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

from tryke import Depends, expect, fixture, test

from homeassistant.config import YAML_CONFIG_FILE, load_yaml_config_file
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import yaml as yaml_util
from homeassistant.util.yaml import loader as yaml_loader

from tests.common import get_test_config_dir, patch_yaml_files
from tests.hass_fixtures import LogCapture, caplog


@dataclass(frozen=True)
class YamlFile:
    """Represents a .yaml file used for testing."""

    path: Path
    contents: str


def load_config_file(config_file_path: Path, files: list[YamlFile]):
    """Patch secret files and return the loaded config file."""
    patch_files = {x.path.as_posix(): x.contents for x in files}
    with patch_yaml_files(patch_files):
        return load_yaml_config_file(
            config_file_path.as_posix(),
            yaml_loader.Secrets(Path(get_test_config_dir())),
        )


@fixture
def filepaths() -> dict[str, Path]:
    """Return a dictionary of filepaths for testing."""
    config_dir = Path(get_test_config_dir())
    return {
        "config": config_dir,
        "sub_folder": config_dir / "subFolder",
        "unrelated": config_dir / "unrelated",
    }


@fixture
def default_config(filepaths: dict[str, Path] = Depends(filepaths)) -> YamlFile:
    """Return the default config file for testing."""
    return YamlFile(
        path=filepaths["config"] / YAML_CONFIG_FILE,
        contents=(
            "http:\n"
            "  api_password: !secret http_pw\n"
            "component:\n"
            "  username: !secret comp1_un\n"
            "  password: !secret comp1_pw\n"
            ""
        ),
    )


@fixture
def default_secrets(filepaths: dict[str, Path] = Depends(filepaths)) -> YamlFile:
    """Return the default secrets file for testing."""
    return YamlFile(
        path=filepaths["config"] / yaml_util.SECRET_YAML,
        contents=(
            "http_pw: pwhttp\n"
            "comp1_un: un1\n"
            "comp1_pw: pw1\n"
            "stale_pw: not_used\n"
            "logger: debug\n"
        ),
    )


@test
def secrets_from_yaml(
    default_config: YamlFile = Depends(default_config),
    default_secrets: YamlFile = Depends(default_secrets),
) -> None:
    """Did secrets load ok."""
    loaded_file = load_config_file(
        default_config.path, [default_config, default_secrets]
    )
    expect(loaded_file["http"]).to_equal({"api_password": "pwhttp"})
    expect(loaded_file["component"]).to_equal({"username": "un1", "password": "pw1"})


@test
def secrets_from_parent_folder(
    filepaths: dict[str, Path] = Depends(filepaths),
    default_config: YamlFile = Depends(default_config),
    default_secrets: YamlFile = Depends(default_secrets),
) -> None:
    """Test loading secrets from parent folder."""
    config_file = YamlFile(
        path=filepaths["sub_folder"] / "sub.yaml",
        contents=default_config.contents,
    )
    loaded_file = load_config_file(config_file.path, [config_file, default_secrets])
    expect(loaded_file["http"]).to_equal({"api_password": "pwhttp"})


@test
def secret_overrides_parent(
    filepaths: dict[str, Path] = Depends(filepaths),
    default_config: YamlFile = Depends(default_config),
    default_secrets: YamlFile = Depends(default_secrets),
) -> None:
    """Test loading current directory secret overrides the parent."""
    config_file = YamlFile(
        path=filepaths["sub_folder"] / "sub.yaml", contents=default_config.contents
    )
    sub_secrets = YamlFile(
        path=filepaths["sub_folder"] / yaml_util.SECRET_YAML,
        contents="http_pw: override",
    )

    loaded_file = load_config_file(
        config_file.path, [config_file, default_secrets, sub_secrets]
    )

    expect(loaded_file["http"]).to_equal({"api_password": "override"})


@test
def secrets_from_unrelated_fails(
    filepaths: dict[str, Path] = Depends(filepaths),
    default_secrets: YamlFile = Depends(default_secrets),
) -> None:
    """Test loading secrets from unrelated folder fails."""
    config_file = YamlFile(
        path=filepaths["sub_folder"] / "sub.yaml",
        contents="http:\n  api_password: !secret test",
    )
    unrelated_secrets = YamlFile(
        path=filepaths["unrelated"] / yaml_util.SECRET_YAML, contents="test: failure"
    )
    expect(
        lambda: load_config_file(
            config_file.path, [config_file, default_secrets, unrelated_secrets]
        )
    ).to_raise(HomeAssistantError, match="Secret test not defined")


@test
def secrets_logger_removed(
    filepaths: dict[str, Path] = Depends(filepaths),
    default_secrets: YamlFile = Depends(default_secrets),
) -> None:
    """Ensure logger: debug gets removed from secrets file once logger is configured."""
    config_file = YamlFile(
        path=filepaths["config"] / YAML_CONFIG_FILE,
        contents="api_password: !secret logger",
    )
    expect(
        lambda: load_config_file(config_file.path, [config_file, default_secrets])
    ).to_raise(HomeAssistantError, match="Secret logger not defined")


@test
def bad_logger_value(
    filepaths: dict[str, Path] = Depends(filepaths),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Ensure only logger: debug is allowed in secret file."""
    config_file = YamlFile(
        path=filepaths["config"] / YAML_CONFIG_FILE,
        contents="api_password: !secret pw",
    )
    secrets_file = YamlFile(
        path=filepaths["config"] / yaml_util.SECRET_YAML,
        contents="logger: info\npw: abc",
    )
    with caplog.at_level(logging.ERROR):
        load_config_file(config_file.path, [config_file, secrets_file])
        expect(
            "Error in secrets.yaml: 'logger: debug' expected, but 'logger: info' found"
            in caplog.messages
        ).to_be(True)


@test
def secrets_are_not_dict(
    filepaths: dict[str, Path] = Depends(filepaths),
    default_config: YamlFile = Depends(default_config),
) -> None:
    """Did secrets handle non-dict file."""
    non_dict_secrets = YamlFile(
        path=filepaths["config"] / yaml_util.SECRET_YAML,
        contents="- http_pw: pwhttp\n  comp1_un: un1\n  comp1_pw: pw1\n",
    )
    expect(
        lambda: load_config_file(
            default_config.path, [default_config, non_dict_secrets]
        )
    ).to_raise(HomeAssistantError, match="Secrets is not a dictionary")
