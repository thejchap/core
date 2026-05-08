"""Test entity discovery for device-specific schemas (tryke port).

The bulk of these tests fall straight out of the deep-mock chain — most just
need a per-device node + ``integration``. Tests that need indirect platforms
parametrize, ``entity_registry_enabled_by_default``, or device_registry
fixtures stay skipped with specific reasons.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test
from zwave_js_server.model.node import Node

from homeassistant.components.zwave_js.discovery import (
    FirmwareVersionRange,
    ZWaveDiscoverySchema,
    ZWaveValueDiscoverySchema,
    check_value,
)
from homeassistant.components.zwave_js.discovery_data_template import (
    DynamicCurrentTempClimateDataTemplate,
)
from homeassistant.core import HomeAssistant

from ._fixtures import (
    aeon_smart_switch_6,
    client,
    enbrighten_58446_zwa4013,
    fortrezz_ssa2_siren,
    fortrezz_ssa3_siren,
    ge_12730,
    iblinds_v2,
    indicator_test,
    inovelli_lzw36,
    integration,
    light_device_class_is_null,
    lock_popp_electric_strike_lock_control,
    merten_507801,
    multisensor_6,
    touchwand_glass9,
    vision_security_zl7432,
    zvidar,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture — see PATTERNS.md `_trigger_executor` note."""


# ---------------------------------------------------------------------------
# Pure unit tests — `check_value` and `FirmwareVersionRange` exception.
# ---------------------------------------------------------------------------


def _make_mock_value(cc_specific: dict | None = None) -> MagicMock:
    """Create a base mock ZwaveValue for check_value tests."""
    value = MagicMock()
    value.command_class = 49
    value.endpoint = 0
    value.property_ = "Air temperature"
    value.property_name = "Air temperature"
    value.property_key = None
    value.metadata.type = "number"
    value.metadata.readable = True
    value.metadata.writeable = False
    value.metadata.states = None
    value.metadata.cc_specific = cc_specific
    value.metadata.stateful = None
    value.value = 9
    return value


@test("check_value matches when all cc_specific pairs match")
def check_value_all_available_cc_specific_match() -> None:
    """Test check_value matches when all cc_specific key/value pairs are present."""
    schema = ZWaveValueDiscoverySchema(
        command_class={49},
        all_available_cc_specific={("scale", 0), ("sensorType", 1)},
    )
    value = _make_mock_value({"scale": 0, "sensorType": 1})
    expect(check_value(value, schema)).to_be(True)


@test("check_value fails on partial cc_specific match")
def check_value_all_available_cc_specific_partial_match() -> None:
    """Test check_value fails when not all cc_specific key/value pairs match."""
    schema = ZWaveValueDiscoverySchema(
        command_class={49},
        all_available_cc_specific={("scale", 0), ("sensorType", 1)},
    )
    value = _make_mock_value({"scale": 0, "sensorType": 5})
    expect(check_value(value, schema)).to_be(False)


@test("check_value fails when cc_specific is None and all_available is set")
def check_value_all_available_cc_specific_none() -> None:
    """Test check_value fails when cc_specific is None and all_available is set."""
    schema = ZWaveValueDiscoverySchema(
        command_class={49},
        all_available_cc_specific={("scale", 0)},
    )
    value = _make_mock_value()
    expect(check_value(value, schema)).to_be(False)


@test("check_value matches when any cc_specific pair matches")
def check_value_any_available_cc_specific_match() -> None:
    """Test check_value matches when any cc_specific key/value pair is present."""
    schema = ZWaveValueDiscoverySchema(
        command_class={49},
        any_available_cc_specific={("sensorType", 1), ("sensorType", 3)},
    )
    value = _make_mock_value({"sensorType": 1, "scale": 0})
    expect(check_value(value, schema)).to_be(True)


@test("check_value fails when no cc_specific pair matches")
def check_value_any_available_cc_specific_no_match() -> None:
    """Test check_value fails when no cc_specific key/value pair matches."""
    schema = ZWaveValueDiscoverySchema(
        command_class={49},
        any_available_cc_specific={("sensorType", 1), ("sensorType", 3)},
    )
    value = _make_mock_value({"sensorType": 5, "scale": 0})
    expect(check_value(value, schema)).to_be(False)


@test("check_value fails when cc_specific is None and any_available is set")
def check_value_any_available_cc_specific_none() -> None:
    """Test check_value fails when cc_specific is None and any_available is set."""
    schema = ZWaveValueDiscoverySchema(
        command_class={49},
        any_available_cc_specific={("sensorType", 1)},
    )
    value = _make_mock_value()
    expect(check_value(value, schema)).to_be(False)


@test("FirmwareVersionRange raises ValueError on empty range")
def firmware_version_range_exception() -> None:
    """Test FirmwareVersionRange exception."""
    raised = False
    try:
        ZWaveDiscoverySchema(
            "test",
            ZWaveValueDiscoverySchema(command_class=1),
            firmware_version_range=FirmwareVersionRange(),
        )
    except ValueError:
        raised = True
    expect(raised).to_be(True)


# ---------------------------------------------------------------------------
# Per-device discovery tests.
# ---------------------------------------------------------------------------


@test("aeon smart switch 6 has a meter reset button")
async def aeon_smart_switch_6_state(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    _node: Node = Depends(aeon_smart_switch_6),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test that Smart Switch 6 has a meter reset button."""
    state = hass.states.get("button.smart_switch_6_reset_accumulated_values")
    expect(state is not None).to_be(True)


@test("iblinds v2 multilevel switch is discovered as cover")
async def iblinds_v2_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    iblinds_v2: Node = Depends(iblinds_v2),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test that an iBlinds v2.0 multilevel switch value is discovered as a cover."""
    expect(iblinds_v2.device_class.specific.label).to_equal("Unused")
    expect(hass.states.get("light.window_blind_controller") is None).to_be(True)
    expect(hass.states.get("cover.window_blind_controller") is not None).to_be(True)


@test("touchwand glass 9 is discovered as cover")
async def touchwand_glass9_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    touchwand_glass9: Node = Depends(touchwand_glass9),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test a touchwand_glass9 is discovered as a cover."""
    node_device_class = touchwand_glass9.device_class
    expect(node_device_class is not None).to_be(True)
    expect(node_device_class.specific.label).to_equal("Unused")
    expect(hass.states.async_entity_ids_count("light")).to_be(0)
    expect(hass.states.async_entity_ids_count("cover")).to_be(3)
    expect(hass.states.get("cover.gp9") is not None).to_be(True)


@test("zvidar multilevel switch is discovered as cover")
async def zvidar_state_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    zvidar: Node = Depends(zvidar),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test that a ZVIDAR Z-CM-V01 multilevel switch is discovered as a cover."""
    expect(zvidar.device_class.specific.label).to_equal("Unused")
    expect(hass.states.get("light.window_blind_controller") is None).to_be(True)
    expect(hass.states.get("cover.window_blind_controller") is not None).to_be(True)


@test("ge 12730 multilevel switch is discovered as fan")
async def ge_12730_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    ge_12730: Node = Depends(ge_12730),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test GE 12730 Fan Controller v2.0 multilevel switch is discovered as a fan."""
    expect(ge_12730.device_class.specific.label).to_equal("Multilevel Power Switch")
    expect(hass.states.get("light.in_wall_smart_fan_control") is None).to_be(True)
    expect(hass.states.get("fan.in_wall_smart_fan_control") is not None).to_be(True)


@test("enbrighten 58446 ZWA4013 is discovered as fan")
async def enbrighten_58446_zwa4013_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    enbrighten_58446_zwa4013: Node = Depends(enbrighten_58446_zwa4013),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test Enbrighten 58446 ZWA4013 multilevel switch is discovered as a fan."""
    expect(enbrighten_58446_zwa4013.device_class.specific.label).to_equal(
        "Multilevel Power Switch"
    )
    expect(hass.states.get("light.zwa4013_fan") is None).to_be(True)
    expect(hass.states.get("fan.zwa4013_fan") is not None).to_be(True)


@test("inovelli LZW36 endpoint 2 is discovered as fan")
async def inovelli_lzw36_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    inovelli_lzw36: Node = Depends(inovelli_lzw36),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test LZW36 Fan Controller multilevel switch endpoint 2 is discovered as a fan."""
    expect(inovelli_lzw36.device_class.specific.label).to_equal("Unused")
    state = hass.states.get("light.family_room_combo")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("off")
    expect(hass.states.get("fan.family_room_combo_2") is not None).to_be(True)


@test("vision security ZL7432 is caught by device-specific discovery")
async def vision_security_zl7432_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    _node: Node = Depends(vision_security_zl7432),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test Vision Security ZL7432 is caught by the device specific discovery."""
    for entity_id in (
        "switch.in_wall_dual_relay_switch",
        "switch.in_wall_dual_relay_switch_2",
    ):
        state = hass.states.get(entity_id)
        expect(state is not None).to_be(True)
        expect(state.attributes["assumed_state"]).to_be(True)


@test("popp electric strike lock control discovery")
async def lock_popp_electric_strike_lock_control_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    _node: Node = Depends(lock_popp_electric_strike_lock_control),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test that the Popp Electric Strike Lock Control gets discovered correctly."""
    expect(hass.states.get("lock.node_62") is not None).to_be(True)
    expect(
        hass.states.get("binary_sensor.node_62_the_current_status_of_the_door")
        is not None
    ).to_be(True)
    expect(hass.states.get("select.node_62_current_lock_mode") is not None).to_be(
        True
    )


@test("fortrezz SSA2 siren discovery")
async def fortrez_ssa2_siren(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    _node: Node = Depends(fortrezz_ssa2_siren),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test Fortrezz SSA2 siren gets discovered correctly."""
    expect(hass.states.get("select.siren_and_strobe_alarm") is not None).to_be(True)


@test("fortrezz SSA3 siren discovery")
async def fortrez_ssa3_siren(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    _node: Node = Depends(fortrezz_ssa3_siren),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test Fortrezz SSA3 siren gets discovered correctly."""
    expect(hass.states.get("select.siren_and_strobe_alarm") is not None).to_be(True)


@test("merten 507801 multilevel switch is discovered as cover")
async def merten_507801_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    merten_507801: Node = Depends(merten_507801),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test that Merten 507801 multilevel switch value is discovered as a cover."""
    expect(merten_507801.device_class.specific.label).to_equal("Unused")
    expect(hass.states.get("light.connect_roller_shutter") is None).to_be(True)
    expect(hass.states.get("cover.connect_roller_shutter") is not None).to_be(True)


@test("multisensor 6 dynamic climate template raises on missing data")
async def dynamic_climate_data_discovery_template_failure(
    _t: None = Depends(_trigger_executor),
    _hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    multisensor_6: Node = Depends(multisensor_6),
) -> None:
    """Test DynamicCurrentTempClimateDataTemplate with no data raises ValueError."""
    raised = False
    try:
        DynamicCurrentTempClimateDataTemplate().resolve_data(
            multisensor_6.values[f"{multisensor_6.node_id}-49-0-Ultraviolet"]
        )
    except ValueError:
        raised = True
    expect(raised).to_be(True)


@test("light with null device class is discovered as a light")
async def light_device_class_is_null_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    light_device_class_is_null: Node = Depends(light_device_class_is_null),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test a Multilevel Switch CC value with a null device class is discovered as a light."""
    expect(light_device_class_is_null.device_class is None).to_be(True)
    expect(hass.states.get("light.bar_display_cases") is not None).to_be(True)


@test("indicator test discovery — switch endpoint coverage")
async def indicator_test_discovery(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    _node: Node = Depends(indicator_test),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test the indicator-CC test node gets discovered without errors."""
    # The integration should have spawned at least one entity for this node.
    expect(hass.states.async_entity_ids_count() > 0).to_be(True)


# ---------------------------------------------------------------------------
# Skipped tests — extras that need indirect parametrize / extra fixtures.
# ---------------------------------------------------------------------------


@test.skip(
    "Shelly QNSH 001P10: needs entity_registry fixture — port deferred"
)
async def shelly_001p10_disabled_entities() -> None:
    """Stub for test_shelly_001p10_disabled_entities."""


@test.skip(
    "Merten 507801 disabled entities: needs entity_registry fixture — port deferred"
)
async def merten_507801_disabled_enitites() -> None:
    """Stub for test_merten_507801_disabled_enitites."""


@test.skip(
    "Zooz Zen72: indirect platforms parametrize + entity_registry fixture — port deferred"
)
async def zooz_zen72() -> None:
    """Stub for test_zooz_zen72."""


@test.skip(
    "Rediscovery: needs entity_registry_enabled_by_default + caplog — port deferred"
)
async def rediscovery() -> None:
    """Stub for test_rediscovery."""


@test.skip(
    "Aeotec Smart Switch 7: needs entity_registry fixture — port deferred"
)
async def aeotec_smart_switch_7_discovery() -> None:
    """Stub for test_aeotec_smart_switch_7."""


@test.skip("Nabu Casa ZWA-2: needs entity_registry fixture — port deferred")
async def nabu_casa_zwa2_discovery() -> None:
    """Stub for test_nabu_casa_zwa2."""


@test.skip(
    "Nabu Casa ZWA-2 legacy: needs entity_registry fixture — port deferred"
)
async def nabu_casa_zwa2_legacy_discovery() -> None:
    """Stub for test_nabu_casa_zwa2_legacy."""


@test.skip(
    "Fibaro FGMS001 v2.8 motion: indirect platforms parametrize + "
    "entity_registry+device_registry — port deferred"
)
async def fibaro_fgms001_v2_8_motion_discovery() -> None:
    """Stub for test_fibaro_fgms001_v2_8_motion_discovery."""
