"""Test config flow."""

from tryke import test


@test.skip("requires mqtt_mock broker fixture")
async def mqtt_abort_if_existing_entry() -> None:
    """Check MQTT flow aborts when an entry already exist."""


@test.skip("requires mqtt_mock broker fixture")
async def mqtt_abort_invalid_topic() -> None:
    """Check MQTT flow aborts if discovery topic is invalid."""


@test.skip("requires mqtt_mock broker fixture")
async def mqtt_setup() -> None:
    """Test we can finish a config flow through MQTT with custom prefix."""


@test.skip("requires mqtt_mock broker fixture")
async def user_setup() -> None:
    """Test we can finish a config flow."""


@test.skip("requires mqtt_mock broker fixture")
async def user_setup_advanced() -> None:
    """Test we can finish a config flow with advanced options."""


@test.skip("requires mqtt_mock broker fixture")
async def user_setup_advanced_strip_wildcard() -> None:
    """Test we can finish a config flow stripping wildcard."""


@test.skip("requires mqtt_mock broker fixture")
async def user_setup_invalid_topic_prefix() -> None:
    """Test abort on invalid discovery topic."""


@test.skip("requires mqtt_mock broker fixture")
async def user_single_instance() -> None:
    """Test we only allow a single config flow."""
