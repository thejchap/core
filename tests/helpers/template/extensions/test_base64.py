"""Test base64 encoding and decoding functions for Home Assistant templates."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass
from tests.helpers.template.helpers import render


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "homeassistant",
        value_template='{{ "homeassistant" | base64_encode }}',
        expected="aG9tZWFzc2lzdGFudA==",
    ),
    test.case(
        "pack_int",
        value_template="{{ int('0F010003', base=16) | pack('>I') | base64_encode }}",
        expected="DwEAAw==",
    ),
    test.case(
        "from_hex",
        value_template="{{ 'AA01000200150020' | from_hex | base64_encode }}",
        expected="qgEAAgAVACA=",
    ),
)
async def base64_encode(
    value_template: str,
    expected: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the base64_encode filter."""
    expect(render(hass, value_template)).to_equal(expected)


@test
async def base64_decode(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the base64_decode filter."""
    expect(render(hass, '{{ "aG9tZWFzc2lzdGFudA==" | base64_decode }}')).to_equal(
        "homeassistant"
    )
    expect(
        render(hass, '{{ "aG9tZWFzc2lzdGFudA==" | base64_decode(None) }}')
    ).to_equal(b"homeassistant")
    expect(
        render(hass, '{{ "aG9tZWFzc2lzdGFudA==" | base64_decode("ascii") }}')
    ).to_equal("homeassistant")
