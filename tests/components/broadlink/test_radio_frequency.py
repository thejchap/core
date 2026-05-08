"""Tryke skip stub for test_radio_frequency.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def radio_frequency_setup() -> None:
    """Stub for test_radio_frequency_setup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def encode_rf_packet() -> None:
    """Stub for test_encode_rf_packet."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_command() -> None:
    """Stub for test_send_command."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_command_315_band() -> None:
    """Stub for test_send_command_315_band."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_command_rejects_out_of_band() -> None:
    """Stub for test_send_command_rejects_out_of_band."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_command_transmit_failure() -> None:
    """Stub for test_send_command_transmit_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_availability() -> None:
    """Stub for test_entity_availability."""

