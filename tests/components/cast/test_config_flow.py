"""Tests for the Cast config flow."""

from unittest.mock import ANY, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import cast
from homeassistant.components.cast.home_assistant_cast import CAST_USER_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import cast_mock_patches, castbrowser_mock

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _cast: None = Depends(cast_mock_patches),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def creating_entry_sets_up_media_player(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up Cast loads the media player."""
    with (
        patch(
            "homeassistant.components.cast.media_player.async_setup_entry",
            return_value=True,
        ) as mock_setup,
        patch("pychromecast.discovery.discover_chromecasts", return_value=(True, None)),
        patch(
            "pychromecast.discovery.stop_discovery",
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            cast.DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

        await hass.async_block_till_done()

    expect(len(mock_setup.mock_calls)).to_equal(1)


@test.cases(
    test.case("user", source=config_entries.SOURCE_USER),
    test.case("zeroconf", source=config_entries.SOURCE_ZEROCONF),
)
async def single_instance(
    *,
    source: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we only allow a single config flow."""
    MockConfigEntry(domain="cast").add_to_hass(hass)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        "cast", context={"source": source}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can finish a config flow."""
    result = await hass.config_entries.flow.async_init(
        "cast", context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    users = await hass.auth.async_get_users()
    expect(
        bool(next((user for user in users if user.name == CAST_USER_NAME), None))
    ).to_be(True)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].data).to_equal(
        {
            "ignore_cec": [],
            "known_hosts": [],
            "uuid": [],
            "user_id": users[0].id,
        }
    )


@test
async def user_setup_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can finish a config flow."""
    result = await hass.config_entries.flow.async_init(
        "cast", context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"known_hosts": ["192.168.0.1", "", " ", "192.168.0.2 "]}
    )

    users = await hass.auth.async_get_users()
    expect(
        bool(next((user for user in users if user.name == CAST_USER_NAME), None))
    ).to_be(True)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].data).to_equal(
        {
            "ignore_cec": [],
            "known_hosts": ["192.168.0.1", "192.168.0.2"],
            "uuid": [],
            "user_id": users[0].id,
        }
    )


@test
async def zeroconf_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can finish a config flow through zeroconf."""
    result = await hass.config_entries.flow.async_init(
        "cast", context={"source": config_entries.SOURCE_ZEROCONF}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    users = await hass.auth.async_get_users()
    expect(
        bool(next((user for user in users if user.name == CAST_USER_NAME), None))
    ).to_be(True)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].data).to_equal(
        {
            "ignore_cec": [],
            "known_hosts": [],
            "uuid": [],
            "user_id": users[0].id,
        }
    )


@test
async def zeroconf_setup_onboarding(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we automatically finish a config flow through zeroconf during onboarding."""
    with patch(
        "homeassistant.components.onboarding.async_is_onboarded", return_value=False
    ):
        result = await hass.config_entries.flow.async_init(
            "cast", context={"source": config_entries.SOURCE_ZEROCONF}
        )

    users = await hass.auth.async_get_users()
    expect(
        bool(next((user for user in users if user.name == CAST_USER_NAME), None))
    ).to_be(True)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].data).to_equal(
        {
            "ignore_cec": [],
            "known_hosts": [],
            "uuid": [],
            "user_id": users[0].id,
        }
    )


@test.cases(
    test.case(
        "known_hosts",
        parameter="known_hosts",
        initial=["192.168.0.10", "192.168.0.11"],
        suggested=["192.168.0.10", "192.168.0.11"],
        user_input=["192.168.0.1", " ", "  192.168.0.2 "],
        updated=["192.168.0.1", "192.168.0.2"],
    ),
    test.case(
        "uuid",
        parameter="uuid",
        initial=["bla", "blu"],
        suggested="bla,blu",
        user_input="foo,  ,  bar ",
        updated=["foo", "bar"],
    ),
    test.case(
        "ignore_cec",
        parameter="ignore_cec",
        initial=["cast1", "cast2"],
        suggested="cast1,cast2",
        user_input="other_cast,  ,  some_cast ",
        updated=["other_cast", "some_cast"],
    ),
)
async def option_flow(
    *,
    parameter: str,
    initial: list[str],
    suggested: str | list[str],
    user_input: str | list[str],
    updated: list[str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    basic_parameters = ["known_hosts"]
    advanced_parameters = ["ignore_cec", "uuid"]

    data = {
        "ignore_cec": [],
        "known_hosts": [],
        "uuid": [],
    }
    data[parameter] = initial
    config_entry = MockConfigEntry(domain="cast", data=data)
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("basic_options")
    data_schema = result["data_schema"].schema
    expect(set(data_schema)).to_equal({"known_hosts"})
    orig_data = dict(config_entry.data)

    context = {"source": config_entries.SOURCE_USER, "show_advanced_options": True}
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context=context
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("basic_options")
    data_schema = result["data_schema"].schema
    for other_param in basic_parameters:
        if other_param == parameter:
            continue
        expect(get_schema_suggested_value(data_schema, other_param)).to_equal([])
    if parameter in basic_parameters:
        expect(get_schema_suggested_value(data_schema, parameter)).to_equal(suggested)

    user_input_dict: dict[str, str | list[str]] = {}
    if parameter in basic_parameters:
        user_input_dict[parameter] = user_input
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=user_input_dict,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("advanced_options")
    for other_param in basic_parameters:
        if other_param == parameter:
            continue
        expect(config_entry.data[other_param]).to_equal([])
    expect(config_entry.data[parameter]).to_equal(initial)

    data_schema = result["data_schema"].schema
    for other_param in advanced_parameters:
        if other_param == parameter:
            continue
        expect(get_schema_suggested_value(data_schema, other_param)).to_equal("")
    if parameter in advanced_parameters:
        expect(get_schema_suggested_value(data_schema, parameter)).to_equal(suggested)

    user_input_dict = {}
    if parameter in advanced_parameters:
        user_input_dict[parameter] = user_input
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=user_input_dict,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})
    for other_param in advanced_parameters:
        if other_param == parameter:
            continue
        expect(config_entry.data[other_param]).to_equal([])
    expect(config_entry.data[parameter]).to_equal(updated)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})
    expected_data = {**orig_data, "known_hosts": []}
    if parameter in advanced_parameters:
        expected_data[parameter] = updated
    expect(dict(config_entry.data)).to_equal(expected_data)


@test
async def known_hosts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    castbrowser: MagicMock = Depends(castbrowser_mock),
) -> None:
    """Test known hosts is passed to pychromecasts."""
    result = await hass.config_entries.flow.async_init(
        "cast", context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"known_hosts": ["192.168.0.1", "192.168.0.2"]}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    await hass.async_block_till_done(wait_background_tasks=True)
    config_entry = hass.config_entries.async_entries("cast")[0]

    expect(castbrowser.return_value.start_discovery.call_count).to_equal(1)
    castbrowser.assert_called_once_with(ANY, ANY, ["192.168.0.1", "192.168.0.2"])
    castbrowser.reset_mock()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"known_hosts": ["192.168.0.11", "192.168.0.12"]},
    )

    await hass.async_block_till_done(wait_background_tasks=True)

    castbrowser.return_value.start_discovery.assert_not_called()
    castbrowser.assert_not_called()
    castbrowser.return_value.host_browser.update_hosts.assert_called_once_with(
        ["192.168.0.11", "192.168.0.12"]
    )
