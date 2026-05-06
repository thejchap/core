"""Test the sonos config flow."""

from tryke import test


@test.skip("requires sonos conftest fixtures (zeroconf_payload, soco)")
async def user_form() -> None:
    """Test we get the user initiated form."""


@test.skip("requires sonos conftest fixtures (zeroconf_payload, soco)")
async def user_form_already_created() -> None:
    """Ensure we abort a flow if the entry is already created from config."""


@test.skip("requires sonos conftest fixtures (zeroconf_payload, soco)")
async def zeroconf_form() -> None:
    """Test we get the zeroconf form."""


@test.skip("requires sonos conftest fixtures (zeroconf_payload, soco)")
async def zeroconf_form_not_ipv4() -> None:
    """Test we abort zeroconf form when not IPv4."""


@test.skip("requires sonos conftest fixtures (zeroconf_payload, soco)")
async def ssdp_discovery() -> None:
    """Test SSDP discovery."""


@test.skip("requires sonos conftest fixtures (zeroconf_payload, soco)")
async def zeroconf_sonos_v1() -> None:
    """Test zeroconf for Sonos V1."""


@test.skip("requires sonos conftest fixtures (zeroconf_payload, soco)")
async def zeroconf_form_not_sonos() -> None:
    """Test zeroconf abort when not sonos."""
