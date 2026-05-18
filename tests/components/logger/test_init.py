"""The tests for the Logger component."""

from collections import defaultdict
import datetime
import logging
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import logger
from homeassistant.components.logger import LOGSEVERITY
from homeassistant.components.logger.helpers import SAVE_DELAY_LONG
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import Unauthorized
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import MockUser, async_call_logger_set_level, async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    hass as hass_fx,
    hass_read_only_user as hass_read_only_user_fx,
    hass_storage as hass_storage_fx,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def restore_logging_class():
    """Restore logging class (autouse equivalent)."""
    klass = logging.getLoggerClass()
    yield
    logging.setLoggerClass(klass)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _restore: None = Depends(restore_logging_class),
) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0

HASS_NS = "unused.homeassistant"
COMPONENTS_NS = f"{HASS_NS}.components"
ZONE_NS = f"{COMPONENTS_NS}.zone"
GROUP_NS = f"{COMPONENTS_NS}.group"
CONFIGED_NS = "otherlibx"
UNCONFIG_NS = "unconfigurednamespace"
INTEGRATION = "test_component"
INTEGRATION_NS = f"homeassistant.components.{INTEGRATION}"


@test
async def log_filtering(
    hass: HomeAssistant = Depends(hass_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test logging filters."""

    expect(
        await async_setup_component(
            hass,
            "logger",
            {
                "logger": {
                    "default": "warning",
                    "logs": {
                        "test.filter": "info",
                    },
                    "filters": {
                        "test.filter": [
                            "doesntmatchanything",
                            ".*shouldfilterall.*",
                            "^filterthis:.*",
                            "in the middle",
                        ],
                        "test.other_filter": [".*otherfilterer"],
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    filter_logger = logging.getLogger("test.filter")

    def msg_test(logger, result, message, *args):
        logger.error(message, *args)
        formatted_message = message % args
        expect((formatted_message in caplog.text)).to_be(result)
        caplog.clear()

    msg_test(
        filter_logger, False, "this line containing shouldfilterall should be filtered"
    )
    msg_test(filter_logger, True, "this line should not be filtered filterthis:")
    msg_test(filter_logger, False, "this in the middle should be filtered")
    msg_test(filter_logger, False, "filterthis: should be filtered")
    msg_test(filter_logger, False, "format string shouldfilter%s", "all")
    msg_test(filter_logger, True, "format string shouldfilter%s", "not")

    # Filtering should work even if log level is modified
    async with async_call_logger_set_level(
        "test.filter", "WARNING", hass=hass, caplog=caplog
    ):
        expect(filter_logger.getEffectiveLevel()).to_equal(logging.WARNING)
        msg_test(
            filter_logger,
            False,
            "this line containing shouldfilterall should still be filtered",
        )

        # Filtering should be scoped to a service
        msg_test(
            filter_logger,
            True,
            "this line containing otherfilterer should not be filtered",
        )
        msg_test(
            logging.getLogger("test.other_filter"),
            False,
            "this line containing otherfilterer SHOULD be filtered",
        )


@test
async def setting_level(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test we set log levels."""
    mocks = defaultdict(Mock)

    with patch("logging.getLogger", mocks.__getitem__):
        expect(
            await async_setup_component(
                hass,
                "logger",
                {
                    "logger": {
                        "default": "warning",
                        "logs": {
                            "test": "info",
                            "test.child": "debug",
                            "test.child.child": "warning",
                        },
                    }
                },
            )
        ).to_be(True)
        await hass.async_block_till_done()

    expect(len(mocks)).to_equal(5)

    expect(len(mocks[""].orig_setLevel.mock_calls)).to_equal(1)
    expect(mocks[""].orig_setLevel.mock_calls[0][1][0]).to_equal(LOGSEVERITY["WARNING"])

    expect(len(mocks["test"].orig_setLevel.mock_calls)).to_equal(1)
    expect(mocks["test"].orig_setLevel.mock_calls[0][1][0]).to_equal(
        LOGSEVERITY["INFO"]
    )

    expect(len(mocks["test.child"].orig_setLevel.mock_calls)).to_equal(1)
    expect(mocks["test.child"].orig_setLevel.mock_calls[0][1][0]).to_equal(
        LOGSEVERITY["DEBUG"]
    )

    expect(len(mocks["test.child.child"].orig_setLevel.mock_calls)).to_equal(1)
    expect(mocks["test.child.child"].orig_setLevel.mock_calls[0][1][0]).to_equal(
        LOGSEVERITY["WARNING"]
    )

    expect(
        len(mocks["homeassistant.components.logger"].orig_setLevel.mock_calls)
    ).to_equal(0)

    # Test set default level
    with patch("logging.getLogger", mocks.__getitem__):
        await hass.services.async_call(
            "logger", "set_default_level", {"level": "fatal"}, blocking=True
        )
    expect(len(mocks[""].orig_setLevel.mock_calls)).to_equal(2)
    expect(mocks[""].orig_setLevel.mock_calls[1][1][0]).to_equal(LOGSEVERITY["FATAL"])

    # Test update other loggers
    with patch("logging.getLogger", mocks.__getitem__):
        await hass.services.async_call(
            "logger",
            "set_level",
            {"test.child": "info", "new_logger": "notset"},
            blocking=True,
        )
    expect(len(mocks)).to_equal(6)

    expect(len(mocks["test.child"].orig_setLevel.mock_calls)).to_equal(2)
    expect(mocks["test.child"].orig_setLevel.mock_calls[1][1][0]).to_equal(
        LOGSEVERITY["INFO"]
    )

    expect(len(mocks["new_logger"].orig_setLevel.mock_calls)).to_equal(1)
    expect(mocks["new_logger"].orig_setLevel.mock_calls[0][1][0]).to_equal(
        LOGSEVERITY["NOTSET"]
    )


@test
async def can_set_level_from_yaml(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Test logger propagation."""

    expect(
        await async_setup_component(
            hass,
            "logger",
            {
                "logger": {
                    "logs": {
                        CONFIGED_NS: "warning",
                        f"{CONFIGED_NS}.info": "info",
                        f"{CONFIGED_NS}.debug": "debug",
                        HASS_NS: "warning",
                        COMPONENTS_NS: "info",
                        ZONE_NS: "debug",
                        GROUP_NS: "info",
                    },
                }
            },
        )
    ).to_be(True)
    await _assert_log_levels(hass)
    _reset_logging()


@test
async def can_set_level_from_store(
    hass: HomeAssistant = Depends(hass_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test setting up logs from store."""
    hass_storage["core.logger"] = {
        "data": {
            "logs": {
                CONFIGED_NS: {
                    "level": "WARNING",
                    "persistence": "once",
                    "type": "module",
                },
                f"{CONFIGED_NS}.info": {
                    "level": "INFO",
                    "persistence": "once",
                    "type": "module",
                },
                f"{CONFIGED_NS}.debug": {
                    "level": "DEBUG",
                    "persistence": "once",
                    "type": "module",
                },
                HASS_NS: {"level": "WARNING", "persistence": "once", "type": "module"},
                COMPONENTS_NS: {
                    "level": "INFO",
                    "persistence": "once",
                    "type": "module",
                },
                ZONE_NS: {"level": "DEBUG", "persistence": "once", "type": "module"},
                GROUP_NS: {"level": "INFO", "persistence": "once", "type": "module"},
            }
        },
        "key": "core.logger",
        "version": 1,
    }
    expect(await async_setup_component(hass, "logger", {})).to_be(True)
    await _assert_log_levels(hass)
    _reset_logging()


async def _assert_log_levels(hass: HomeAssistant) -> None:
    expect(logging.getLogger(UNCONFIG_NS).level).to_equal(logging.NOTSET)
    expect(logging.getLogger(UNCONFIG_NS).isEnabledFor(logging.CRITICAL)).to_be(True)
    expect(
        logging.getLogger(f"{UNCONFIG_NS}.any").isEnabledFor(logging.CRITICAL)
    ).to_be(True)
    expect(
        logging.getLogger(f"{UNCONFIG_NS}.any.any").isEnabledFor(logging.CRITICAL)
    ).to_be(True)

    expect(logging.getLogger(CONFIGED_NS).isEnabledFor(logging.DEBUG)).to_be(False)
    expect(logging.getLogger(CONFIGED_NS).isEnabledFor(logging.WARNING)).to_be(True)
    expect(
        logging.getLogger(f"{CONFIGED_NS}.any").isEnabledFor(logging.WARNING)
    ).to_be(True)
    expect(
        logging.getLogger(f"{CONFIGED_NS}.any.any").isEnabledFor(logging.WARNING)
    ).to_be(True)
    expect(
        logging.getLogger(f"{CONFIGED_NS}.info").isEnabledFor(logging.DEBUG)
    ).to_be(False)
    expect(
        logging.getLogger(f"{CONFIGED_NS}.info").isEnabledFor(logging.INFO)
    ).to_be(True)
    expect(
        logging.getLogger(f"{CONFIGED_NS}.info.any").isEnabledFor(logging.DEBUG)
    ).to_be(False)
    expect(
        logging.getLogger(f"{CONFIGED_NS}.info.any").isEnabledFor(logging.INFO)
    ).to_be(True)
    expect(
        logging.getLogger(f"{CONFIGED_NS}.debug").isEnabledFor(logging.DEBUG)
    ).to_be(True)
    expect(
        logging.getLogger(f"{CONFIGED_NS}.debug.any").isEnabledFor(logging.DEBUG)
    ).to_be(True)

    expect(logging.getLogger(HASS_NS).isEnabledFor(logging.DEBUG)).to_be(False)
    expect(logging.getLogger(HASS_NS).isEnabledFor(logging.WARNING)).to_be(True)

    expect(logging.getLogger(COMPONENTS_NS).isEnabledFor(logging.DEBUG)).to_be(False)
    expect(logging.getLogger(COMPONENTS_NS).isEnabledFor(logging.WARNING)).to_be(True)
    expect(logging.getLogger(COMPONENTS_NS).isEnabledFor(logging.INFO)).to_be(True)

    expect(logging.getLogger(GROUP_NS).isEnabledFor(logging.DEBUG)).to_be(False)
    expect(logging.getLogger(GROUP_NS).isEnabledFor(logging.WARNING)).to_be(True)
    expect(logging.getLogger(GROUP_NS).isEnabledFor(logging.INFO)).to_be(True)

    expect(logging.getLogger(f"{GROUP_NS}.any").isEnabledFor(logging.DEBUG)).to_be(
        False
    )
    expect(logging.getLogger(f"{GROUP_NS}.any").isEnabledFor(logging.WARNING)).to_be(
        True
    )
    expect(logging.getLogger(f"{GROUP_NS}.any").isEnabledFor(logging.INFO)).to_be(True)

    expect(logging.getLogger(ZONE_NS).isEnabledFor(logging.DEBUG)).to_be(True)
    expect(logging.getLogger(f"{ZONE_NS}.any").isEnabledFor(logging.DEBUG)).to_be(True)

    await hass.services.async_call(
        logger.DOMAIN, "set_level", {f"{UNCONFIG_NS}.any": "debug"}, blocking=True
    )

    expect(logging.getLogger(UNCONFIG_NS).level).to_equal(logging.NOTSET)
    expect(logging.getLogger(f"{UNCONFIG_NS}.any").level).to_equal(logging.DEBUG)
    expect(logging.getLogger(UNCONFIG_NS).level).to_equal(logging.NOTSET)

    await hass.services.async_call(
        logger.DOMAIN, "set_default_level", {"level": "debug"}, blocking=True
    )

    expect(logging.getLogger(UNCONFIG_NS).isEnabledFor(logging.DEBUG)).to_be(True)
    expect(
        logging.getLogger(f"{UNCONFIG_NS}.any").isEnabledFor(logging.DEBUG)
    ).to_be(True)
    expect(
        logging.getLogger(f"{UNCONFIG_NS}.any.any").isEnabledFor(logging.DEBUG)
    ).to_be(True)
    expect(logging.getLogger("").isEnabledFor(logging.DEBUG)).to_be(True)

    expect(logging.getLogger(COMPONENTS_NS).isEnabledFor(logging.DEBUG)).to_be(False)
    expect(logging.getLogger(GROUP_NS).isEnabledFor(logging.DEBUG)).to_be(False)

    logging.getLogger(CONFIGED_NS).setLevel(logging.INFO)
    expect(logging.getLogger(CONFIGED_NS).level).to_equal(logging.WARNING)

    logging.getLogger("").setLevel(logging.NOTSET)


def _reset_logging():
    """Reset loggers."""
    logging.getLogger(CONFIGED_NS).orig_setLevel(logging.NOTSET)
    logging.getLogger(f"{CONFIGED_NS}.info").orig_setLevel(logging.NOTSET)
    logging.getLogger(f"{CONFIGED_NS}.debug").orig_setLevel(logging.NOTSET)
    logging.getLogger(HASS_NS).orig_setLevel(logging.NOTSET)
    logging.getLogger(COMPONENTS_NS).orig_setLevel(logging.NOTSET)
    logging.getLogger(ZONE_NS).orig_setLevel(logging.NOTSET)
    logging.getLogger(GROUP_NS).orig_setLevel(logging.NOTSET)
    logging.getLogger(INTEGRATION_NS).orig_setLevel(logging.NOTSET)


@test
async def can_set_integration_level_from_store(
    hass: HomeAssistant = Depends(hass_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test setting up integration logs from store."""
    hass_storage["core.logger"] = {
        "data": {
            "logs": {
                INTEGRATION: {
                    "level": "WARNING",
                    "persistence": "once",
                    "type": "integration",
                },
            }
        },
        "key": "core.logger",
        "version": 1,
    }
    expect(await async_setup_component(hass, "logger", {})).to_be(True)

    expect(logging.getLogger(INTEGRATION_NS).isEnabledFor(logging.DEBUG)).to_be(False)
    expect(logging.getLogger(INTEGRATION_NS).isEnabledFor(logging.WARNING)).to_be(True)

    _reset_logging()


@test
async def chattier_log_level_wins_1(
    hass: HomeAssistant = Depends(hass_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test chattier log level in store takes precedence."""
    hass_storage["core.logger"] = {
        "data": {
            "logs": {
                INTEGRATION_NS: {
                    "level": "DEBUG",
                    "persistence": "once",
                    "type": "module",
                },
            }
        },
        "key": "core.logger",
        "version": 1,
    }
    expect(
        await async_setup_component(
            hass,
            "logger",
            {
                "logger": {
                    "logs": {
                        INTEGRATION_NS: "warning",
                    }
                }
            },
        )
    ).to_be(True)

    expect(logging.getLogger(INTEGRATION_NS).isEnabledFor(logging.DEBUG)).to_be(True)
    expect(logging.getLogger(INTEGRATION_NS).isEnabledFor(logging.WARNING)).to_be(True)

    _reset_logging()


@test
async def chattier_log_level_wins_2(
    hass: HomeAssistant = Depends(hass_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test chattier log level in yaml takes precedence."""
    hass_storage["core.logger"] = {
        "data": {
            "logs": {
                INTEGRATION_NS: {
                    "level": "WARNING",
                    "persistence": "once",
                    "type": "module",
                },
            }
        },
        "key": "core.logger",
        "version": 1,
    }
    expect(
        await async_setup_component(
            hass, "logger", {"logger": {"logs": {INTEGRATION_NS: "debug"}}}
        )
    ).to_be(True)

    expect(logging.getLogger(INTEGRATION_NS).isEnabledFor(logging.DEBUG)).to_be(True)
    expect(logging.getLogger(INTEGRATION_NS).isEnabledFor(logging.WARNING)).to_be(True)

    _reset_logging()


@test
async def log_once_removed_from_store(
    hass: HomeAssistant = Depends(hass_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test logs with persistence "once" are removed from the store at startup."""
    store_contents = {
        "data": {
            "logs": {
                ZONE_NS: {"type": "module", "level": "DEBUG", "persistence": "once"}
            }
        },
        "key": "core.logger",
        "version": 1,
    }
    hass_storage["core.logger"] = store_contents

    expect(await async_setup_component(hass, "logger", {})).to_be(True)

    expect(hass_storage["core.logger"]["data"]).to_equal(store_contents["data"])

    async_fire_time_changed(
        hass, dt_util.utcnow() + datetime.timedelta(seconds=SAVE_DELAY_LONG)
    )
    await hass.async_block_till_done()

    expect(hass_storage["core.logger"]["data"]).to_equal({"logs": {}})


@test.cases(
    test.case("set_level", service="set_level"),
    test.case("set_default_level", service="set_default_level"),
)
async def services_require_admin(
    service: str,
    hass: HomeAssistant = Depends(hass_fx),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fx),
) -> None:
    """Test logger services require admin."""
    expect(await async_setup_component(hass, "logger", {})).to_be(True)

    async with expect_raises_async(Unauthorized):
        await hass.services.async_call(
            logger.DOMAIN,
            service,
            {"level": "debug"} if service == "set_default_level" else {"test": "debug"},
            context=Context(user_id=hass_read_only_user.id),
            blocking=True,
        )
