"""Test the DoorBird config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
from doorbirdpy import DoorBird
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.doorbird.const import (
    CONF_EVENTS,
    DEFAULT_DOORBELL_EVENT,
    DEFAULT_MOTION_EVENT,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import (
    VALID_CONFIG,
    get_mock_doorbird_api,
    mock_not_found_exception,
    mock_unauthorized_exception,
)
from ._fixtures import doorbird_api

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: DoorBird = Depends(doorbird_api),
) -> None:
    """Test we get the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.doorbird.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.doorbird.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.2.3.4")
    expect(result2["data"]).to_equal(
        {
            "host": "1.2.3.4",
            "name": "mydoorbird",
            "password": "password",
            "username": "friend",
        }
    )
    expect(result2["options"]).to_equal(
        {CONF_EVENTS: [DEFAULT_DOORBELL_EVENT, DEFAULT_MOTION_EVENT]}
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_zeroconf_wrong_oui(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort when we get the wrong OUI via zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.8"),
            ip_addresses=[ip_address("192.168.1.8")],
            hostname="mock_hostname",
            name="Doorstation - abc123._axis-video._tcp.local.",
            port=None,
            properties={"macaddress": "notdoorbirdoui"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_doorbird_device")


@test
async def form_zeroconf_link_local_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort when we get a link local address via zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("169.254.103.61"),
            ip_addresses=[ip_address("169.254.103.61")],
            hostname="mock_hostname",
            name="Doorstation - abc123._axis-video._tcp.local.",
            port=None,
            properties={"macaddress": "1CCAE3DOORBIRD"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("link_local_address")


@test
async def form_zeroconf_ipv4_address(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: DoorBird = Depends(doorbird_api),
) -> None:
    """Test we abort and update the ip address from zeroconf with an ipv4 address."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1CCAE3AAAAAA",
        data=VALID_CONFIG,
        options={CONF_EVENTS: ["event1", "event2", "event3"]},
    )
    config_entry.add_to_hass(hass)

    api.info.return_value = {
        "PRIMARY_MAC_ADDR": "1CCAE3AAAAAA",
        "WIFI_MAC_ADDR": "1CCAE3BBBBBB",
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("4.4.4.4"),
            ip_addresses=[ip_address("4.4.4.4")],
            hostname="mock_hostname",
            name="Doorstation - abc123._axis-video._tcp.local.",
            port=None,
            properties={"macaddress": "1CCAE3AAAAAA"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("4.4.4.4")


@test
async def form_zeroconf_ignored_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: DoorBird = Depends(doorbird_api),
) -> None:
    """Test we abort when the entry was ignored, without attempting to connect."""
    config_entry = MockConfigEntry(
        source=config_entries.SOURCE_IGNORE,
        domain=DOMAIN,
        unique_id="1CCAE3AAAAAA",
        data={},
        options={},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("4.4.4.4"),
            ip_addresses=[ip_address("4.4.4.4")],
            hostname="mock_hostname",
            name="Doorstation - abc123._axis-video._tcp.local.",
            port=None,
            properties={"macaddress": "1CCAE3AAAAAA"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form_zeroconf_ipv4_address_wrong_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: DoorBird = Depends(doorbird_api),
) -> None:
    """Test we abort when the device MAC doesn't match during zeroconf update."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1CCAE3AAAAAA",
        data=VALID_CONFIG,
        options={CONF_EVENTS: ["event1", "event2", "event3"]},
    )
    config_entry.add_to_hass(hass)

    api.info.return_value = {
        "PRIMARY_MAC_ADDR": "1CCAE3DIFFERENT",
        "WIFI_MAC_ADDR": "1CCAE3BBBBBB",
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("4.4.4.4"),
            ip_addresses=[ip_address("4.4.4.4")],
            hostname="mock_hostname",
            name="Doorstation - abc123._axis-video._tcp.local.",
            port=None,
            properties={"macaddress": "1CCAE3AAAAAA"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_device")
    expect(config_entry.data[CONF_HOST]).to_equal("1.2.3.4")


@test
async def form_zeroconf_ipv4_address_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: DoorBird = Depends(doorbird_api),
) -> None:
    """Test we abort when we cannot connect to validate during zeroconf update."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1CCAE3AAAAAA",
        data=VALID_CONFIG,
        options={CONF_EVENTS: ["event1", "event2", "event3"]},
    )
    config_entry.add_to_hass(hass)

    api.info.side_effect = mock_unauthorized_exception()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("4.4.4.4"),
            ip_addresses=[ip_address("4.4.4.4")],
            hostname="mock_hostname",
            name="Doorstation - abc123._axis-video._tcp.local.",
            port=None,
            properties={"macaddress": "1CCAE3AAAAAA"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")
    expect(config_entry.data[CONF_HOST]).to_equal("1.2.3.4")


@test
async def form_zeroconf_non_ipv4_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort when we get a non ipv4 address via zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("fd00::b27c:63bb:cc85:4ea0"),
            ip_addresses=[ip_address("fd00::b27c:63bb:cc85:4ea0")],
            hostname="mock_hostname",
            name="Doorstation - abc123._axis-video._tcp.local.",
            port=None,
            properties={"macaddress": "1CCAE3DOORBIRD"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_ipv4_address")


@test
async def form_zeroconf_correct_oui(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: DoorBird = Depends(doorbird_api),
) -> None:
    """Test we can setup from zeroconf with the correct OUI source."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.5"),
            ip_addresses=[ip_address("192.168.1.5")],
            hostname="mock_hostname",
            name="Doorstation - abc123._axis-video._tcp.local.",
            port=None,
            properties={"macaddress": "1CCAE3DOORBIRD"},
            type="mock_type",
        ),
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with (
        patch("homeassistant.components.logbook.async_setup", return_value=True),
        patch(
            "homeassistant.components.doorbird.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.doorbird.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_CONFIG
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("1.2.3.4")
    expect(result2["data"]).to_equal(
        {
            "host": "1.2.3.4",
            "name": "mydoorbird",
            "password": "password",
            "username": "friend",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "client_response_error",
        doorbell_state_side_effect=aiohttp.ClientResponseError(
            request_info=Mock(), history=Mock(), status=404
        ),
    ),
    test.case("os_error", doorbell_state_side_effect=OSError),
    test.case("none", doorbell_state_side_effect=None),
)
async def form_zeroconf_correct_oui_wrong_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: DoorBird = Depends(doorbird_api),
    *,
    doorbell_state_side_effect: Exception | None,
) -> None:
    """Test we can setup from zeroconf with the correct OUI source but not a doorstation."""
    doorbirdapi = get_mock_doorbird_api(info={"WIFI_MAC_ADDR": "macaddr"})
    type(doorbirdapi).doorbell_state = AsyncMock(side_effect=doorbell_state_side_effect)

    with patch(
        "homeassistant.components.doorbird.config_flow.DoorBird",
        return_value=doorbirdapi,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("192.168.1.5"),
                ip_addresses=[ip_address("192.168.1.5")],
                hostname="mock_hostname",
                name="Doorstation - abc123._axis-video._tcp.local.",
                port=None,
                properties={"macaddress": "1CCAE3DOORBIRD"},
                type="mock_type",
            ),
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_doorbird_device")


@test
async def form_user_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    doorbirdapi = get_mock_doorbird_api(info_side_effect=OSError)
    with patch(
        "homeassistant.components.doorbird.config_flow.DoorBird",
        return_value=doorbirdapi,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_user_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot invalid auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_error = mock_unauthorized_exception()
    doorbirdapi = get_mock_doorbird_api(info_side_effect=mock_error)
    with patch(
        "homeassistant.components.doorbird.config_flow.DoorBird",
        return_value=doorbirdapi,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_user_doorbird_not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: DoorBird = Depends(doorbird_api),
) -> None:
    """Test handling unable to connect to the device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_error = mock_not_found_exception()
    doorbirdapi = get_mock_doorbird_api(info_side_effect=mock_error)
    with patch(
        "homeassistant.components.doorbird.config_flow.DoorBird",
        return_value=doorbirdapi,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    with (
        patch(
            "homeassistant.components.doorbird.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.doorbird.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], VALID_CONFIG
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("1.2.3.4")
    expect(result3["data"]).to_equal(
        {
            "host": "1.2.3.4",
            "name": "mydoorbird",
            "password": "password",
            "username": "friend",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_user_doorbird_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: DoorBird = Depends(doorbird_api),
) -> None:
    """Test handling unable an unknown exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    doorbirdapi = get_mock_doorbird_api(info_side_effect=ValueError)
    with patch(
        "homeassistant.components.doorbird.config_flow.DoorBird",
        return_value=doorbirdapi,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})

    with (
        patch(
            "homeassistant.components.doorbird.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.doorbird.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], VALID_CONFIG
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("1.2.3.4")
    expect(result3["data"]).to_equal(
        {
            "host": "1.2.3.4",
            "name": "mydoorbird",
            "password": "password",
            "username": "friend",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="abcde12345",
        data=VALID_CONFIG,
        options={CONF_EVENTS: ["event1", "event2", "event3"]},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.doorbird.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_EVENTS: "eventa,   eventc,    eventq"}
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(config_entry.options).to_equal(
            {CONF_EVENTS: ["eventa", "eventc", "eventq"]}
        )


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_NAME: "DoorBird",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    config_entry.add_to_hass(hass)
    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    expect(len(flows)).to_equal(1)
    flow = flows[0]

    mock_error = mock_unauthorized_exception()
    doorbirdapi = get_mock_doorbird_api(info_side_effect=mock_error)
    with patch(
        "homeassistant.components.doorbird.config_flow.DoorBird",
        return_value=doorbirdapi,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})

    doorbirdapi = get_mock_doorbird_api(info={"WIFI_MAC_ADDR": "macaddr"})
    with (
        patch(
            "homeassistant.components.doorbird.config_flow.DoorBird",
            return_value=doorbirdapi,
        ),
        patch(
            "homeassistant.components.doorbird.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.doorbird.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)
