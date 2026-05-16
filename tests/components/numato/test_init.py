"""Tests for the numato integration."""

from numato_gpio import NumatoGpioError
from tryke import Depends, expect, fixture, test

from homeassistant.components import numato
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import config as config_fixture, numato_fixture as numato_fixture_fx
from .common import NUMATO_CFG, mockup_raise, mockup_return
from .numato_mock import NumatoModuleMock

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test
async def setup_no_devices(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
) -> None:
    """Test handling of an 'empty' discovery.

    Platform setups are expected to return after handling errors locally
    without raising.
    """
    numato_fixture.discover = mockup_return
    expect(await async_setup_component(hass, "numato", NUMATO_CFG)).to_be(True)
    expect(len(numato_fixture.devices)).to_equal(0)


@test
async def fail_setup_raising_discovery(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
) -> None:
    """Test handling of an exception during discovery.

    Setup shall return False.
    """
    numato_fixture.discover = mockup_raise
    expect(await async_setup_component(hass, "numato", NUMATO_CFG)).to_be(False)
    await hass.async_block_till_done()


@test
async def hass_numato_api_wrong_port_directions(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
) -> None:
    """Test handling of wrong port directions.

    This won't happen in the current platform implementation but would raise
    in case of an introduced bug in the platforms.
    """
    numato_fixture.discover()
    api = numato.NumatoAPI()
    api.setup_output(0, 5)
    api.setup_input(0, 2)
    api.setup_output(0, 6)
    expect(lambda: api.read_adc_input(0, 5)).to_raise(NumatoGpioError)
    expect(lambda: api.read_input(0, 6)).to_raise(NumatoGpioError)
    expect(lambda: api.write_output(0, 2, 1)).to_raise(NumatoGpioError)


@test
async def hass_numato_api_errors(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
) -> None:
    """Test whether Home Assistant numato API (re-)raises errors."""
    numato_fixture.discover()
    numato_fixture.devices[0].setup = mockup_raise
    numato_fixture.devices[0].adc_read = mockup_raise
    numato_fixture.devices[0].read = mockup_raise
    numato_fixture.devices[0].write = mockup_raise
    api = numato.NumatoAPI()
    expect(lambda: api.setup_input(0, 5)).to_raise(NumatoGpioError)
    expect(lambda: api.read_adc_input(0, 1)).to_raise(NumatoGpioError)
    expect(lambda: api.read_input(0, 2)).to_raise(NumatoGpioError)
    expect(lambda: api.write_output(0, 2, 1)).to_raise(NumatoGpioError)


@test
async def invalid_port_number(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
    config: dict = Depends(config_fixture),
) -> None:
    """Test validation of ADC port number type."""
    sensorports_cfg = config["numato"]["devices"][0]["sensors"]["ports"]
    port1_config = sensorports_cfg["1"]
    sensorports_cfg["one"] = port1_config
    del sensorports_cfg["1"]
    expect(await async_setup_component(hass, "numato", config)).to_be(False)
    await hass.async_block_till_done()
    expect(bool(numato_fixture.devices)).to_be(False)


@test
async def too_low_adc_port_number(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
    config: dict = Depends(config_fixture),
) -> None:
    """Test handling of failing component setup.

    Tries setting up an ADC on a port below (0) the allowed range.
    """
    sensorports_cfg = config["numato"]["devices"][0]["sensors"]["ports"]
    sensorports_cfg.update({0: {"name": "toolow"}})
    expect(await async_setup_component(hass, "numato", config)).to_be(False)
    expect(bool(numato_fixture.devices)).to_be(False)


@test
async def too_high_adc_port_number(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
    config: dict = Depends(config_fixture),
) -> None:
    """Test handling of failing component setup.

    Tries setting up an ADC on a port above (8) the allowed range.
    """
    sensorports_cfg = config["numato"]["devices"][0]["sensors"]["ports"]
    sensorports_cfg.update({8: {"name": "toohigh"}})
    expect(await async_setup_component(hass, "numato", config)).to_be(False)
    expect(bool(numato_fixture.devices)).to_be(False)


@test
async def invalid_adc_range_value_type(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
    config: dict = Depends(config_fixture),
) -> None:
    """Test validation of ADC range config's types.

    Replaces the source range beginning by a string.
    """
    sensorports_cfg = config["numato"]["devices"][0]["sensors"]["ports"]
    sensorports_cfg["1"]["source_range"][0] = "zero"
    expect(await async_setup_component(hass, "numato", config)).to_be(False)
    expect(bool(numato_fixture.devices)).to_be(False)


@test
async def invalid_adc_source_range_length(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
    config: dict = Depends(config_fixture),
) -> None:
    """Test validation of ADC range config's length.

    Adds an element to the source range.
    """
    sensorports_cfg = config["numato"]["devices"][0]["sensors"]["ports"]
    sensorports_cfg["1"]["source_range"].append(42)
    expect(await async_setup_component(hass, "numato", config)).to_be(False)
    expect(bool(numato_fixture.devices)).to_be(False)


@test
async def invalid_adc_source_range_order(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
    config: dict = Depends(config_fixture),
) -> None:
    """Test validation of ADC range config's order.

    Sets the source range to a decreasing [2, 1].
    """
    sensorports_cfg = config["numato"]["devices"][0]["sensors"]["ports"]
    sensorports_cfg["1"]["source_range"] = [2, 1]
    expect(await async_setup_component(hass, "numato", config)).to_be(False)
    expect(bool(numato_fixture.devices)).to_be(False)


@test
async def invalid_adc_destination_range_value_type(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
    config: dict = Depends(config_fixture),
) -> None:
    """Test validation of ADC range .

    Replaces the destination range beginning by a string.
    """
    sensorports_cfg = config["numato"]["devices"][0]["sensors"]["ports"]
    sensorports_cfg["1"]["destination_range"][0] = "zero"
    expect(await async_setup_component(hass, "numato", config)).to_be(False)
    expect(bool(numato_fixture.devices)).to_be(False)


@test
async def invalid_adc_destination_range_length(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
    config: dict = Depends(config_fixture),
) -> None:
    """Test validation of ADC range config's length.

    Adds an element to the destination range.
    """
    sensorports_cfg = config["numato"]["devices"][0]["sensors"]["ports"]
    sensorports_cfg["1"]["destination_range"].append(42)
    expect(await async_setup_component(hass, "numato", config)).to_be(False)
    expect(bool(numato_fixture.devices)).to_be(False)


@test
async def invalid_adc_destination_range_order(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    numato_fixture: NumatoModuleMock = Depends(numato_fixture_fx),
    config: dict = Depends(config_fixture),
) -> None:
    """Test validation of ADC range config's order.

    Sets the destination range to a decreasing [2, 1].
    """
    sensorports_cfg = config["numato"]["devices"][0]["sensors"]["ports"]
    sensorports_cfg["1"]["destination_range"] = [2, 1]
    expect(await async_setup_component(hass, "numato", config)).to_be(False)
    expect(bool(numato_fixture.devices)).to_be(False)
