"""Test config flow."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from tests.common import MockConfigEntry
from tests.components.tasmota._fixtures import mqtt_mock as mqtt_mock_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke Depends() resolution."""


_PAYLOAD = (
    '{"ip":"192.168.0.136","dn":"Tasmota","fn":["Tasmota",null,null,null,null,'
    'null,null,null],"hn":"tasmota_0848A2","mac":"DC4F220848A2","md":"Sonoff Basic",'
    '"ty":0,"if":0,"ofln":"Offline","onln":"Online","state":["OFF","ON",'
    '"TOGGLE","HOLD"],"sw":"9.4.0.4","t":"tasmota_0848A2","ft":"%topic%/%prefix%/",'
    '"tp":["cmnd","stat","tele"],"rl":[1,0,0,0,0,0,0,0],"swc":[-1,-1,-1,-1,-1,-1,-1,-1],'
    '"swn":[null,null,null,null,null,null,null,null],"btn":[0,0,0,0,0,0,0,0],'
    '"so":{"4":0,"11":0,"13":0,"17":1,"20":0,"30":0,"68":0,"73":0,"82":0,"114":1,"117":0},'
    '"lk":1,"lt_st":0,"sho":[0,0,0,0],"ver":1}'
)


@test
async def mqtt_abort_if_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Check MQTT flow aborts when an entry already exists."""
    MockConfigEntry(domain="tasmota").add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        "tasmota", context={"source": config_entries.SOURCE_MQTT}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def mqtt_abort_invalid_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Check MQTT flow aborts if discovery topic is invalid."""
    discovery_info = MqttServiceInfo(
        topic="tasmota/discovery/DC4F220848A2/bla",
        payload=_PAYLOAD,
        qos=0,
        retain=False,
        subscribed_topic="tasmota/discovery/#",
        timestamp=None,
    )
    result = await hass.config_entries.flow.async_init(
        "tasmota", context={"source": config_entries.SOURCE_MQTT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_discovery_info")

    discovery_info = MqttServiceInfo(
        topic="tasmota/discovery/DC4F220848A2/config",
        payload="",
        qos=0,
        retain=False,
        subscribed_topic="tasmota/discovery/#",
        timestamp=None,
    )
    result = await hass.config_entries.flow.async_init(
        "tasmota", context={"source": config_entries.SOURCE_MQTT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_discovery_info")

    discovery_info = MqttServiceInfo(
        topic="tasmota/discovery/DC4F220848A2/config",
        payload=_PAYLOAD,
        qos=0,
        retain=False,
        subscribed_topic="tasmota/discovery/#",
        timestamp=None,
    )
    result = await hass.config_entries.flow.async_init(
        "tasmota", context={"source": config_entries.SOURCE_MQTT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def mqtt_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test we can finish a config flow through MQTT with custom prefix."""
    discovery_info = MqttServiceInfo(
        topic="tasmota/discovery/DC4F220848A2/config",
        payload=_PAYLOAD,
        qos=0,
        retain=False,
        subscribed_topic="tasmota/discovery/#",
        timestamp=None,
    )
    result = await hass.config_entries.flow.async_init(
        "tasmota", context={"source": config_entries.SOURCE_MQTT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].data).to_equal({"discovery_prefix": "tasmota/discovery"})


@test
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test we can finish a config flow."""
    result = await hass.config_entries.flow.async_init(
        "tasmota", context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].data).to_equal({"discovery_prefix": "tasmota/discovery"})


@test
async def user_setup_advanced(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test we can finish a config flow with advanced options."""
    result = await hass.config_entries.flow.async_init(
        "tasmota",
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"discovery_prefix": "test_tasmota/discovery"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].data).to_equal(
        {"discovery_prefix": "test_tasmota/discovery"}
    )


@test
async def user_setup_advanced_strip_wildcard(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test we can finish a config flow stripping wildcard."""
    result = await hass.config_entries.flow.async_init(
        "tasmota",
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"discovery_prefix": "test_tasmota/discovery/#"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].data).to_equal(
        {"discovery_prefix": "test_tasmota/discovery"}
    )


@test
async def user_setup_invalid_topic_prefix(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test abort on invalid discovery topic."""
    result = await hass.config_entries.flow.async_init(
        "tasmota",
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"discovery_prefix": "tasmota/config/##"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("invalid_discovery_topic")


@test
async def user_single_instance(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test we only allow a single config flow."""
    MockConfigEntry(domain="tasmota").add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        "tasmota", context={"source": config_entries.SOURCE_MQTT}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
