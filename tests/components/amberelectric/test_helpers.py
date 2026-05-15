"""Test formatters."""

from amberelectric.models.price_descriptor import PriceDescriptor
from tryke import expect, test

from homeassistant.components.amberelectric.helpers import normalize_descriptor


@test
def normalize_descriptor_returns_expected_values() -> None:
    """Test normalizing descriptors works correctly."""
    expect(normalize_descriptor(None)).to_be_none()
    expect(normalize_descriptor(PriceDescriptor.NEGATIVE)).to_equal("negative")
    expect(normalize_descriptor(PriceDescriptor.EXTREMELYLOW)).to_equal("extremely_low")
    expect(normalize_descriptor(PriceDescriptor.VERYLOW)).to_equal("very_low")
    expect(normalize_descriptor(PriceDescriptor.LOW)).to_equal("low")
    expect(normalize_descriptor(PriceDescriptor.NEUTRAL)).to_equal("neutral")
    expect(normalize_descriptor(PriceDescriptor.HIGH)).to_equal("high")
    expect(normalize_descriptor(PriceDescriptor.SPIKE)).to_equal("spike")
