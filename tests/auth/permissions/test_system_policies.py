"""Test system policies."""

from tryke import expect, test

from homeassistant.auth.permissions import (
    POLICY_SCHEMA,
    PolicyPermissions,
    system_policies,
)


@test
def admin_policy() -> None:
    """Test admin policy works."""
    POLICY_SCHEMA(system_policies.ADMIN_POLICY)

    perms = PolicyPermissions(system_policies.ADMIN_POLICY, None)
    expect(perms.check_entity("light.kitchen", "read")).to_be(True)
    expect(perms.check_entity("light.kitchen", "control")).to_be(True)
    expect(perms.check_entity("light.kitchen", "edit")).to_be(True)


@test
def user_policy() -> None:
    """Test user policy works."""
    POLICY_SCHEMA(system_policies.USER_POLICY)

    perms = PolicyPermissions(system_policies.USER_POLICY, None)
    expect(perms.check_entity("light.kitchen", "read")).to_be(True)
    expect(perms.check_entity("light.kitchen", "control")).to_be(True)
    expect(perms.check_entity("light.kitchen", "edit")).to_be(True)


@test
def read_only_policy() -> None:
    """Test read only policy works."""
    POLICY_SCHEMA(system_policies.READ_ONLY_POLICY)

    perms = PolicyPermissions(system_policies.READ_ONLY_POLICY, None)
    expect(perms.check_entity("light.kitchen", "read")).to_be(True)
    expect(perms.check_entity("light.kitchen", "control")).to_be(False)
    expect(perms.check_entity("light.kitchen", "edit")).to_be(False)
