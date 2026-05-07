"""Tryke skip-stubs for bayesian config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_step_user() -> None:
    """Stub for test_config_flow_step_user (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def subentry_flow() -> None:
    """Stub for test_subentry_flow (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def single_state_observation() -> None:
    """Stub for test_single_state_observation (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def single_numeric_state_observation() -> None:
    """Stub for test_single_numeric_state_observation (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def multi_numeric_state_observation() -> None:
    """Stub for test_multi_numeric_state_observation (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def single_template_observation() -> None:
    """Stub for test_single_template_observation (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def basic_options() -> None:
    """Stub for test_basic_options (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def reconfiguring_observations() -> None:
    """Stub for test_reconfiguring_observations (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def invalid_configs() -> None:
    """Stub for test_invalid_configs (port deferred)."""
