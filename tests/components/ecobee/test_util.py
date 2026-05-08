"""Tests for the ecobee.util module."""

import voluptuous as vol
from tryke import expect, test

from homeassistant.components.ecobee.util import ecobee_date, ecobee_time


@test
def ecobee_date_with_valid_input() -> None:
    """Test that the date function returns the expected result."""
    test_input = "2019-09-27"
    expect(ecobee_date(test_input)).to_equal(test_input)


@test
def ecobee_date_with_invalid_input() -> None:
    """Test that the date function raises the expected exception."""
    test_input = "20190927"
    expect(lambda: ecobee_date(test_input)).to_raise(vol.Invalid)


@test
def ecobee_time_with_valid_input() -> None:
    """Test that the time function returns the expected result."""
    test_input = "20:55:15"
    expect(ecobee_time(test_input)).to_equal(test_input)


@test
def ecobee_time_with_invalid_input() -> None:
    """Test that the time function raises the expected exception."""
    test_input = "20:55"
    expect(lambda: ecobee_time(test_input)).to_raise(vol.Invalid)
