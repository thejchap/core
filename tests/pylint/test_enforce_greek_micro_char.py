"""Tests for pylint hass_enforce_greek_micro_char plugin."""

from __future__ import annotations

import astroid
from pylint.checkers import BaseChecker
from pylint.testutils.unittest_linter import UnittestLinter
from pylint.utils.ast_walker import ASTWalker
from tryke import Depends, expect, fixture, test

from . import assert_no_messages
from .fixtures import enforce_greek_micro_char_checker, linter


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "good_const_with_annotation",
        code="""
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER: Final = "μg/m³"
        """,
    ),
    test.case(
        "good_unicode_const_with_annotation",
        code="""
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER: Final = "\u03bcg/m³"
        """,
    ),
    test.case(
        "good_const_without_annotation",
        code="""
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER = "μg/m³"
        """,
    ),
    test.case(
        "good_str_enum",
        code="""
            class UnitOfElectricPotential(StrEnum):
                \"\"\"Electric potential units.\"\"\"

                MICROVOLT = "μV"
                MILLIVOLT = "mV"
                VOLT = "V"
                KILOVOLT = "kV"
                MEGAVOLT = "MV"
        """,
    ),
    test.case(
        "good_sensor_description",
        code="""
            SENSOR_DESCRIPTION = {
                "radiation_rate": AranetSensorEntityDescription(
                    key="radiation_rate",
                    translation_key="radiation_rate",
                    name="Radiation Dose Rate",
                    native_unit_of_measurement="μSv/h",
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=2,
                    scale=0.001,
                ),
            }
            OTHER_DICT = {
                "value_with_bad_mu_should_pass": "µ"
            }
        """,
    ),
)
def enforce_greek_micro_char(
    code: str,
    linter: UnittestLinter = Depends(linter),
    enforce_greek_micro_char_checker: BaseChecker = Depends(
        enforce_greek_micro_char_checker
    ),
) -> None:
    """Good test cases."""
    root_node = astroid.parse(code, "homeassistant.components.pylint_test")
    walker = ASTWalker(linter)
    walker.add_checker(enforce_greek_micro_char_checker)

    with assert_no_messages(linter):
        walker.walk(root_node)


@test.cases(
    test.case(
        "bad_const_with_annotation",
        code="""
            CONCENTRATION_MICROGRAMS_PER_CUBIC_METER: Final = "µg/m³"
        """,
    ),
    test.case(
        "bad_unicode_const_with_annotation",
        code="""
            CONCENTRATION_MICROGRAMS_PER_CUBIC_METER: Final = "\u00b5g/m³"
        """,
    ),
    test.case(
        "bad_const_without_annotation",
        code="""
            CONCENTRATION_MICROGRAMS_PER_CUBIC_METER = "µg/m³"
        """,
    ),
    test.case(
        "bad_str_enum",
        code="""
            class UnitOfElectricPotential(StrEnum):
                \"\"\"Electric potential units.\"\"\"

                MICROVOLT = "µV"
                MILLIVOLT = "mV"
                VOLT = "V"
                KILOVOLT = "kV"
                MEGAVOLT = "MV"
        """,
    ),
    test.case(
        "bad_sensor_description",
        code="""
            SENSOR_DESCRIPTION = {
                "radiation_rate": AranetSensorEntityDescription(
                    key="radiation_rate",
                    translation_key="radiation_rate",
                    name="Radiation Dose Rate",
                    native_unit_of_measurement="µSv/h",
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=2,
                    scale=0.001,
                ),
            }
        """,
    ),
)
def enforce_greek_micro_char_assign_bad(
    code: str,
    linter: UnittestLinter = Depends(linter),
    enforce_greek_micro_char_checker: BaseChecker = Depends(
        enforce_greek_micro_char_checker
    ),
) -> None:
    """Bad assignment test cases."""
    root_node = astroid.parse(code, "homeassistant.components.pylint_test")
    walker = ASTWalker(linter)
    walker.add_checker(enforce_greek_micro_char_checker)

    walker.walk(root_node)
    messages = linter.release_messages()
    expect(len(messages)).to_equal(1).fatal()
    message = next(iter(messages))
    expect(message.msg_id).to_equal("hass-enforce-greek-micro-char")
