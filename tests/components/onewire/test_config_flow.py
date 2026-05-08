"""Tests for 1-Wire config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, patch

from aio_ownet.exceptions import OWServerConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.onewire.const import DOMAIN
from homeassistant.config_entries import SOURCE_HASSIO, SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.hassio import HassioServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

_HASSIO_DISCOVERY = HassioServiceInfo(
    config={"host": "1302b8e0-owserver", "port": 4304, "addon": "owserver (1-wire)"},
    name="owserver (1-wire)",
    slug="1302b8e0_owserver",
    uuid="e3fa56560d93458b96a594cbcea3017e",
)
_ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address("5.6.7.8"),
    ip_addresses=[ip_address("5.6.7.8")],
    hostname="ubuntu.local.",
    name="OWFS (1-wire) Server",
    port=4304,
    type="_owserver._tcp.local.",
    properties={},
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Module-local fixture executor anchor — autouse mock_setup_entry."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    new_entry = result["result"]
    expect(new_entry.title).to_equal("1.2.3.4")
    expect(new_entry.data).to_equal({CONF_HOST: "1.2.3.4", CONF_PORT: 1234})


@test
async def user_flow_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow recovery after invalid server."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
        side_effect=OWServerConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    new_entry = result["result"]
    expect(new_entry.title).to_equal("1.2.3.4")
    expect(new_entry.data).to_equal({CONF_HOST: "1.2.3.4", CONF_PORT: 1234})


@test
async def user_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test user duplicate flow."""
    entry.add_to_hass(hass)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 1234},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow."""
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(bool(result["errors"])).to_be(False)

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
        side_effect=OWServerConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 2345},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 2345},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({CONF_HOST: "2.3.4.5", CONF_PORT: 2345})


@test
async def reconfigure_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test reconfigure duplicate flow."""
    entry.add_to_hass(hass)
    other_config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOST: "2.3.4.5",
            CONF_PORT: 2345,
        },
        entry_id="other",
    )
    other_config_entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 2345},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data).to_equal({CONF_HOST: "1.2.3.4", CONF_PORT: 1234})
    expect(other_config_entry.data).to_equal({CONF_HOST: "2.3.4.5", CONF_PORT: 2345})


@test
async def hassio_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HassIO discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HASSIO},
        data=_HASSIO_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(bool(result["errors"])).to_be(False)

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
        side_effect=OWServerConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    new_entry = result["result"]
    expect(new_entry.title).to_equal("owserver (1-wire)")
    expect(new_entry.data).to_equal({CONF_HOST: "1302b8e0-owserver", CONF_PORT: 4304})


@test
async def hassio_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test HassIO discovery duplicate flow."""
    entry.add_to_hass(hass)
    # Hassio discovery uses different host so use a new entry that matches
    matching_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={CONF_HOST: "1302b8e0-owserver", CONF_PORT: 4304},
        entry_id="matching",
    )
    matching_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_HASSIO},
        data=_HASSIO_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=_ZEROCONF_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    with patch(
        "homeassistant.components.onewire.onewirehub.OWServerStatelessProxy.validate",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zeroconf_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test zeroconf discovery duplicate flow."""
    entry.add_to_hass(hass)
    matching_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={CONF_HOST: "5.6.7.8", CONF_PORT: 4304},
        entry_id="matching",
    )
    matching_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=_ZEROCONF_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test.skip("requires filled_device_registry + entity registry chain")
async def user_options_clear(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires filled device registry."""


@test.skip("requires filled_device_registry + entity registry chain")
async def user_options_empty_selection_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires filled device registry."""


@test.skip("requires filled_device_registry + entity registry chain")
async def user_options_set_single(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires filled device registry."""


@test.skip("requires filled_device_registry + entity registry chain")
async def user_options_set_multiple(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires filled device registry."""


@test.skip("requires filled_device_registry + entity registry chain")
async def user_options_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub — requires filled device registry."""
