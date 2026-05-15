"""Tryke skip stub (pending port)."""

from unittest.mock import Mock

from tryke import expect, test

from homeassistant.components.logbook.models import EventAsRow, LazyEventPartialState


@test
def lazy_event_partial_state_context() -> None:
    """Test we can extract context from a lazy event partial state."""
    state = LazyEventPartialState(
        EventAsRow(
            row_id=1,
            event_type="event_type",
            event_data={},
            time_fired_ts=1,
            context_id_bin=b"1234123412341234",
            context_user_id_bin=b"1234123412341234",
            context_parent_id_bin=b"4444444444444444",
            state="state",
            entity_id="entity_id",
            icon="icon",
            context_only=False,
            data={},
            context=Mock(),
        ),
        {},
    )
    expect(state.context_id).to_equal("1H68SK8C9J6CT32CHK6GRK4CSM")
    expect(state.context_user_id).to_equal("31323334313233343132333431323334")
    expect(state.context_parent_id).to_equal("1M6GT38D1M6GT38D1M6GT38D1M")
    expect(state.event_type).to_equal("event_type")
    expect(state.entity_id).to_equal("entity_id")
    expect(state.state).to_equal("state")
