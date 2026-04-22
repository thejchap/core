"""Tests for the auth models."""

from tryke import expect, test

from homeassistant.auth import models, permissions


@test
def owner_fetching_owner_permissions() -> None:
    """Test we fetch the owner permissions for an owner user."""
    group = models.Group(name="Test Group", policy={})
    owner = models.User(
        name="Test User", perm_lookup=None, groups=[group], is_owner=True
    )
    expect(owner.permissions is permissions.OwnerPermissions).to_be(True)


@test
def permissions_merged() -> None:
    """Test we merge the groups permissions."""
    group = models.Group(
        name="Test Group", policy={"entities": {"domains": {"switch": True}}}
    )
    group2 = models.Group(
        name="Test Group",
        policy={"entities": {"entity_ids": {"light.kitchen": True}}},
    )
    user = models.User(name="Test User", perm_lookup=None, groups=[group, group2])
    # Make sure we cache instance
    expect(user.permissions is user.permissions).to_be(True)

    expect(user.permissions.check_entity("switch.bla", "read")).to_be(True)
    expect(user.permissions.check_entity("light.kitchen", "read")).to_be(True)
    expect(user.permissions.check_entity("light.not_kitchen", "read")).to_be(False)


@test
def cache_cleared_on_group_change() -> None:
    """Test we clear the cache when a group changes."""
    group = models.Group(
        name="Test Group", policy={"entities": {"domains": {"switch": True}}}
    )
    admin_group = models.Group(
        name="Admin group", id=models.GROUP_ID_ADMIN, policy={"entities": {}}
    )
    user = models.User(
        name="Test User", perm_lookup=None, groups=[group], is_active=True
    )
    # Make sure we cache instance
    expect(user.permissions is user.permissions).to_be(True)

    # Make sure we cache is_admin
    expect(user.is_admin is user.is_admin).to_be(True)
    expect(user.is_active).to_be(True)

    user.groups = []
    expect(user.groups).to_equal([])
    expect(user.is_admin).to_be(False)

    user.is_owner = True
    expect(user.is_admin).to_be(True)
    user.is_owner = False

    expect(user.is_admin).to_be(False)
    user.groups = [admin_group]
    expect(user.is_admin).to_be(True)

    user.is_active = False
    expect(user.is_admin).to_be(False)
