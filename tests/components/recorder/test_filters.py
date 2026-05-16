"""The tests for recorder filters."""

from tryke import expect, test

from homeassistant.components.recorder.filters import (
    Filters,
    extract_include_exclude_filter_conf,
    merge_include_exclude_filters,
)
from homeassistant.const import CONF_DOMAINS, CONF_ENTITIES, CONF_EXCLUDE, CONF_INCLUDE
from homeassistant.helpers.entityfilter import CONF_ENTITY_GLOBS

EMPTY_INCLUDE_FILTER = {
    CONF_INCLUDE: {
        CONF_DOMAINS: None,
        CONF_ENTITIES: None,
        CONF_ENTITY_GLOBS: None,
    }
}
SIMPLE_INCLUDE_FILTER = {
    CONF_INCLUDE: {
        CONF_DOMAINS: ["homeassistant"],
        CONF_ENTITIES: ["sensor.one"],
        CONF_ENTITY_GLOBS: ["climate.*"],
    }
}
SIMPLE_INCLUDE_FILTER_DIFFERENT_ENTITIES = {
    CONF_INCLUDE: {
        CONF_DOMAINS: ["other"],
        CONF_ENTITIES: ["not_sensor.one"],
        CONF_ENTITY_GLOBS: ["not_climate.*"],
    }
}
SIMPLE_EXCLUDE_FILTER = {
    CONF_EXCLUDE: {
        CONF_DOMAINS: ["homeassistant"],
        CONF_ENTITIES: ["sensor.one"],
        CONF_ENTITY_GLOBS: ["climate.*"],
    }
}
SIMPLE_INCLUDE_EXCLUDE_FILTER = {**SIMPLE_INCLUDE_FILTER, **SIMPLE_EXCLUDE_FILTER}


@test
def extract_include_exclude_filter_conf_test() -> None:
    """Test we can extract a filter from configuration without altering it."""
    include_filter = extract_include_exclude_filter_conf(SIMPLE_INCLUDE_FILTER)
    expect(include_filter).to_equal(
        {
            CONF_EXCLUDE: {
                CONF_DOMAINS: set(),
                CONF_ENTITIES: set(),
                CONF_ENTITY_GLOBS: set(),
            },
            CONF_INCLUDE: {
                CONF_DOMAINS: {"homeassistant"},
                CONF_ENTITIES: {"sensor.one"},
                CONF_ENTITY_GLOBS: {"climate.*"},
            },
        }
    )

    exclude_filter = extract_include_exclude_filter_conf(SIMPLE_EXCLUDE_FILTER)
    expect(exclude_filter).to_equal(
        {
            CONF_INCLUDE: {
                CONF_DOMAINS: set(),
                CONF_ENTITIES: set(),
                CONF_ENTITY_GLOBS: set(),
            },
            CONF_EXCLUDE: {
                CONF_DOMAINS: {"homeassistant"},
                CONF_ENTITIES: {"sensor.one"},
                CONF_ENTITY_GLOBS: {"climate.*"},
            },
        }
    )

    include_exclude_filter = extract_include_exclude_filter_conf(
        SIMPLE_INCLUDE_EXCLUDE_FILTER
    )
    expect(include_exclude_filter).to_equal(
        {
            CONF_INCLUDE: {
                CONF_DOMAINS: {"homeassistant"},
                CONF_ENTITIES: {"sensor.one"},
                CONF_ENTITY_GLOBS: {"climate.*"},
            },
            CONF_EXCLUDE: {
                CONF_DOMAINS: {"homeassistant"},
                CONF_ENTITIES: {"sensor.one"},
                CONF_ENTITY_GLOBS: {"climate.*"},
            },
        }
    )

    include_exclude_filter[CONF_EXCLUDE][CONF_ENTITIES] = {"cover.altered"}
    # verify it really is a copy
    expect(SIMPLE_INCLUDE_EXCLUDE_FILTER[CONF_EXCLUDE][CONF_ENTITIES] != {"cover.altered"}).to_be(True)
    empty_include_filter = extract_include_exclude_filter_conf(EMPTY_INCLUDE_FILTER)
    expect(empty_include_filter).to_equal(
        {
            CONF_EXCLUDE: {
                CONF_DOMAINS: set(),
                CONF_ENTITIES: set(),
                CONF_ENTITY_GLOBS: set(),
            },
            CONF_INCLUDE: {
                CONF_DOMAINS: set(),
                CONF_ENTITIES: set(),
                CONF_ENTITY_GLOBS: set(),
            },
        }
    )


@test
def merge_include_exclude_filters_test() -> None:
    """Test we can merge two filters together."""
    include_exclude_filter_base = extract_include_exclude_filter_conf(
        SIMPLE_INCLUDE_EXCLUDE_FILTER
    )
    include_filter_add = extract_include_exclude_filter_conf(
        SIMPLE_INCLUDE_FILTER_DIFFERENT_ENTITIES
    )
    merged_filter = merge_include_exclude_filters(
        include_exclude_filter_base, include_filter_add
    )
    expect(merged_filter).to_equal(
        {
            CONF_EXCLUDE: {
                CONF_DOMAINS: {"homeassistant"},
                CONF_ENTITIES: {"sensor.one"},
                CONF_ENTITY_GLOBS: {"climate.*"},
            },
            CONF_INCLUDE: {
                CONF_DOMAINS: {"other", "homeassistant"},
                CONF_ENTITIES: {"not_sensor.one", "sensor.one"},
                CONF_ENTITY_GLOBS: {"climate.*", "not_climate.*"},
            },
        }
    )


@test
async def an_empty_filter_raises() -> None:
    """Test empty filter raises when not guarding with has_config."""
    filters = Filters()
    expect(not filters.has_config).to_be(True)
    expect(lambda: filters.states_metadata_entity_filter()).to_raise(
        RuntimeError,
        match="No filter configuration provided, check has_config before calling this method",
    )
    expect(lambda: filters.states_entity_filter()).to_raise(
        RuntimeError,
        match="No filter configuration provided, check has_config before calling this method",
    )
    expect(lambda: filters.events_entity_filter()).to_raise(
        RuntimeError,
        match="No filter configuration provided, check has_config before calling this method",
    )
