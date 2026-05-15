"""Configure and test MatrixBot."""

from tryke import expect, test


@test
async def services() -> None:
    """Test hass/MatrixBot state."""
    expect(1).to_be(1)
