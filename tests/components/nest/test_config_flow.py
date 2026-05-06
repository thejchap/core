"""Tryke skip-stubs for nest config flow tests.

Original tests use OAuth2 application credentials flow; full port deferred.
"""

from tryke import test

@test.skip("OAuth2 application credentials flow")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def config_flow_restart() -> None:
    """Stub for test_config_flow_restart (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def config_flow_wrong_project_id() -> None:
    """Stub for test_config_flow_wrong_project_id (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def config_flow_pubsub_create_subscription_failure() -> None:
    """Stub for test_config_flow_pubsub_create_subscription_failure (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def multiple_config_entries() -> None:
    """Stub for test_multiple_config_entries (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def duplicate_config_entries() -> None:
    """Stub for test_duplicate_config_entries (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def reauth_multiple_config_entries() -> None:
    """Stub for test_reauth_multiple_config_entries (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def pubsub_subscriber_config_entry_reauth() -> None:
    """Stub for test_pubsub_subscriber_config_entry_reauth (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def config_entry_title_from_home() -> None:
    """Stub for test_config_entry_title_from_home (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def config_entry_title_multiple_homes() -> None:
    """Stub for test_config_entry_title_multiple_homes (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def title_failure_fallback() -> None:
    """Stub for test_title_failure_fallback (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def structure_missing_trait() -> None:
    """Stub for test_structure_missing_trait (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def dhcp_discovery() -> None:
    """Stub for test_dhcp_discovery (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def dhcp_discovery_already_setup() -> None:
    """Stub for test_dhcp_discovery_already_setup (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def dhcp_discovery_with_creds() -> None:
    """Stub for test_dhcp_discovery_with_creds (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def token_error() -> None:
    """Stub for test_token_error (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def existing_topic_and_subscription() -> None:
    """Stub for test_existing_topic_and_subscription (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def no_eligible_topics() -> None:
    """Stub for test_no_eligible_topics (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def list_topics_failure() -> None:
    """Stub for test_list_topics_failure (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def create_topic_failed() -> None:
    """Stub for test_create_topic_failed (port deferred)."""

@test.skip("OAuth2 application credentials flow")
async def list_subscriptions_failure() -> None:
    """Stub for test_list_subscriptions_failure (port deferred)."""
