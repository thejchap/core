"""Tryke skip-stubs for template/test_weather.py."""

from tryke import test


@test.skip("requires template integration setup — port deferred")
async def legacy_template_creates_warning() -> None:
    """Stub for test_legacy_template_creates_warning."""

@test.skip("requires template integration setup — port deferred")
async def template_state_exception() -> None:
    """Stub for test_template_state_exception."""

@test.skip("requires template integration setup — port deferred")
async def template_state_text() -> None:
    """Stub for test_template_state_text."""

@test.skip("requires template integration setup — port deferred")
async def forecasts() -> None:
    """Stub for test_forecasts."""

@test.skip("requires template integration setup — port deferred")
async def forecasts_invalid() -> None:
    """Stub for test_forecasts_invalid."""

@test.skip("requires template integration setup — port deferred")
async def forecast_format_error() -> None:
    """Stub for test_forecast_format_error."""

@test.skip("requires template integration setup — port deferred")
async def trigger_entity_restore_state() -> None:
    """Stub for test_trigger_entity_restore_state."""

@test.skip("requires template integration setup — port deferred")
async def trigger_action() -> None:
    """Stub for test_trigger_action."""

@test.skip("requires template integration setup — port deferred")
async def restore_weather_save_state() -> None:
    """Stub for test_restore_weather_save_state."""

@test.skip("requires template integration setup — port deferred")
async def trigger_entity_restore_state_fail() -> None:
    """Stub for test_trigger_entity_restore_state_fail."""

@test.skip("requires template integration setup — port deferred")
async def templated_optional_config() -> None:
    """Stub for test_templated_optional_config."""

@test.skip("requires template integration setup — port deferred")
async def setup_config_entry() -> None:
    """Stub for test_setup_config_entry."""

@test.skip("requires template integration setup — port deferred")
async def flow_preview() -> None:
    """Stub for test_flow_preview."""

