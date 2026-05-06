"""Test the Tesla Fleet config flow."""

from tryke import test


@test.skip("requires aioclient_mock + hass_client fixtures")
async def partner_login_auth_error() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def partner_login_partial_failure() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def full_flow_with_domain_registration() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def domain_input_invalid_domain() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def domain_registration_errors() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def domain_registration_precondition_failed() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def domain_registration_public_key_not_found() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def domain_registration_public_key_mismatch() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def domain_registration_partial_failure() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def domain_registration_all_regions_fail() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def registration_complete_no_domain() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def registration_complete_with_domain_and_user_input() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def registration_complete_with_domain_no_user_input() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reauthentication() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reauth_account_mismatch() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def duplicate_unique_id_abort() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reauth_confirm_form() -> None:
    """Skipped pending fixture port."""
