"""Test core_config."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
import copy
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import Mock, PropertyMock, patch

from tryke import Depends, expect, fixture, test
from voluptuous import Invalid, MultipleInvalid
from webrtc_models import RTCConfiguration, RTCIceServer

from homeassistant.const import (
    ATTR_ASSUMED_STATE,
    ATTR_FRIENDLY_NAME,
    CONF_AUTH_MFA_MODULES,
    CONF_AUTH_PROVIDERS,
    CONF_CUSTOMIZE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_UNIT_SYSTEM,
    EVENT_CORE_CONFIG_UPDATE,
    __version__,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.core_config import (
    _CUSTOMIZE_DICT_SCHEMA,
    CORE_CONFIG_SCHEMA,
    CORE_STORAGE_KEY,
    DATA_CUSTOMIZE,
    Config,
    ConfigSource,
    async_process_ha_core_config,
    validate_stun_or_turn_url,
)
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity import Entity, EntityPlatformState
from homeassistant.util.unit_system import (
    METRIC_SYSTEM,
    US_CUSTOMARY_SYSTEM,
    UnitSystem,
)

from .common import MockEntityPlatform, MockUser, async_capture_events
from .hass_fixtures import LogCapture, caplog, hass, hass_storage, issue_registry


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


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
def core_config_schema() -> None:
    """Test core config schema."""
    for value in (
        {"unit_system": "K"},
        {"time_zone": "non-exist"},
        {"latitude": "91"},
        {"longitude": -181},
        {"external_url": "not an url"},
        {"internal_url": "not an url"},
        {"currency", 100},
        {"customize": "bla"},
        {"customize": {"light.sensor": 100}},
        {"customize": {"entity_id": []}},
        {"country": "xx"},
        {"language": "xx"},
        {"radius": -10},
        {"webrtc": "bla"},
        {"webrtc": {}},
    ):
        _expect_raises_sync(MultipleInvalid, CORE_CONFIG_SCHEMA, value)

    CORE_CONFIG_SCHEMA(
        {
            "name": "Test name",
            "latitude": "-23.45",
            "longitude": "123.45",
            "external_url": "https://www.example.com",
            "internal_url": "http://example.local",
            "unit_system": "metric",
            "currency": "USD",
            "customize": {"sensor.temperature": {"hidden": True}},
            "country": "SE",
            "language": "sv",
            "radius": "10",
            "webrtc": {"ice_servers": [{"url": "stun:custom_stun_server:3478"}]},
        }
    )


@test
def core_config_schema_internal_external_warning(
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that we warn for internal/external URL with path."""
    CORE_CONFIG_SCHEMA(
        {
            "external_url": "https://www.example.com/bla",
            "internal_url": "http://example.local/yo",
        }
    )

    expect("Invalid external_url set" in caplog.text).to_be_truthy()
    expect("Invalid internal_url set" in caplog.text).to_be_truthy()


@test
def customize_dict_schema() -> None:
    """Test basic customize config validation."""
    values = ({ATTR_FRIENDLY_NAME: None}, {ATTR_ASSUMED_STATE: "2"})

    for val in values:
        _expect_raises_sync(MultipleInvalid, _CUSTOMIZE_DICT_SCHEMA, val)

    expect(
        _CUSTOMIZE_DICT_SCHEMA({ATTR_FRIENDLY_NAME: 2, ATTR_ASSUMED_STATE: "0"})
    ).to_equal(
        {
            ATTR_FRIENDLY_NAME: "2",
            ATTR_ASSUMED_STATE: False,
        }
    )


@test
def webrtc_schema() -> None:
    """Test webrtc config validation."""
    invalid_webrtc_configs = (
        "bla",
        {},
        {"ice_servers": [], "unknown_key": 123},
        {"ice_servers": [{}]},
        {"ice_servers": [{"invalid_key": 123}]},
    )

    valid_webrtc_configs = (
        (
            {"ice_servers": []},
            {"ice_servers": []},
        ),
        (
            {"ice_servers": {"url": "stun:custom_stun_server:3478"}},
            {"ice_servers": [{"url": ["stun:custom_stun_server:3478"]}]},
        ),
        (
            {"ice_servers": [{"url": "stun:custom_stun_server:3478"}]},
            {"ice_servers": [{"url": ["stun:custom_stun_server:3478"]}]},
        ),
        (
            {"ice_servers": [{"url": ["stun:custom_stun_server:3478"]}]},
            {"ice_servers": [{"url": ["stun:custom_stun_server:3478"]}]},
        ),
        (
            {
                "ice_servers": [
                    {
                        "url": ["stun:custom_stun_server:3478"],
                        "username": "bla",
                        "credential": "hunter2",
                    }
                ]
            },
            {
                "ice_servers": [
                    {
                        "url": ["stun:custom_stun_server:3478"],
                        "username": "bla",
                        "credential": "hunter2",
                    }
                ]
            },
        ),
    )

    for config in invalid_webrtc_configs:
        _expect_raises_sync(MultipleInvalid, CORE_CONFIG_SCHEMA, {"webrtc": config})

    for config, validated_webrtc in valid_webrtc_configs:
        validated = CORE_CONFIG_SCHEMA({"webrtc": config})
        expect(validated["webrtc"]).to_equal(validated_webrtc)


@test
def validate_stun_or_turn_url_parsing() -> None:
    """Test validate_stun_or_turn_url."""
    invalid_urls = (
        "custom_stun_server",
        "custom_stun_server:3478",
        "bum:custom_stun_server:3478",
        "http://blah.com:80",
    )

    valid_urls = (
        "stun:custom_stun_server:3478",
        "turn:custom_stun_server:3478",
        "stuns:custom_stun_server:3478",
        "turns:custom_stun_server:3478",
        # The validator does not reject urls with path
        "stun:custom_stun_server:3478/path",
        "turn:custom_stun_server:3478/path",
        "stuns:custom_stun_server:3478/path",
        "turns:custom_stun_server:3478/path",
        # The validator allows any query
        "stun:custom_stun_server:3478?query",
        "turn:custom_stun_server:3478?query",
        "stuns:custom_stun_server:3478?query",
        "turns:custom_stun_server:3478?query",
    )

    for url in invalid_urls:
        _expect_raises_sync(Invalid, validate_stun_or_turn_url, url)

    for url in valid_urls:
        expect(validate_stun_or_turn_url(url)).to_equal(url)


@test
def customize_glob_is_ordered() -> None:
    """Test that customize_glob preserves order."""
    conf = CORE_CONFIG_SCHEMA({"customize_glob": OrderedDict()})
    expect(isinstance(conf["customize_glob"], OrderedDict)).to_be_truthy()


async def _compute_state(hass: HomeAssistant, config: dict[str, Any]) -> State | None:
    await async_process_ha_core_config(hass, config)

    entity = Entity()
    entity.entity_id = "test.test"
    entity.hass = hass
    entity.platform = MockEntityPlatform(hass)
    entity._platform_state = EntityPlatformState.ADDED
    entity.schedule_update_ha_state()

    await hass.async_block_till_done()

    return hass.states.get("test.test")


@test
async def entity_customization(hass: HomeAssistant = Depends(hass)) -> None:
    """Test entity customization through configuration."""
    config = {
        CONF_LATITUDE: 50,
        CONF_LONGITUDE: 50,
        CONF_NAME: "Test",
        CONF_CUSTOMIZE: {"test.test": {"hidden": True}},
    }

    state = await _compute_state(hass, config)

    expect(state.attributes["hidden"]).to_be_truthy()


@test
async def loading_configuration_from_storage(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test loading core config onto hass object."""
    hass_storage["core.config"] = {
        "data": {
            "elevation": 10,
            "latitude": 55,
            "location_name": "Home",
            "longitude": 13,
            "time_zone": "Europe/Copenhagen",
            "unit_system": "metric",
            "external_url": "https://www.example.com",
            "internal_url": "http://example.local",
            "currency": "EUR",
            "country": "SE",
            "language": "sv",
            "radius": 150,
        },
        "key": "core.config",
        "version": 1,
        "minor_version": 4,
    }
    await async_process_ha_core_config(hass, {"allowlist_external_dirs": "/etc"})

    expect(hass.config.latitude).to_equal(55)
    expect(hass.config.longitude).to_equal(13)
    expect(hass.config.elevation).to_equal(10)
    expect(hass.config.location_name).to_equal("Home")
    expect(hass.config.units).to_be(METRIC_SYSTEM)
    expect(hass.config.time_zone).to_equal("Europe/Copenhagen")
    expect(hass.config.external_url).to_equal("https://www.example.com")
    expect(hass.config.internal_url).to_equal("http://example.local")
    expect(hass.config.currency).to_equal("EUR")
    expect(hass.config.country).to_equal("SE")
    expect(hass.config.language).to_equal("sv")
    expect(hass.config.radius).to_equal(150)
    expect(len(hass.config.allowlist_external_dirs)).to_equal(3)
    expect("/etc" in hass.config.allowlist_external_dirs).to_be_truthy()
    expect(hass.config.config_source).to_be(ConfigSource.STORAGE)


@test
async def loading_configuration_from_storage_with_yaml_only(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test loading core and YAML config onto hass object."""
    hass_storage["core.config"] = {
        "data": {
            "elevation": 10,
            "latitude": 55,
            "location_name": "Home",
            "longitude": 13,
            "time_zone": "Europe/Copenhagen",
            "unit_system": "metric",
        },
        "key": "core.config",
        "version": 1,
    }
    await async_process_ha_core_config(
        hass, {"media_dirs": {"mymedia": "/usr"}, "allowlist_external_dirs": "/etc"}
    )

    expect(hass.config.latitude).to_equal(55)
    expect(hass.config.longitude).to_equal(13)
    expect(hass.config.elevation).to_equal(10)
    expect(hass.config.location_name).to_equal("Home")
    expect(hass.config.units).to_be(METRIC_SYSTEM)
    expect(hass.config.time_zone).to_equal("Europe/Copenhagen")
    expect(len(hass.config.allowlist_external_dirs)).to_equal(3)
    expect("/etc" in hass.config.allowlist_external_dirs).to_be_truthy()
    expect(hass.config.media_dirs).to_equal({"mymedia": "/usr"})
    expect(hass.config.config_source).to_be(ConfigSource.STORAGE)


@test
async def migration_and_updating_configuration(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test updating configuration stores the new configuration."""
    core_data = {
        "data": {
            "elevation": 10,
            "latitude": 55,
            "location_name": "Home",
            "longitude": 13,
            "time_zone": "Europe/Copenhagen",
            "unit_system": "imperial",
            "external_url": "https://www.example.com",
            "internal_url": "http://example.local",
            "currency": "BTC",
        },
        "key": "core.config",
        "version": 1,
        "minor_version": 1,
    }
    hass_storage["core.config"] = dict(core_data)
    await async_process_ha_core_config(hass, {"allowlist_external_dirs": "/etc"})
    await hass.config.async_update(latitude=50, currency="USD")

    expected_new_core_data = copy.deepcopy(core_data)
    # From async_update above
    expected_new_core_data["data"]["latitude"] = 50
    expected_new_core_data["data"]["currency"] = "USD"
    # 1.1 -> 1.2 store migration with migrated unit system
    expected_new_core_data["data"]["unit_system_v2"] = "us_customary"
    # 1.1 -> 1.3 defaults for country and language
    expected_new_core_data["data"]["country"] = None
    expected_new_core_data["data"]["language"] = "en"
    # 1.1 -> 1.4 defaults for zone radius
    expected_new_core_data["data"]["radius"] = 100
    # Bumped minor version
    expected_new_core_data["minor_version"] = 4
    expect(hass_storage["core.config"]).to_equal(expected_new_core_data)
    expect(hass.config.latitude).to_equal(50)
    expect(hass.config.currency).to_equal("USD")
    expect(hass.config.country).to_be(None)
    expect(hass.config.language).to_equal("en")
    expect(hass.config.radius).to_equal(100)


@test
async def override_stored_configuration(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test loading core and YAML config onto hass object."""
    hass_storage["core.config"] = {
        "data": {
            "elevation": 10,
            "latitude": 55,
            "location_name": "Home",
            "longitude": 13,
            "time_zone": "Europe/Copenhagen",
            "unit_system": "metric",
        },
        "key": "core.config",
        "version": 1,
    }
    await async_process_ha_core_config(
        hass, {"latitude": 60, "allowlist_external_dirs": "/etc"}
    )

    expect(hass.config.latitude).to_equal(60)
    expect(hass.config.longitude).to_equal(13)
    expect(hass.config.elevation).to_equal(10)
    expect(hass.config.location_name).to_equal("Home")
    expect(hass.config.units).to_be(METRIC_SYSTEM)
    expect(hass.config.time_zone).to_equal("Europe/Copenhagen")
    expect(len(hass.config.allowlist_external_dirs)).to_equal(3)
    expect("/etc" in hass.config.allowlist_external_dirs).to_be_truthy()
    expect(hass.config.config_source).to_be(ConfigSource.YAML)


@test
async def loading_configuration(hass: HomeAssistant = Depends(hass)) -> None:
    """Test loading core config onto hass object."""
    await async_process_ha_core_config(
        hass,
        {
            "latitude": 60,
            "longitude": 50,
            "elevation": 25,
            "name": "Huis",
            "unit_system": "imperial",
            "time_zone": "America/New_York",
            "allowlist_external_dirs": "/etc",
            "external_url": "https://www.example.com",
            "internal_url": "http://example.local",
            "media_dirs": {"mymedia": "/usr"},
            "debug": True,
            "currency": "EUR",
            "country": "SE",
            "language": "sv",
            "radius": 150,
            "webrtc": {"ice_servers": [{"url": "stun:custom_stun_server:3478"}]},
        },
    )

    expect(hass.config.latitude).to_equal(60)
    expect(hass.config.longitude).to_equal(50)
    expect(hass.config.elevation).to_equal(25)
    expect(hass.config.location_name).to_equal("Huis")
    expect(hass.config.units).to_be(US_CUSTOMARY_SYSTEM)
    expect(hass.config.time_zone).to_equal("America/New_York")
    expect(hass.config.external_url).to_equal("https://www.example.com")
    expect(hass.config.internal_url).to_equal("http://example.local")
    expect(len(hass.config.allowlist_external_dirs)).to_equal(3)
    expect("/etc" in hass.config.allowlist_external_dirs).to_be_truthy()
    expect("/usr" in hass.config.allowlist_external_dirs).to_be_truthy()
    expect(hass.config.media_dirs).to_equal({"mymedia": "/usr"})
    expect(hass.config.config_source).to_be(ConfigSource.YAML)
    expect(hass.config.debug).to_be(True)
    expect(hass.config.currency).to_equal("EUR")
    expect(hass.config.country).to_equal("SE")
    expect(hass.config.language).to_equal("sv")
    expect(hass.config.radius).to_equal(150)
    expect(hass.config.webrtc).to_equal(
        RTCConfiguration([RTCIceServer(urls=["stun:custom_stun_server:3478"])])
    )


@test.cases(
    test.case(
        "v2_no_users",
        minor_version=2,
        users=(),
        user_data={},
        default_language="en",
    ),
    test.case(
        "v2_owner_no_data",
        minor_version=2,
        users=({"is_owner": True},),
        user_data={},
        default_language="en",
    ),
    test.case(
        "v2_owner_sv",
        minor_version=2,
        users=({"id": "user1", "is_owner": True},),
        user_data={"user1": {"language": {"language": "sv"}}},
        default_language="sv",
    ),
    test.case(
        "v2_non_owner_sv",
        minor_version=2,
        users=({"id": "user1", "is_owner": False},),
        user_data={"user1": {"language": {"language": "sv"}}},
        default_language="en",
    ),
    test.case(
        "v3_no_users",
        minor_version=3,
        users=(),
        user_data={},
        default_language="en",
    ),
    test.case(
        "v3_owner_no_data",
        minor_version=3,
        users=({"is_owner": True},),
        user_data={},
        default_language="en",
    ),
    test.case(
        "v3_owner_sv",
        minor_version=3,
        users=({"id": "user1", "is_owner": True},),
        user_data={"user1": {"language": {"language": "sv"}}},
        default_language="en",
    ),
    test.case(
        "v3_non_owner_sv",
        minor_version=3,
        users=({"id": "user1", "is_owner": False},),
        user_data={"user1": {"language": {"language": "sv"}}},
        default_language="en",
    ),
)
async def language_default(
    minor_version: int,
    users: tuple[dict[str, Any], ...],
    user_data: dict[str, Any],
    default_language: str,
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test language config default to owner user's language during migration.

    This should only happen if the core store version < 1.3.
    """
    core_data = {
        "data": {},
        "key": "core.config",
        "version": 1,
        "minor_version": minor_version,
    }
    hass_storage["core.config"] = dict(core_data)

    for user_config in users:
        user = MockUser(**user_config).add_to_hass(hass)
        if user.id not in user_data:
            continue
        storage_key = f"frontend.user_data_{user.id}"
        hass_storage[storage_key] = {
            "key": storage_key,
            "version": 1,
            "data": user_data[user.id],
        }

    await async_process_ha_core_config(
        hass,
        {},
    )
    expect(hass.config.language).to_equal(default_language)


@test
async def loading_configuration_default_media_dirs_docker(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test loading core config onto hass object."""
    with patch("homeassistant.core_config.is_docker_env", return_value=True):
        await async_process_ha_core_config(
            hass,
            {
                "name": "Huis",
            },
        )

    expect(hass.config.location_name).to_equal("Huis")
    expect(len(hass.config.allowlist_external_dirs)).to_equal(2)
    expect("/media" in hass.config.allowlist_external_dirs).to_be_truthy()
    expect(hass.config.media_dirs).to_equal({"local": "/media"})


@test
async def loading_configuration_from_packages(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test loading packages config onto hass object config."""
    await async_process_ha_core_config(
        hass,
        {
            "latitude": 39,
            "longitude": -1,
            "elevation": 500,
            "name": "Huis",
            "unit_system": "metric",
            "time_zone": "Europe/Madrid",
            "external_url": "https://www.example.com",
            "internal_url": "http://example.local",
            "packages": {
                "package_1": {"wake_on_lan": None},
                "package_2": {
                    "light": {"platform": "hue"},
                    "media_extractor": None,
                    "sun": None,
                },
            },
        },
    )

    # Empty packages not allowed
    await _expect_raises_async(
        MultipleInvalid,
        async_process_ha_core_config(
            hass,
            {
                "latitude": 39,
                "longitude": -1,
                "elevation": 500,
                "name": "Huis",
                "unit_system": "metric",
                "time_zone": "Europe/Madrid",
                "packages": {"empty_package": None},
            },
        ),
    )


@test.cases(
    test.case(
        "metric",
        unit_system_name="metric",
        expected_unit_system=METRIC_SYSTEM,
    ),
    test.case(
        "imperial",
        unit_system_name="imperial",
        expected_unit_system=US_CUSTOMARY_SYSTEM,
    ),
    test.case(
        "us_customary",
        unit_system_name="us_customary",
        expected_unit_system=US_CUSTOMARY_SYSTEM,
    ),
)
async def loading_configuration_unit_system(
    unit_system_name: str,
    expected_unit_system: UnitSystem,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test backward compatibility when loading core config."""
    await async_process_ha_core_config(
        hass,
        {
            "latitude": 60,
            "longitude": 50,
            "elevation": 25,
            "name": "Huis",
            "unit_system": unit_system_name,
            "time_zone": "America/New_York",
            "external_url": "https://www.example.com",
            "internal_url": "http://example.local",
        },
    )

    expect(hass.config.units).to_be(expected_unit_system)


@test
async def merge_customize(hass: HomeAssistant = Depends(hass)) -> None:
    """Test loading core config onto hass object."""
    core_config = {
        "latitude": 60,
        "longitude": 50,
        "elevation": 25,
        "name": "Huis",
        "unit_system": "imperial",
        "time_zone": "GMT",
        "customize": {"a.a": {"friendly_name": "A"}},
        "packages": {
            "pkg1": {"homeassistant": {"customize": {"b.b": {"friendly_name": "BB"}}}}
        },
    }
    await async_process_ha_core_config(hass, core_config)

    expect(hass.data[DATA_CUSTOMIZE].get("b.b")).to_equal({"friendly_name": "BB"})


@test
async def auth_provider_config(hass: HomeAssistant = Depends(hass)) -> None:
    """Test loading auth provider config onto hass object."""
    core_config = {
        "latitude": 60,
        "longitude": 50,
        "elevation": 25,
        "name": "Huis",
        "unit_system": "imperial",
        "time_zone": "GMT",
        CONF_AUTH_PROVIDERS: [
            {"type": "homeassistant"},
        ],
        CONF_AUTH_MFA_MODULES: [{"type": "totp"}, {"type": "totp", "id": "second"}],
    }
    if hasattr(hass, "auth"):
        del hass.auth
    await async_process_ha_core_config(hass, core_config)

    expect(len(hass.auth.auth_providers)).to_equal(1)
    expect(hass.auth.auth_providers[0].type).to_equal("homeassistant")
    expect(len(hass.auth.auth_mfa_modules)).to_equal(2)
    expect(hass.auth.auth_mfa_modules[0].id).to_equal("totp")
    expect(hass.auth.auth_mfa_modules[1].id).to_equal("second")


@test
async def auth_provider_config_default(hass: HomeAssistant = Depends(hass)) -> None:
    """Test loading default auth provider config."""
    core_config = {
        "latitude": 60,
        "longitude": 50,
        "elevation": 25,
        "name": "Huis",
        "unit_system": "imperial",
        "time_zone": "GMT",
    }
    if hasattr(hass, "auth"):
        del hass.auth
    await async_process_ha_core_config(hass, core_config)

    expect(len(hass.auth.auth_providers)).to_equal(1)
    expect(hass.auth.auth_providers[0].type).to_equal("homeassistant")
    expect(len(hass.auth.auth_mfa_modules)).to_equal(1)
    expect(hass.auth.auth_mfa_modules[0].id).to_equal("totp")


@test
async def disallowed_auth_provider_config(hass: HomeAssistant = Depends(hass)) -> None:
    """Test loading insecure example auth provider is disallowed."""
    core_config = {
        "latitude": 60,
        "longitude": 50,
        "elevation": 25,
        "name": "Huis",
        "unit_system": "imperial",
        "time_zone": "GMT",
        CONF_AUTH_PROVIDERS: [
            {
                "type": "insecure_example",
                "users": [
                    {
                        "username": "test-user",
                        "password": "test-pass",
                        "name": "Test Name",
                    }
                ],
            }
        ],
    }
    await _expect_raises_async(Invalid, async_process_ha_core_config(hass, core_config))


@test
async def disallowed_duplicated_auth_provider_config(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test loading insecure example auth provider is disallowed."""
    core_config = {
        "latitude": 60,
        "longitude": 50,
        "elevation": 25,
        "name": "Huis",
        "unit_system": "imperial",
        "time_zone": "GMT",
        CONF_AUTH_PROVIDERS: [{"type": "homeassistant"}, {"type": "homeassistant"}],
    }
    await _expect_raises_async(Invalid, async_process_ha_core_config(hass, core_config))


@test
async def disallowed_auth_mfa_module_config(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test loading insecure example auth mfa module is disallowed."""
    core_config = {
        "latitude": 60,
        "longitude": 50,
        "elevation": 25,
        "name": "Huis",
        "unit_system": "imperial",
        "time_zone": "GMT",
        CONF_AUTH_MFA_MODULES: [
            {
                "type": "insecure_example",
                "data": [{"user_id": "mock-user", "pin": "test-pin"}],
            }
        ],
    }
    await _expect_raises_async(Invalid, async_process_ha_core_config(hass, core_config))


@test
async def disallowed_duplicated_auth_mfa_module_config(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test loading insecure example auth mfa module is disallowed."""
    core_config = {
        "latitude": 60,
        "longitude": 50,
        "elevation": 25,
        "name": "Huis",
        "unit_system": "imperial",
        "time_zone": "GMT",
        CONF_AUTH_MFA_MODULES: [{"type": "totp"}, {"type": "totp"}],
    }
    await _expect_raises_async(Invalid, async_process_ha_core_config(hass, core_config))


@test
async def core_config_schema_historic_currency(
    hass: HomeAssistant = Depends(hass),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test core config schema."""
    await async_process_ha_core_config(hass, {"currency": "LTT"})

    issue = issue_registry.async_get_issue("homeassistant", "historic_currency")
    expect(issue).to_be_truthy()
    expect(issue.translation_placeholders).to_equal({"currency": "LTT"})


@test
async def core_store_historic_currency(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test core config store."""
    core_data = {
        "data": {
            "currency": "LTT",
        },
        "key": "core.config",
        "version": 1,
        "minor_version": 1,
    }
    hass_storage["core.config"] = dict(core_data)
    await async_process_ha_core_config(hass, {})

    issue_id = "historic_currency"
    issue = issue_registry.async_get_issue("homeassistant", issue_id)
    expect(issue).to_be_truthy()
    expect(issue.translation_placeholders).to_equal({"currency": "LTT"})

    await hass.config.async_update(currency="EUR")
    issue = issue_registry.async_get_issue("homeassistant", issue_id)
    expect(issue).to_be_falsy()


@test
async def core_config_schema_no_country(
    hass: HomeAssistant = Depends(hass),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test core config schema."""
    await async_process_ha_core_config(hass, {})

    issue = issue_registry.async_get_issue("homeassistant", "country_not_configured")
    expect(issue).to_be_truthy()


@test
async def core_store_no_country(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test core config store."""
    core_data = {
        "data": {},
        "key": "core.config",
        "version": 1,
        "minor_version": 1,
    }
    hass_storage["core.config"] = dict(core_data)
    await async_process_ha_core_config(hass, {})

    issue_id = "country_not_configured"
    issue = issue_registry.async_get_issue("homeassistant", issue_id)
    expect(issue).to_be_truthy()

    await hass.config.async_update(country="SE")
    issue = issue_registry.async_get_issue("homeassistant", issue_id)
    expect(issue).to_be_falsy()


@test
async def configuration_legacy_template_is_removed(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test loading core config onto hass object."""
    await async_process_ha_core_config(
        hass,
        {
            "latitude": 60,
            "longitude": 50,
            "elevation": 25,
            "name": "Huis",
            "unit_system": "imperial",
            "time_zone": "America/New_York",
            "allowlist_external_dirs": "/etc",
            "external_url": "https://www.example.com",
            "internal_url": "http://example.local",
            "media_dirs": {"mymedia": "/usr"},
            "legacy_templates": True,
            "debug": True,
            "currency": "EUR",
            "country": "SE",
            "language": "sv",
            "radius": 150,
        },
    )

    expect(hass.config.legacy_templates).to_be_falsy()


@test
async def config_defaults() -> None:
    """Test config defaults."""
    hass = Mock()
    hass.data = {}
    config = Config(hass, "/test/ha-config")
    expect(config.hass).to_be(hass)
    expect(config.latitude).to_equal(0)
    expect(config.longitude).to_equal(0)
    expect(config.elevation).to_equal(0)
    expect(config.location_name).to_equal("Home")
    expect(config.time_zone).to_equal("UTC")
    expect(config.internal_url).to_be(None)
    expect(config.external_url).to_be(None)
    expect(config.config_source).to_be(ConfigSource.DEFAULT)
    expect(config.skip_pip).to_be(False)
    expect(config.skip_pip_packages).to_equal([])
    expect(config.components).to_equal(set())
    expect(config.api).to_be(None)
    expect(config.config_dir).to_equal("/test/ha-config")
    expect(config.allowlist_external_dirs).to_equal(set())
    expect(config.allowlist_external_urls).to_equal(set())
    expect(config.media_dirs).to_equal({})
    expect(config.recovery_mode).to_be(False)
    expect(config.legacy_templates).to_be(False)
    expect(config.currency).to_equal("EUR")
    expect(config.country).to_be(None)
    expect(config.language).to_equal("en")
    expect(config.radius).to_equal(100)


@test
async def config_path_with_file() -> None:
    """Test get_config_path method."""
    hass = Mock()
    hass.data = {}
    config = Config(hass, "/test/ha-config")
    expect(config.path("test.conf")).to_equal("/test/ha-config/test.conf")


@test
async def config_path_with_dir_and_file() -> None:
    """Test get_config_path method."""
    hass = Mock()
    hass.data = {}
    config = Config(hass, "/test/ha-config")
    expect(config.path("dir", "test.conf")).to_equal("/test/ha-config/dir/test.conf")


@test
async def config_cache_path_with_file() -> None:
    """Test cache_path method with file."""
    hass = Mock()
    hass.data = {}
    config = Config(hass, "/test/ha-config")
    expect(config.cache_path("test.cache")).to_equal(
        "/test/ha-config/.cache/test.cache"
    )


@test
async def config_cache_path_with_dir_and_file() -> None:
    """Test cache_path method with dir and file."""
    hass = Mock()
    hass.data = {}
    config = Config(hass, "/test/ha-config")
    expect(config.cache_path("dir", "test.cache")).to_equal(
        "/test/ha-config/.cache/dir/test.cache"
    )


@test
async def config_as_dict() -> None:
    """Test as dict."""
    hass = Mock()
    hass.data = {}
    config = Config(hass, "/test/ha-config")
    type(config.hass.state).value = PropertyMock(return_value="RUNNING")
    expected = {
        "latitude": 0,
        "longitude": 0,
        "elevation": 0,
        CONF_UNIT_SYSTEM: METRIC_SYSTEM.as_dict(),
        "location_name": "Home",
        "time_zone": "UTC",
        "components": [],
        "config_dir": "/test/ha-config",
        "whitelist_external_dirs": [],
        "allowlist_external_dirs": [],
        "allowlist_external_urls": [],
        "version": __version__,
        "config_source": ConfigSource.DEFAULT,
        "recovery_mode": False,
        "state": "RUNNING",
        "external_url": None,
        "internal_url": None,
        "currency": "EUR",
        "country": None,
        "language": "en",
        "safe_mode": False,
        "debug": False,
        "radius": 100,
    }

    expect(expected).to_equal(config.as_dict())


@test
async def config_is_allowed_path() -> None:
    """Test is_allowed_path method."""
    hass = Mock()
    hass.data = {}
    config = Config(hass, "/test/ha-config")
    with TemporaryDirectory() as tmp_dir:
        # The created dir is in /tmp. This is a symlink on OS X
        # causing this test to fail unless we resolve path first.
        config.allowlist_external_dirs = {os.path.realpath(tmp_dir)}

        test_file = os.path.join(tmp_dir, "test.jpg")
        await asyncio.get_running_loop().run_in_executor(
            None, Path(test_file).write_text, "test"
        )

        valid = [test_file, tmp_dir, os.path.join(tmp_dir, "notfound321")]
        for path in valid:
            expect(config.is_allowed_path(path)).to_be_truthy()

        config.allowlist_external_dirs = {"/home", "/var"}

        invalid = [
            "/hass/config/secure",
            "/etc/passwd",
            "/root/secure_file",
            "/var/../etc/passwd",
            test_file,
        ]
        for path in invalid:
            expect(config.is_allowed_path(path)).to_be_falsy()

        _expect_raises_sync(AssertionError, config.is_allowed_path, None)


@test
async def config_is_allowed_external_url() -> None:
    """Test is_allowed_external_url method."""
    hass = Mock()
    hass.data = {}
    config = Config(hass, "/test/ha-config")
    config.allowlist_external_urls = [
        "http://x.com/",
        "https://y.com/bla/",
        "https://z.com/images/1.jpg/",
    ]

    valid = [
        "http://x.com/1.jpg",
        "http://x.com",
        "https://y.com/bla/",
        "https://y.com/bla/2.png",
        "https://z.com/images/1.jpg",
    ]
    for url in valid:
        expect(config.is_allowed_external_url(url)).to_be_truthy()

    invalid = [
        "https://a.co",
        "https://y.com/bla_wrong",
        "https://y.com/bla/../image.jpg",
        "https://z.com/images",
    ]
    for url in invalid:
        expect(config.is_allowed_external_url(url)).to_be_falsy()


@test
async def event_on_update(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that event is fired on update."""
    events = async_capture_events(hass, EVENT_CORE_CONFIG_UPDATE)

    expect(hass.config.latitude).not_.to_equal(12)

    await hass.config.async_update(latitude=12)
    await hass.async_block_till_done()

    expect(hass.config.latitude).to_equal(12)
    expect(len(events)).to_equal(1)
    expect(events[0].data).to_equal({"latitude": 12})


@test
async def bad_timezone_raises_value_error(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test bad timezone raises ValueError."""
    await _expect_raises_async(
        ValueError, hass.config.async_update(time_zone="not_a_timezone")
    )


@test
async def additional_data_in_core_config(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test that we can handle additional data in core configuration."""
    config = Config(hass, "/test/ha-config")
    config.async_initialize()
    hass_storage[CORE_STORAGE_KEY] = {
        "version": 1,
        "data": {"location_name": "Test Name", "additional_valid_key": "value"},
    }
    await config.async_load()
    expect(config.location_name).to_equal("Test Name")


@test
async def incorrect_internal_external_url(
    hass: HomeAssistant = Depends(hass),
    hass_storage: dict[str, Any] = Depends(hass_storage),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test that we warn when detecting invalid internal/external url."""
    config = Config(hass, "/test/ha-config")
    config.async_initialize()

    hass_storage[CORE_STORAGE_KEY] = {
        "version": 1,
        "data": {
            "internal_url": None,
            "external_url": None,
        },
    }
    await config.async_load()
    expect("Invalid external_url set" in caplog.text).to_be_falsy()
    expect("Invalid internal_url set" in caplog.text).to_be_falsy()

    config = Config(hass, "/test/ha-config")
    config.async_initialize()

    hass_storage[CORE_STORAGE_KEY] = {
        "version": 1,
        "data": {
            "internal_url": "https://community.home-assistant.io/profile",
            "external_url": "https://www.home-assistant.io/blue",
        },
    }
    await config.async_load()
    expect("Invalid external_url set" in caplog.text).to_be_truthy()
    expect("Invalid internal_url set" in caplog.text).to_be_truthy()


@test
async def top_level_components(hass: HomeAssistant = Depends(hass)) -> None:
    """Test top level components are updated when components change."""
    hass.config.components.add("homeassistant")
    expect(hass.config.components).to_equal({"homeassistant"})
    expect(hass.config.top_level_components).to_equal({"homeassistant"})
    hass.config.components.add("homeassistant.scene")
    expect(hass.config.components).to_equal({"homeassistant", "homeassistant.scene"})
    expect(hass.config.top_level_components).to_equal({"homeassistant"})
    hass.config.components.remove("homeassistant")
    expect(hass.config.components).to_equal({"homeassistant.scene"})
    expect(hass.config.top_level_components).to_equal(set())
    _expect_raises_sync(
        ValueError, hass.config.components.remove, "homeassistant.scene"
    )
    _expect_raises_sync(
        NotImplementedError, hass.config.components.discard, "homeassistant"
    )


@test
async def debug_mode_defaults_to_off(hass: HomeAssistant = Depends(hass)) -> None:
    """Test debug mode defaults to off."""
    expect(hass.config.debug).to_be_falsy()


@test
async def core_config_schema_imperial_unit(
    hass: HomeAssistant = Depends(hass),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test core config schema."""
    await async_process_ha_core_config(
        hass,
        {
            "latitude": 60,
            "longitude": 50,
            "elevation": 25,
            "name": "Home",
            "unit_system": "imperial",
            "time_zone": "America/New_York",
            "currency": "USD",
            "country": "US",
            "language": "en",
            "radius": 150,
        },
    )

    issue = issue_registry.async_get_issue("homeassistant", "imperial_unit_system")
    expect(issue).to_be_truthy()
