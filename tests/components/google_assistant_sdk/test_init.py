"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_success() -> None:
    """Stub for test_setup_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_success() -> None:
    """Stub for test_expired_token_refresh_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def expired_token_refresh_failure() -> None:
    """Stub for test_expired_token_refresh_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_client_error() -> None:
    """Stub for test_setup_client_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_text_command() -> None:
    """Stub for test_send_text_command."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_text_commands() -> None:
    """Stub for test_send_text_commands."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_text_command_expired_token_refresh_failure() -> None:
    """Stub for test_send_text_command_expired_token_refresh_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_text_command_grpc_error() -> None:
    """Stub for test_send_text_command_grpc_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_text_command_media_player() -> None:
    """Stub for test_send_text_command_media_player."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def conversation_agent() -> None:
    """Stub for test_conversation_agent."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def conversation_agent_refresh_token() -> None:
    """Stub for test_conversation_agent_refresh_token."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def conversation_agent_language_changed() -> None:
    """Stub for test_conversation_agent_language_changed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""

