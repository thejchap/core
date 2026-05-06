"""Tryke fixtures for pvpc_hourly_pricing tests."""

from __future__ import annotations

from http import HTTPStatus

from tryke import Depends, fixture

from homeassistant.components.pvpc_hourly_pricing.const import ATTR_TARIFF, DOMAIN
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, CURRENCY_EURO, UnitOfEnergy

from tests.common import load_fixture
from tests.hass_fixtures import aioclient_mock as aioclient_mock_fx
from tests.test_util.aiohttp import AiohttpClientMocker

FIXTURE_JSON_PUBLIC_DATA_2023_01_06 = "PVPC_DATA_2023_01_06.json"
FIXTURE_JSON_ESIOS_DATA_PVPC_2023_01_06 = "PRICES_ESIOS_1001_2023_01_06.json"
_ESIOS_INDICATORS_FOR_EACH_SENSOR = ("1001", "1739", "1900", "10211")


def check_valid_state(
    state: object, tariff: str, value: object = None, key_attr: str | None = None
) -> None:
    """Ensure that sensor has a valid state and attributes."""
    assert state
    assert (
        state.attributes[ATTR_UNIT_OF_MEASUREMENT]
        == f"{CURRENCY_EURO}/{UnitOfEnergy.KILO_WATT_HOUR}"
    )
    try:
        _ = float(state.state)
        assert -0.1 < float(state.state) < 0.5
        assert state.attributes[ATTR_TARIFF] == tariff
    except ValueError:
        pass

    if value is not None and isinstance(value, str):
        assert state.state == value
    elif value is not None:
        assert abs(float(state.state) - float(value)) < 1e-6
    if key_attr is not None:
        assert abs(float(state.state) - state.attributes[key_attr]) < 1e-6


@fixture
def pvpc_aioclient_mock(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> AiohttpClientMocker:
    """Create a mock aioclient with pvpc responses."""
    mask_url_public = (
        "https://api.esios.ree.es/archives/70/download_json?locale=es&date={0}"
    )
    mask_url_esios = (
        "https://api.esios.ree.es/indicators/{0}"
        "?start_date={1}T00:00&end_date={1}T23:59"
    )
    example_day = "2023-01-06"
    aioclient_mock.get(
        mask_url_public.format(example_day),
        text=load_fixture(f"{DOMAIN}/{FIXTURE_JSON_PUBLIC_DATA_2023_01_06}"),
    )
    for esios_ind in _ESIOS_INDICATORS_FOR_EACH_SENSOR:
        aioclient_mock.get(
            mask_url_esios.format(esios_ind, example_day),
            text=load_fixture(f"{DOMAIN}/{FIXTURE_JSON_ESIOS_DATA_PVPC_2023_01_06}"),
        )

    aioclient_mock.get(
        mask_url_public.format("2023-01-07"),
        status=HTTPStatus.OK,
        text='{"message":"No values for specified archive"}',
    )
    for esios_ind in _ESIOS_INDICATORS_FOR_EACH_SENSOR:
        aioclient_mock.get(
            mask_url_esios.format(esios_ind, "2023-01-07"),
            status=HTTPStatus.OK,
            text=(
                '{"indicator":{"name":"Término de facturación de energía activa del '
                'PVPC 2.0TD","short_name":"PVPC T. 2.0TD","id":1001,"composited":false,'
                '"step_type":"linear","disaggregated":true,"magnitud":'
                '[{"name":"Precio","id":23}],"tiempo":[{"name":"Hora","id":4}],"geos":[],'
                '"values_updated_at":null,"values":[]}}'
            ).replace("1001", esios_ind),
        )
    for esios_ind in _ESIOS_INDICATORS_FOR_EACH_SENSOR:
        aioclient_mock.get(
            mask_url_esios.format(esios_ind, "2023-01-08"),
            status=HTTPStatus.UNAUTHORIZED,
            text="HTTP Token: Access denied.",
        )

    return aioclient_mock
