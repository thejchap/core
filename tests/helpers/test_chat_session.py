"""Test the chat session helper."""

from datetime import timedelta
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import chat_session
from homeassistant.util import dt as dt_util, ulid as ulid_util

from tests.common import async_fire_time_changed
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("none_start_id", start_id=None, given_id="mock-ulid"),
    # This ULID is not known as a session
    test.case(
        "unknown_ulid", start_id="01JHXE0952TSJCFJZ869AW6HMD", given_id="mock-ulid"
    ),
    test.case("not_a_ulid", start_id="not-a-ulid", given_id="not-a-ulid"),
)
async def conversation_id(
    start_id: str | None,
    given_id: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test conversation ID generation."""
    # Patched inline rather than via a module-level @fixture, because
    # Tryke module-level fixtures auto-run for every test in the file
    # and would taint tests below that rely on the real ulid_now.
    with (
        patch("homeassistant.helpers.chat_session.ulid_now", return_value="mock-ulid"),
        chat_session.async_get_chat_session(hass, start_id) as session,
    ):
        expect(session.conversation_id).to_equal(given_id)


@test
async def context_var(hass: HomeAssistant = Depends(hass)) -> None:
    """Test context var."""
    with chat_session.async_get_chat_session(hass) as session:
        with chat_session.async_get_chat_session(
            hass, session.conversation_id
        ) as session2:
            expect(session is session2).to_be(True)

        with chat_session.async_get_chat_session(hass, None) as session2:
            expect(session.conversation_id != session2.conversation_id).to_be(True)

        with chat_session.async_get_chat_session(hass, "something else") as session2:
            expect(session.conversation_id != session2.conversation_id).to_be(True)

        with chat_session.async_get_chat_session(
            hass, ulid_util.ulid_now()
        ) as session2:
            expect(session.conversation_id != session2.conversation_id).to_be(True)


@test
async def cleanup(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test cleanup of the chat session."""
    with chat_session.async_get_chat_session(hass) as session:
        conversation_id = session.conversation_id

    # Reuse conversation ID to ensure we can chat with same session
    with chat_session.async_get_chat_session(hass, conversation_id) as session:
        expect(session.conversation_id).to_equal(conversation_id)

    # Set the last updated to be older than the timeout
    hass.data[chat_session.DATA_CHAT_SESSION][conversation_id].last_updated = (
        dt_util.utcnow() + chat_session.CONVERSATION_TIMEOUT
    )

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + chat_session.CONVERSATION_TIMEOUT + timedelta(seconds=1),
    )

    # Should not be cleaned up, but it should have scheduled another cleanup
    with chat_session.async_get_chat_session(hass, conversation_id) as session:
        expect(session.conversation_id).to_equal(conversation_id)

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + chat_session.CONVERSATION_TIMEOUT * 2 + timedelta(seconds=1),
    )

    # It should be cleaned up now and we start a new conversation
    with chat_session.async_get_chat_session(hass, conversation_id) as session:
        expect(session.conversation_id != conversation_id).to_be(True)
