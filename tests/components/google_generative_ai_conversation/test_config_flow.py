"""Tryke skip-stubs for google_generative_ai_conversation config flow tests.

The integration depends on `conversation` which depends on
`homeassistant.exposed_entities`; that dependency is not available under
the tryke shim's minimal hass setup. Defer the full config flow port.
"""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the google_generative_ai_conversation DOMAIN imports cleanly."""
    from homeassistant.components.google_generative_ai_conversation.const import (  # noqa: PLC0415
        DOMAIN,
    )
    expect(DOMAIN).to_equal("google_generative_ai_conversation")


@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def form() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def duplicate_entry() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def reauth_flow() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def reauth_flow_invalid_api_key() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def options() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def creating_conversation_subentry() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def creating_conversation_subentry_not_loaded() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def creating_tts_subentry() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def creating_tts_subentry_not_loaded() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def creating_ai_task_subentry() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def creating_ai_task_subentry_not_loaded() -> None:
    """Stub."""

@test.skip("requires conversation+exposed_entities setup chain (not in tryke shim)")
async def options_models() -> None:
    """Stub."""
