"""The tests for the Netatmo api."""

from pyatmo.const import ALL_SCOPES
from tryke import expect, test

from homeassistant.components import cloud
from homeassistant.components.netatmo import api
from homeassistant.components.netatmo.const import API_SCOPES_EXCLUDED_FROM_CLOUD


@test
async def get_api_scopes_cloud() -> None:
    """Test method to get API scopes when using cloud auth implementation."""
    result = api.get_api_scopes(cloud.DOMAIN)

    for scope in API_SCOPES_EXCLUDED_FROM_CLOUD:
        expect(scope in result).to_be(False)


@test
async def get_api_scopes_other() -> None:
    """Test method to get API scopes when using a non-cloud implementation."""
    result = api.get_api_scopes("netatmo_239846i2f0j2")

    expect(sorted(ALL_SCOPES)).to_equal(result)
