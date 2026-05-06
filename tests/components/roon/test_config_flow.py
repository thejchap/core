"""Test the roon config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.roon.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


class RoonApiMock:
    """Class to mock the Roon API for testing."""

    @property
    def token(self):
        """Return a good authentication key."""
        return "good_token"

    @property
    def core_id(self):
        """Return the roon host."""
        return "core_id"

    @property
    def core_name(self):
        """Return the roon core name."""
        return "Roon Core"

    def stop(self):
        """Stop socket."""
        return


class RoonApiMockNoToken(RoonApiMock):
    """Class to mock the Roon API for testing, with failed authorisation."""

    @property
    def token(self):
        """Return a bad authentication key."""
        return None


class RoonApiMockException(RoonApiMock):
    """Class to mock the Roon API for testing, throws an unexpected exception."""

    @property
    def token(self):
        """Throw exception."""
        raise Exception  # noqa: TRY002


class RoonDiscoveryMock:
    """Class to mock Roon Discovery for testing."""

    def all(self):
        """Return a discovered roon server."""
        return ["2.2.2.2"]

    def stop(self):
        """Stop discovery running."""
        return


class RoonDiscoveryFailedMock(RoonDiscoveryMock):
    """Class to mock Roon Discovery for testing, with no servers discovered."""

    def all(self):
        """Return no discovered roon servers."""
        return []


@fixture
def _trigger_executor() -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def successful_discovery_and_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test when discovery and auth both work ok."""
    with (
        patch(
            "homeassistant.components.roon.config_flow.RoonApi",
            return_value=RoonApiMock(),
        ),
        patch(
            "homeassistant.components.roon.config_flow.RoonDiscovery",
            return_value=RoonDiscoveryMock(),
        ),
        patch(
            "homeassistant.components.roon.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("link")
        expect(result["errors"]).to_equal({})

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    expect(result2["title"]).to_equal("Roon Labs Music Player")
    expect(result2["data"]).to_equal(
        {
            "host": None,
            "port": None,
            "api_key": "good_token",
            "roon_server_id": "core_id",
            "roon_server_name": "Roon Core",
        }
    )


@test
async def unsuccessful_discovery_user_form_and_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unsuccessful discover, user adding the host via the form and then successful auth."""
    with (
        patch(
            "homeassistant.components.roon.config_flow.RoonApi",
            return_value=RoonApiMock(),
        ),
        patch(
            "homeassistant.components.roon.config_flow.RoonDiscovery",
            return_value=RoonDiscoveryFailedMock(),
        ),
        patch(
            "homeassistant.components.roon.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("fallback")
        expect(result["errors"]).to_equal({})

        await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.1.1.1", "port": 9331}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    expect(result2["title"]).to_equal("Roon Labs Music Player")
    expect(result2["data"]).to_equal(
        {
            "host": "1.1.1.1",
            "api_key": "good_token",
            "port": 9331,
            "roon_server_id": "core_id",
            "roon_server_name": "Roon Core",
        }
    )


@test
async def duplicate_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user adding the host via the form for host that is already configured."""
    CONFIG = {"host": "1.1.1.1"}

    MockConfigEntry(domain=DOMAIN, unique_id="0123456789", data=CONFIG).add_to_hass(
        hass
    )

    with (
        patch(
            "homeassistant.components.roon.config_flow.RoonApi",
            return_value=RoonApiMock(),
        ),
        patch(
            "homeassistant.components.roon.config_flow.RoonDiscovery",
            return_value=RoonDiscoveryFailedMock(),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("fallback")
        expect(result["errors"]).to_equal({})

        await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.1.1.1", "port": 9331}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("already_configured")


@test
async def successful_discovery_no_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful discover, but failed auth."""
    with (
        patch(
            "homeassistant.components.roon.config_flow.RoonApi",
            return_value=RoonApiMockNoToken(),
        ),
        patch(
            "homeassistant.components.roon.config_flow.RoonDiscovery",
            return_value=RoonDiscoveryMock(),
        ),
        patch(
            "homeassistant.components.roon.config_flow.TIMEOUT",
            0,
        ),
        patch(
            "homeassistant.components.roon.config_flow.AUTHENTICATE_TIMEOUT",
            0.01,
        ),
        patch(
            "homeassistant.components.roon.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("link")
        expect(result["errors"]).to_equal({})

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def unexpected_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful discover, and unexpected exception during auth."""
    with (
        patch(
            "homeassistant.components.roon.config_flow.RoonApi",
            return_value=RoonApiMockException(),
        ),
        patch(
            "homeassistant.components.roon.config_flow.RoonDiscovery",
            return_value=RoonDiscoveryMock(),
        ),
        patch(
            "homeassistant.components.roon.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("link")
        expect(result["errors"]).to_equal({})

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    expect(result2["errors"]).to_equal({"base": "unknown"})
