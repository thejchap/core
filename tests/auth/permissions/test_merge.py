"""Tests for permissions merging."""

from tryke import expect, test

from homeassistant.auth.permissions.merge import merge_policies


@test
def merging_permissions_true_rules_dict() -> None:
    """Test merging policy with two entities."""
    policy1 = {
        "something_else": True,
        "entities": {"entity_ids": {"light.kitchen": True}},
    }
    policy2 = {"entities": {"entity_ids": True}}
    expect(merge_policies([policy1, policy2])).to_equal(
        {
            "something_else": True,
            "entities": {"entity_ids": True},
        }
    )


@test
def merging_permissions_multiple_subcategories() -> None:
    """Test merging policy with two entities."""
    policy1 = {"entities": None}
    policy2 = {"entities": {"entity_ids": True}}
    policy3 = {"entities": True}
    expect(merge_policies([policy1, policy2])).to_equal(policy2)
    expect(merge_policies([policy1, policy3])).to_equal(policy3)

    expect(merge_policies([policy2, policy3])).to_equal(policy3)
