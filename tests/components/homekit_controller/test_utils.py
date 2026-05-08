"""Checks for basic helper utils."""

from tryke import expect, test

from homeassistant.components.homekit_controller.utils import unique_id_to_iids


@test
def unique_id_to_iids_test() -> None:
    """Check that unique_id_to_iids is safe against different invalid ids."""
    expect(unique_id_to_iids("pairingid_1_2_3")).to_equal((1, 2, 3))
    expect(unique_id_to_iids("pairingid_1_2")).to_equal((1, 2, None))
    expect(unique_id_to_iids("pairingid_1")).to_equal((1, None, None))

    expect(unique_id_to_iids("pairingid")).to_be(None)
    expect(unique_id_to_iids("pairingid_1_2_3_4")).to_be(None)
    expect(unique_id_to_iids("pairingid_a")).to_be(None)
    expect(unique_id_to_iids("pairingid_1_a")).to_be(None)
    expect(unique_id_to_iids("pairingid_1_2_a")).to_be(None)
