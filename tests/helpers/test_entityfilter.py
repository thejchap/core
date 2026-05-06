"""The tests for the EntityFilter component."""

from tryke import expect, test

from homeassistant.helpers.entityfilter import (
    FILTER_SCHEMA,
    INCLUDE_EXCLUDE_FILTER_SCHEMA,
    EntityFilter,
    generate_filter,
)


@test
def no_filters_case_1() -> None:
    """If include and exclude not included, pass everything."""
    incl_dom: dict = {}
    incl_ent: dict = {}
    excl_dom: dict = {}
    excl_ent: dict = {}
    testfilter = generate_filter(incl_dom, incl_ent, excl_dom, excl_ent)

    for value in ("sensor.test", "sun.sun", "light.test"):
        expect(testfilter(value)).to_be(True)


@test
def includes_only_case_2() -> None:
    """If include specified, only pass if specified (Case 2)."""
    incl_dom = {"light", "sensor"}
    incl_ent = {"binary_sensor.working"}
    excl_dom: dict = {}
    excl_ent: dict = {}
    testfilter = generate_filter(incl_dom, incl_ent, excl_dom, excl_ent)

    expect(testfilter("sensor.test")).to_be(True)
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("binary_sensor.working")).to_be(True)
    expect(testfilter("binary_sensor.notworking")).to_be(False)
    expect(testfilter("sun.sun")).to_be(False)


@test
def includes_only_with_glob_case_2() -> None:
    """If include specified, only pass if specified (Case 2)."""
    incl_dom = {"light", "sensor"}
    incl_glob = {"cover.*_window"}
    incl_ent = {"binary_sensor.working"}
    excl_dom: dict = {}
    excl_glob: dict = {}
    excl_ent: dict = {}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    expect(testfilter("sensor.test")).to_be(True)
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("cover.bedroom_window")).to_be(True)
    expect(testfilter("binary_sensor.working")).to_be(True)
    expect(testfilter("binary_sensor.notworking")).to_be(False)
    expect(testfilter("sun.sun")).to_be(False)
    expect(testfilter("cover.garage_door")).to_be(False)


@test
def excludes_only_case_3() -> None:
    """If exclude specified, pass all but specified (Case 3)."""
    incl_dom: dict = {}
    incl_ent: dict = {}
    excl_dom = {"light", "sensor"}
    excl_ent = {"binary_sensor.working"}
    testfilter = generate_filter(incl_dom, incl_ent, excl_dom, excl_ent)

    expect(testfilter("sensor.test")).to_be(False)
    expect(testfilter("light.test")).to_be(False)
    expect(testfilter("binary_sensor.working")).to_be(False)
    expect(testfilter("binary_sensor.another")).to_be(True)
    expect(testfilter("sun.sun")).to_be(True)


@test
def excludes_only_with_glob_case_3() -> None:
    """If exclude specified, pass all but specified (Case 3)."""
    incl_dom: dict = {}
    incl_glob: dict = {}
    incl_ent: dict = {}
    excl_dom = {"light", "sensor"}
    excl_glob = {"cover.*_window"}
    excl_ent = {"binary_sensor.working"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    expect(testfilter("sensor.test")).to_be(False)
    expect(testfilter("light.test")).to_be(False)
    expect(testfilter("cover.bedroom_window")).to_be(False)
    expect(testfilter("binary_sensor.working")).to_be(False)
    expect(testfilter("binary_sensor.another")).to_be(True)
    expect(testfilter("sun.sun")).to_be(True)
    expect(testfilter("cover.garage_door")).to_be(True)


@test
def with_include_domain_case4() -> None:
    """Test case 4 - include and exclude specified, with included domain."""
    incl_dom = {"light", "sensor"}
    incl_ent = {"binary_sensor.working"}
    excl_dom: dict = {}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    testfilter = generate_filter(incl_dom, incl_ent, excl_dom, excl_ent)

    expect(testfilter("sensor.test")).to_be(True)
    expect(testfilter("sensor.notworking")).to_be(False)
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.working")).to_be(True)
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("sun.sun")).to_be(False)


@test
def with_include_domain_exclude_glob_case4() -> None:
    """Test case 4 - include and exclude specified, with included domain but excluded by glob."""
    incl_dom = {"light", "sensor"}
    incl_ent = {"binary_sensor.working"}
    incl_glob: dict = {}
    excl_dom: dict = {}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    excl_glob = {"sensor.busted"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    expect(testfilter("sensor.test")).to_be(True)
    expect(testfilter("sensor.busted")).to_be(False)
    expect(testfilter("sensor.notworking")).to_be(False)
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.working")).to_be(True)
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("sun.sun")).to_be(False)


@test
def with_include_glob_case4() -> None:
    """Test case 4 - include and exclude specified, with included glob."""
    incl_dom: dict = {}
    incl_glob = {"light.*", "sensor.*"}
    incl_ent = {"binary_sensor.working"}
    excl_dom: dict = {}
    excl_glob: dict = {}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    expect(testfilter("sensor.test")).to_be(True)
    expect(testfilter("sensor.notworking")).to_be(False)
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.working")).to_be(True)
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("sun.sun")).to_be(False)


@test
def with_include_domain_glob_filtering_case4() -> None:
    """Test case 4 - include and exclude specified, both have domains and globs."""
    incl_dom = {"light"}
    incl_glob = {"*working"}
    incl_ent: dict = {}
    excl_dom = {"binary_sensor"}
    excl_glob = {"*notworking"}
    excl_ent = {"light.ignoreme"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    expect(testfilter("sensor.working")).to_be(True)
    expect(testfilter("sensor.notworking")).to_be(True)  # include is stronger
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("light.notworking")).to_be(True)  # include is stronger
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.not_working")).to_be(True)  # include is stronger
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("sun.sun")).to_be(False)


@test
def with_include_domain_glob_filtering_case4a_include_strong() -> None:
    """Test case 4 - include and exclude specified, both have domains and globs, and a specifically included entity."""
    incl_dom = {"light"}
    incl_glob = {"*working"}
    incl_ent = {"binary_sensor.specificly_included"}
    excl_dom = {"binary_sensor"}
    excl_glob = {"*notworking"}
    excl_ent = {"light.ignoreme"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    expect(testfilter("sensor.working")).to_be(True)
    expect(testfilter("sensor.notworking")).to_be(True)  # include is stronger
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("light.notworking")).to_be(True)  # include is stronger
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.not_working")).to_be(True)  # include is stronger
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("binary_sensor.specificly_included")).to_be(True)
    expect(testfilter("sun.sun")).to_be(False)


@test
def with_include_glob_filtering_case4a_include_strong() -> None:
    """Test case 4 - include and exclude specified, both have globs, and a specifically included entity."""
    incl_dom: dict = {}
    incl_glob = {"*working"}
    incl_ent = {"binary_sensor.specificly_included"}
    excl_dom: dict = {}
    excl_glob = {"*broken", "*notworking", "binary_sensor.*"}
    excl_ent = {"light.ignoreme"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    expect(testfilter("sensor.working")).to_be(True)
    expect(testfilter("sensor.notworking")).to_be(True)  # include is stronger
    expect(testfilter("sensor.broken")).to_be(False)
    expect(testfilter("light.test")).to_be(False)
    expect(testfilter("light.notworking")).to_be(True)  # include is stronger
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.not_working")).to_be(True)  # include is stronger
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("binary_sensor.specificly_included")).to_be(True)
    expect(testfilter("sun.sun")).to_be(False)


@test
def exclude_domain_case5() -> None:
    """Test case 5 - include and exclude specified, with excluded domain."""
    incl_dom: dict = {}
    incl_ent = {"binary_sensor.working"}
    excl_dom = {"binary_sensor"}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    testfilter = generate_filter(incl_dom, incl_ent, excl_dom, excl_ent)

    expect(testfilter("sensor.test")).to_be(True)
    expect(testfilter("sensor.notworking")).to_be(False)
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.working")).to_be(True)
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("sun.sun")).to_be(True)


@test
def exclude_glob_case5() -> None:
    """Test case 5 - include and exclude specified, with excluded glob."""
    incl_dom: dict = {}
    incl_glob: dict = {}
    incl_ent = {"binary_sensor.working"}
    excl_dom: dict = {}
    excl_glob = {"binary_sensor.*"}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    expect(testfilter("sensor.test")).to_be(True)
    expect(testfilter("sensor.notworking")).to_be(False)
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.working")).to_be(True)
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("sun.sun")).to_be(True)


@test
def exclude_glob_case5_include_strong() -> None:
    """Test case 5 - include and exclude specified, with excluded glob, and a specifically included entity."""
    incl_dom: dict = {}
    incl_glob: dict = {}
    incl_ent = {"binary_sensor.working"}
    excl_dom = {"binary_sensor"}
    excl_glob = {"binary_sensor.*"}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    testfilter = generate_filter(
        incl_dom, incl_ent, excl_dom, excl_ent, incl_glob, excl_glob
    )

    expect(testfilter("sensor.test")).to_be(True)
    expect(testfilter("sensor.notworking")).to_be(False)
    expect(testfilter("light.test")).to_be(True)
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.working")).to_be(True)
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("sun.sun")).to_be(True)


@test
def no_domain_case6() -> None:
    """Test case 6 - include and exclude specified, with no domains."""
    incl_dom: dict = {}
    incl_ent = {"binary_sensor.working"}
    excl_dom: dict = {}
    excl_ent = {"light.ignoreme", "sensor.notworking"}
    testfilter = generate_filter(incl_dom, incl_ent, excl_dom, excl_ent)

    expect(testfilter("sensor.test")).to_be(False)
    expect(testfilter("sensor.notworking")).to_be(False)
    expect(testfilter("light.test")).to_be(False)
    expect(testfilter("light.ignoreme")).to_be(False)
    expect(testfilter("binary_sensor.working")).to_be(True)
    expect(testfilter("binary_sensor.another")).to_be(False)
    expect(testfilter("sun.sun")).to_be(False)


@test
def filter_schema_empty() -> None:
    """Test filter schema."""
    conf: dict = {}
    filt = FILTER_SCHEMA(conf)
    conf.update(
        {
            "include_domains": [],
            "include_entities": [],
            "exclude_domains": [],
            "exclude_entities": [],
            "include_entity_globs": [],
            "exclude_entity_globs": [],
        }
    )
    expect(filt.config).to_equal(conf)
    expect(filt.empty_filter).to_be(True)


@test
def filter_schema() -> None:
    """Test filter schema."""
    conf = {
        "include_domains": ["light"],
        "include_entities": ["switch.kitchen"],
        "exclude_domains": ["cover"],
        "exclude_entities": ["light.kitchen"],
    }
    filt = FILTER_SCHEMA(conf)
    conf.update({"include_entity_globs": [], "exclude_entity_globs": []})
    expect(filt.config).to_equal(conf)
    expect(filt.empty_filter).to_be(False)


@test
def filter_schema_with_globs() -> None:
    """Test filter schema with glob options."""
    conf = {
        "include_domains": ["light"],
        "include_entity_globs": ["sensor.kitchen_*"],
        "include_entities": ["switch.kitchen"],
        "exclude_domains": ["cover"],
        "exclude_entity_globs": ["sensor.weather_*"],
        "exclude_entities": ["light.kitchen"],
    }
    filt = FILTER_SCHEMA(conf)
    expect(filt.config).to_equal(conf)
    expect(filt.empty_filter).to_be(False)


@test
def filter_schema_include_exclude() -> None:
    """Test the include exclude filter schema."""
    conf = {
        "include": {
            "domains": ["light"],
            "entity_globs": ["sensor.kitchen_*"],
            "entities": ["switch.kitchen"],
        },
        "exclude": {
            "domains": ["cover"],
            "entity_globs": ["sensor.weather_*"],
            "entities": ["light.kitchen"],
        },
    }
    filt = INCLUDE_EXCLUDE_FILTER_SCHEMA(conf)
    expect(filt.config).to_equal(
        {
            "include_domains": ["light"],
            "include_entity_globs": ["sensor.kitchen_*"],
            "include_entities": ["switch.kitchen"],
            "exclude_domains": ["cover"],
            "exclude_entity_globs": ["sensor.weather_*"],
            "exclude_entities": ["light.kitchen"],
        }
    )
    expect(filt.empty_filter).to_be(False)


@test
def explicitly_included() -> None:
    """Test if an entity is explicitly included."""
    conf = {
        "include": {
            "domains": ["light"],
            "entity_globs": ["sensor.kitchen_*"],
            "entities": ["switch.kitchen"],
        },
        "exclude": {
            "domains": ["cover"],
            "entity_globs": ["sensor.weather_*"],
            "entities": ["light.kitchen"],
        },
    }
    filt: EntityFilter = INCLUDE_EXCLUDE_FILTER_SCHEMA(conf)
    expect(filt.explicitly_included("light.any")).to_be(False)
    expect(filt.explicitly_included("switch.other")).to_be(False)
    expect(filt.explicitly_included("sensor.kitchen_4")).to_be(True)
    expect(filt.explicitly_included("switch.kitchen")).to_be(True)

    expect(filt.explicitly_excluded("light.any")).to_be(False)
    expect(filt.explicitly_excluded("switch.other")).to_be(False)
    expect(filt.explicitly_excluded("sensor.weather_5")).to_be(True)
    expect(filt.explicitly_excluded("light.kitchen")).to_be(True)


@test
def get_filter() -> None:
    """Test we can get the underlying filter."""
    conf = {
        "include": {
            "domains": ["light"],
            "entity_globs": ["sensor.kitchen_*"],
            "entities": ["switch.kitchen"],
        },
        "exclude": {
            "domains": ["cover"],
            "entity_globs": ["sensor.weather_*"],
            "entities": ["light.kitchen"],
        },
    }
    filt: EntityFilter = INCLUDE_EXCLUDE_FILTER_SCHEMA(conf)
    underlying_filter = filt.get_filter()
    expect(underlying_filter("light.any")).to_be(True)
    expect(underlying_filter("switch.other")).to_be(False)
    expect(underlying_filter("sensor.kitchen_4")).to_be(True)
    expect(underlying_filter("switch.kitchen")).to_be(True)


@test
def complex_include_exclude_filter() -> None:
    """Test a complex include exclude filter."""
    conf = {
        "include": {
            "domains": ["switch", "person"],
            "entities": ["group.family"],
            "entity_globs": [
                "sensor.*_sensor_temperature",
                "sensor.*_actueel",
                "sensor.*_totaal",
                "sensor.calculated*",
                "sensor.solaredge_*",
                "sensor.speedtest*",
                "sensor.teller*",
                "sensor.zp*",
                "binary_sensor.*_sensor_motion",
                "binary_sensor.*_door",
                "sensor.water_*ly",
                "sensor.gas_*ly",
            ],
        },
        "exclude": {
            "domains": [
                "alarm_control_panel",
                "alert",
                "automation",
                "button",
                "camera",
                "climate",
                "counter",
                "cover",
                "geo_location",
                "group",
                "input_boolean",
                "input_datetime",
                "input_number",
                "input_select",
                "input_text",
                "light",
                "media_player",
                "number",
                "proximity",
                "remote",
                "scene",
                "script",
                "sun",
                "timer",
                "updater",
                "variable",
                "weather",
                "zone",
            ],
            "entities": [
                "sensor.solaredge_last_updatetime",
                "sensor.solaredge_last_changed",
            ],
            "entity_globs": ["switch.*_light_level", "switch.sonos_*"],
        },
    }
    filt: EntityFilter = INCLUDE_EXCLUDE_FILTER_SCHEMA(conf)
    expect(filt("switch.espresso_keuken")).to_be(True)
