"""Test the sonos helpers."""

from tryke import expect, fixture, test

from homeassistant.components.sonos.helpers import hostname_to_uid


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def uid_to_hostname() -> None:
    """Test we can convert a hostname to a uid."""
    expect(hostname_to_uid("Sonos-347E5C0CF1E3.local.")).to_equal(
        "RINCON_347E5C0CF1E301400"
    )
    expect(hostname_to_uid("sonos5CAAFDE47AC8.local.")).to_equal(
        "RINCON_5CAAFDE47AC801400"
    )

    expect(lambda: hostname_to_uid("notsonos5CAAFDE47AC8.local.")).to_raise(ValueError)
