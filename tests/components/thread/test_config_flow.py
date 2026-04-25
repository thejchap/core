"""Test the Thread config flow."""

from ipaddress import ip_address
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import thread
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_async_zeroconf

from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_ZEROCONF_RECORD = ZeroconfServiceInfo(
    ip_address=ip_address("127.0.0.1"),
    ip_addresses=[ip_address("127.0.0.1")],
    hostname="HomeAssistant OpenThreadBorderRouter #0BBF",
    name="HomeAssistant OpenThreadBorderRouter #0BBF._meshcop._udp.local.",
    port=8080,
    properties={
        "rv": "1",
        "vn": "HomeAssistant",
        "mn": "OpenThreadBorderRouter",
        "nn": "OpenThread HC",
        "xp": "\xe6\x0f\xc7\xc1\x86!,\xe5",
        "tv": "1.3.0",
        "xa": "\xae\xeb/YKW\x0b\xbf",
        "sb": "\x00\x00\x01\xb1",
        "at": "\x00\x00\x00\x00\x00\x01\x00\x00",
        "pt": "\x8f\x06Q~",
        "sq": "3",
        "bb": "\xf0\xbf",
        "dn": "DefaultDomain",
    },
    type="_meshcop._udp.local.",
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zeroconf: MagicMock = Depends(mock_async_zeroconf),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def import_(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the import flow."""
    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            thread.DOMAIN, context={"source": "import"}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Thread")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(thread.DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal({})
    expect(config_entry.title).to_equal("Thread")
    expect(config_entry.unique_id).to_be(None)


@test.cases(
    test.case("import_source", source="import"),
    test.case("user_source", source="user"),
)
async def single_instance_allowed_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    source: str,
) -> None:
    """Test zeroconf single instance allowed abort reason."""
    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            thread.DOMAIN, context={"source": source}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            thread.DOMAIN, context={"source": "zeroconf"}, data=TEST_ZEROCONF_RECORD
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow."""
    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            thread.DOMAIN, context={"source": "user"}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Thread")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(thread.DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal({})
    expect(config_entry.title).to_equal("Thread")
    expect(config_entry.unique_id).to_be(None)


@test
async def zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        thread.DOMAIN, context={"source": "zeroconf"}, data=TEST_ZEROCONF_RECORD
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result["step_id"]).to_equal("confirm")

    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Thread")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(thread.DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal({})
    expect(config_entry.title).to_equal("Thread")
    expect(config_entry.unique_id).to_be(None)


@test
async def zeroconf_setup_onboarding(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we automatically finish a zeroconf flow during onboarding."""
    with (
        patch(
            "homeassistant.components.onboarding.async_is_onboarded", return_value=False
        ),
        patch(
            "homeassistant.components.thread.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            thread.DOMAIN, context={"source": "zeroconf"}, data=TEST_ZEROCONF_RECORD
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Thread")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("import_then_user", first_source="import", second_source="user"),
    test.case("user_then_import", first_source="user", second_source="import"),
)
async def import_and_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    first_source: str,
    second_source: str,
) -> None:
    """Test single instance allowed for user and import."""
    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            thread.DOMAIN, context={"source": first_source}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            thread.DOMAIN, context={"source": second_source}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test.cases(
    test.case("import_source", source="import"),
    test.case("user_source", source="user"),
)
async def zeroconf_then_import_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    source: str,
) -> None:
    """Test single instance allowed abort reason for import/user flow."""
    result = await hass.config_entries.flow.async_init(
        thread.DOMAIN, context={"source": "zeroconf"}, data=TEST_ZEROCONF_RECORD
    )
    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            thread.DOMAIN, context={"source": source}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test.cases(
    test.case("import_source", source="import"),
    test.case("user_source", source="user"),
)
async def zeroconf_in_progress_then_import_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    source: str,
) -> None:
    """Test priority (import/user) flow with zeroconf flow in progress."""
    result = await hass.config_entries.flow.async_init(
        thread.DOMAIN, context={"source": "zeroconf"}, data=TEST_ZEROCONF_RECORD
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            thread.DOMAIN, context={"source": source}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(mock_setup_entry.call_count).to_equal(1)

    flows_in_progress = hass.config_entries.flow.async_progress()
    expect(len(flows_in_progress)).to_equal(0)
