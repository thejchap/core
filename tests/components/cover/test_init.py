"""The tests for Cover."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import cover
from homeassistant.components.cover import CoverState
from homeassistant.const import ATTR_ENTITY_ID, CONF_PLATFORM, SERVICE_TOGGLE
from homeassistant.core import HomeAssistant, ServiceResponse
from homeassistant.helpers.entity import Entity
from homeassistant.setup import async_setup_component

from ._fixtures import mock_cover_entities as mock_cover_entities_fixture
from .common import MockCover

from tests.common import setup_test_component_platform
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-level anchor for tryke fixture resolution."""
    return 0


@test
async def services(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test the provided services."""
    setup_test_component_platform(hass, cover.DOMAIN, mock_cover_entities)

    expect(
        await async_setup_component(
            hass, cover.DOMAIN, {cover.DOMAIN: {CONF_PLATFORM: "test"}}
        )
    ).to_be(True)
    await hass.async_block_till_done()

    # ent1 = cover without tilt and position
    # ent2 = cover with position but no tilt
    # ent3 = cover with simple tilt functions and no position
    # ent4 = cover with all tilt functions but no position
    # ent5 = cover with all functions
    # ent6 = cover with only open/close, but also reports opening/closing
    ent1, ent2, ent3, ent4, ent5, ent6 = mock_cover_entities

    # Test init all covers should be open
    expect(is_open(hass, ent1)).to_be(True)
    expect(is_open(hass, ent2, 50)).to_be(True)
    expect(is_open(hass, ent3)).to_be(True)
    expect(is_open(hass, ent4)).to_be(True)
    expect(is_open(hass, ent5, 50)).to_be(True)
    expect(is_open(hass, ent6)).to_be(True)

    # call basic toggle services
    await call_service(hass, SERVICE_TOGGLE, ent1)
    await call_service(hass, SERVICE_TOGGLE, ent2)
    await call_service(hass, SERVICE_TOGGLE, ent3)
    await call_service(hass, SERVICE_TOGGLE, ent4)
    await call_service(hass, SERVICE_TOGGLE, ent5)
    await call_service(hass, SERVICE_TOGGLE, ent6)

    # entities should be either closed or closing, depending on if they report transitional states
    expect(is_closed(hass, ent1)).to_be(True)
    expect(is_closing(hass, ent2, 50)).to_be(True)
    expect(is_closed(hass, ent3)).to_be(True)
    expect(is_closed(hass, ent4)).to_be(True)
    expect(is_closing(hass, ent5, 50)).to_be(True)
    expect(is_closing(hass, ent6)).to_be(True)

    # call basic toggle services and set different cover position states
    await call_service(hass, SERVICE_TOGGLE, ent1)
    set_cover_position(ent2, 0)
    await call_service(hass, SERVICE_TOGGLE, ent2)
    await call_service(hass, SERVICE_TOGGLE, ent3)
    await call_service(hass, SERVICE_TOGGLE, ent4)
    set_cover_position(ent5, 15)
    await call_service(hass, SERVICE_TOGGLE, ent5)
    await call_service(hass, SERVICE_TOGGLE, ent6)

    # entities should be in correct state depending on the SUPPORT_STOP feature and cover position
    expect(is_open(hass, ent1)).to_be(True)
    expect(is_closed(hass, ent2, 0)).to_be(True)
    expect(is_open(hass, ent3)).to_be(True)
    expect(is_open(hass, ent4)).to_be(True)
    expect(is_open(hass, ent5, 15)).to_be(True)
    expect(is_opening(hass, ent6)).to_be(True)

    # call basic toggle services
    await call_service(hass, SERVICE_TOGGLE, ent1)
    await call_service(hass, SERVICE_TOGGLE, ent2)
    await call_service(hass, SERVICE_TOGGLE, ent3)
    await call_service(hass, SERVICE_TOGGLE, ent4)
    await call_service(hass, SERVICE_TOGGLE, ent5)
    await call_service(hass, SERVICE_TOGGLE, ent6)

    # entities should be in correct state depending on the SUPPORT_STOP feature and cover position
    expect(is_closed(hass, ent1)).to_be(True)
    expect(is_opening(hass, ent2, 0, closed=True)).to_be(True)
    expect(is_closed(hass, ent3)).to_be(True)
    expect(is_closed(hass, ent4)).to_be(True)
    expect(is_opening(hass, ent5, 15)).to_be(True)
    expect(is_closing(hass, ent6)).to_be(True)

    # Without STOP but still reports opening/closing has a 4th possible toggle state
    set_state(ent6, CoverState.CLOSED)
    await call_service(hass, SERVICE_TOGGLE, ent6)
    expect(is_opening(hass, ent6)).to_be(True)

    # After the unusual state transition: closing -> fully open, toggle should close
    set_state(ent5, CoverState.OPEN)
    await call_service(hass, SERVICE_TOGGLE, ent5)  # Start closing
    expect(is_closing(hass, ent5, 15)).to_be(True)
    set_state(
        ent5, CoverState.OPEN
    )  # Unusual state transition from closing -> fully open
    set_cover_position(ent5, 100)
    await call_service(hass, SERVICE_TOGGLE, ent5)  # Should close, not open
    expect(is_closing(hass, ent5, 100)).to_be(True)


def call_service(hass: HomeAssistant, service: str, ent: Entity) -> ServiceResponse:
    """Call any service on entity."""
    return hass.services.async_call(
        cover.DOMAIN, service, {ATTR_ENTITY_ID: ent.entity_id}, blocking=True
    )


def set_cover_position(ent, position) -> None:
    """Set a position value to a cover."""
    ent._values["current_cover_position"] = position


def set_state(ent, state) -> None:
    """Set the state of a cover."""
    ent._values["state"] = state


def _check_state(
    hass: HomeAssistant,
    ent: Entity,
    *,
    expected_state: str,
    expected_position: int | None,
    expected_is_closed: bool,
) -> bool:
    """Check if the state of a cover is as expected."""
    state = hass.states.get(ent.entity_id)
    correct_state = state.state == expected_state
    correct_is_closed = state.attributes.get("is_closed") == expected_is_closed
    correct_position = state.attributes.get("current_position") == expected_position
    return all([correct_state, correct_is_closed, correct_position])


def is_open(hass: HomeAssistant, ent: Entity, position: int | None = None) -> bool:
    """Return if the cover is open based on the statemachine."""
    return _check_state(
        hass,
        ent,
        expected_state=CoverState.OPEN,
        expected_position=position,
        expected_is_closed=False,
    )


def is_opening(
    hass: HomeAssistant,
    ent: Entity,
    position: int | None = None,
    *,
    closed: bool = False,
) -> bool:
    """Return if the cover is opening based on the statemachine."""
    return _check_state(
        hass,
        ent,
        expected_state=CoverState.OPENING,
        expected_position=position,
        expected_is_closed=closed,
    )


def is_closed(hass: HomeAssistant, ent: Entity, position: int | None = None) -> bool:
    """Return if the cover is closed based on the statemachine."""
    return _check_state(
        hass,
        ent,
        expected_state=CoverState.CLOSED,
        expected_position=position,
        expected_is_closed=True,
    )


def is_closing(hass: HomeAssistant, ent: Entity, position: int | None = None) -> bool:
    """Return if the cover is closing based on the statemachine."""
    return _check_state(
        hass,
        ent,
        expected_state=CoverState.CLOSING,
        expected_position=position,
        expected_is_closed=False,
    )
