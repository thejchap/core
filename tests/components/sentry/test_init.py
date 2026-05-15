"""Tests for Sentry integration."""

import logging
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.sentry import process_before_send
from homeassistant.components.sentry.const import (
    CONF_DSN,
    CONF_ENVIRONMENT,
    CONF_EVENT_CUSTOM_COMPONENTS,
    CONF_EVENT_HANDLED,
    CONF_EVENT_THIRD_PARTY_PACKAGES,
    CONF_TRACING,
    CONF_TRACING_SAMPLE_RATE,
    DOMAIN,
)
from homeassistant.const import __version__ as current_version
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test integration setup from entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DSN: "http://public@example.com/1", CONF_ENVIRONMENT: "production"},
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.sentry.AioHttpIntegration"
        ) as sentry_aiohttp_mock,
        patch(
            "homeassistant.components.sentry.SqlalchemyIntegration"
        ) as sentry_sqlalchemy_mock,
        patch(
            "homeassistant.components.sentry.LoggingIntegration"
        ) as sentry_logging_mock,
        patch("homeassistant.components.sentry.sentry_sdk") as sentry_mock,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    # Test CONF_ENVIRONMENT is migrated to entry options
    expect(CONF_ENVIRONMENT not in entry.data).to_be(True)
    expect(CONF_ENVIRONMENT in entry.options).to_be(True)
    expect(entry.options[CONF_ENVIRONMENT]).to_equal("production")

    expect(sentry_logging_mock.call_count).to_equal(1)
    sentry_logging_mock.assert_called_once_with(
        level=logging.WARNING, event_level=logging.ERROR
    )

    expect(sentry_aiohttp_mock.call_count).to_equal(1)
    expect(sentry_sqlalchemy_mock.call_count).to_equal(1)
    expect(sentry_mock.init.call_count).to_equal(1)

    call_args = sentry_mock.init.call_args[1]
    expect(set(call_args)).to_equal(
        {
            "dsn",
            "environment",
            "integrations",
            "release",
            "before_send",
        }
    )
    expect(call_args["dsn"]).to_equal("http://public@example.com/1")
    expect(call_args["environment"]).to_equal("production")
    expect(call_args["integrations"]).to_equal(
        [
            sentry_logging_mock.return_value,
            sentry_aiohttp_mock.return_value,
            sentry_sqlalchemy_mock.return_value,
        ]
    )
    expect(call_args["release"]).to_equal(current_version)
    expect(bool(call_args["before_send"])).to_be(True)


@test
async def setup_entry_with_tracing(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test integration setup from entry with tracing enabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DSN: "http://public@example.com/1"},
        options={CONF_TRACING: True, CONF_TRACING_SAMPLE_RATE: 0.5},
    )
    entry.add_to_hass(hass)

    with (
        patch("homeassistant.components.sentry.AioHttpIntegration"),
        patch("homeassistant.components.sentry.SqlalchemyIntegration"),
        patch("homeassistant.components.sentry.LoggingIntegration"),
        patch("homeassistant.components.sentry.sentry_sdk") as sentry_mock,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    call_args = sentry_mock.init.call_args[1]
    expect(set(call_args)).to_equal(
        {
            "dsn",
            "environment",
            "integrations",
            "release",
            "before_send",
            "traces_sample_rate",
        }
    )
    expect(call_args["traces_sample_rate"]).to_equal(0.5)


@test
async def process_before_send_basic(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test regular use of the Sentry process before sending function."""
    hass.config.components.add("puppies")
    hass.config.components.add("a_integration")

    # These should not show up in the result.
    hass.config.components.add("puppies.light")
    hass.config.components.add("auth")

    result = process_before_send(
        hass,
        options={},
        channel="test",
        huuid="12345",
        system_info={"installation_type": "pytest"},
        custom_components=["ironing_robot", "fridge_opener"],
        event={},
        hint={},
    )

    expect(bool(result)).to_be(True)
    expect(bool(result["tags"])).to_be(True)
    expect(bool(result["contexts"])).to_be(True)

    ha_context = result["contexts"]["Home Assistant"]
    expect(ha_context["channel"]).to_equal("test")
    expect(ha_context["custom_components"]).to_equal("fridge_opener\nironing_robot")
    expect(ha_context["integrations"]).to_equal("a_integration\npuppies")

    tags = result["tags"]
    expect(tags["channel"]).to_equal("test")
    expect(tags["uuid"]).to_equal("12345")
    expect(tags["installation_type"]).to_equal("pytest")

    user = result["user"]
    expect(user["id"]).to_equal("12345")


@test
async def event_with_platform_context(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test extraction of platform context information during Sentry events."""

    current_platform_mock = Mock()
    current_platform_mock.get().platform_name = "hue"
    current_platform_mock.get().domain = "light"

    with patch(
        "homeassistant.components.sentry.entity_platform.current_platform",
        new=current_platform_mock,
    ):
        result = process_before_send(
            hass,
            options={},
            channel="test",
            huuid="12345",
            system_info={"installation_type": "pytest"},
            custom_components=["ironing_robot"],
            event={},
            hint={},
        )

    expect(bool(result)).to_be(True)
    expect(result["tags"]["integration"]).to_equal("hue")
    expect(result["tags"]["platform"]).to_equal("light")
    expect(result["tags"]["custom_component"]).to_equal("no")

    current_platform_mock.get().platform_name = "ironing_robot"
    current_platform_mock.get().domain = "switch"

    with patch(
        "homeassistant.components.sentry.entity_platform.current_platform",
        new=current_platform_mock,
    ):
        result = process_before_send(
            hass,
            options={CONF_EVENT_CUSTOM_COMPONENTS: True},
            channel="test",
            huuid="12345",
            system_info={"installation_type": "pytest"},
            custom_components=["ironing_robot"],
            event={},
            hint={},
        )

    expect(bool(result)).to_be(True)
    expect(result["tags"]["integration"]).to_equal("ironing_robot")
    expect(result["tags"]["platform"]).to_equal("switch")
    expect(result["tags"]["custom_component"]).to_equal("yes")


@test.cases(
    test.case("adguard", logger="adguard", tags={"package": "adguard"}),
    test.case(
        "hue_coordinator",
        logger="homeassistant.components.hue.coordinator",
        tags={"integration": "hue", "custom_component": "no"},
    ),
    test.case(
        "hue_light",
        logger="homeassistant.components.hue.light",
        tags={"integration": "hue", "platform": "light", "custom_component": "no"},
    ),
    test.case(
        "ironing_robot_switch",
        logger="homeassistant.components.ironing_robot.switch",
        tags={
            "integration": "ironing_robot",
            "platform": "switch",
            "custom_component": "yes",
        },
    ),
    test.case(
        "ironing_robot",
        logger="homeassistant.components.ironing_robot",
        tags={"integration": "ironing_robot", "custom_component": "yes"},
    ),
    test.case(
        "helpers_network",
        logger="homeassistant.helpers.network",
        tags={"helpers": "network"},
    ),
    test.case("tuyapi", logger="tuyapi.test", tags={"package": "tuyapi"}),
)
async def logger_event_extraction(
    *,
    logger: str,
    tags: dict,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test extraction of information from Sentry logger events."""

    result = process_before_send(
        hass,
        options={
            CONF_EVENT_CUSTOM_COMPONENTS: True,
            CONF_EVENT_THIRD_PARTY_PACKAGES: True,
        },
        channel="test",
        huuid="12345",
        system_info={"installation_type": "pytest"},
        custom_components=["ironing_robot"],
        event={"logger": logger},
        hint={},
    )

    expect(bool(result)).to_be(True)
    expect(result["tags"]).to_equal(
        {
            "channel": "test",
            "uuid": "12345",
            "installation_type": "pytest",
            **tags,
        }
    )


@test.cases(
    test.case(
        "adguard_third_party_on",
        logger="adguard",
        options={CONF_EVENT_THIRD_PARTY_PACKAGES: True},
        event=True,
    ),
    test.case(
        "adguard_third_party_off",
        logger="adguard",
        options={CONF_EVENT_THIRD_PARTY_PACKAGES: False},
        event=False,
    ),
    test.case(
        "custom_components_on",
        logger="homeassistant.components.ironing_robot.switch",
        options={CONF_EVENT_CUSTOM_COMPONENTS: True},
        event=True,
    ),
    test.case(
        "custom_components_off",
        logger="homeassistant.components.ironing_robot.switch",
        options={CONF_EVENT_CUSTOM_COMPONENTS: False},
        event=False,
    ),
)
async def filter_log_events(
    *,
    logger: str,
    options: dict,
    event: bool,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test filtering of events based on configuration options."""
    result = process_before_send(
        hass,
        options=options,
        channel="test",
        huuid="12345",
        system_info={"installation_type": "pytest"},
        custom_components=["ironing_robot"],
        event={"logger": logger},
        hint={},
    )

    expect(result is not None).to_be(event)


@test.cases(
    test.case("yes_on", handled="yes", options={CONF_EVENT_HANDLED: True}, event=True),
    test.case(
        "yes_off", handled="yes", options={CONF_EVENT_HANDLED: False}, event=False
    ),
    test.case(
        "no_off", handled="no", options={CONF_EVENT_HANDLED: False}, event=True
    ),
    test.case("no_on", handled="no", options={CONF_EVENT_HANDLED: True}, event=True),
)
async def filter_handled_events(
    *,
    handled: str,
    options: dict,
    event: bool,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Tests filtering of handled events based on configuration options."""
    result = process_before_send(
        hass,
        options=options,
        channel="test",
        huuid="12345",
        system_info={"installation_type": "pytest"},
        custom_components=[],
        event={"tags": {"handled": handled}},
        hint={},
    )

    expect(result is not None).to_be(event)
