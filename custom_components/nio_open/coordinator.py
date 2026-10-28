"""Data coordinator for the NIO Open Platform."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NioApi, NioAuthError
from .const import DOMAIN, ENDPOINTS, SCAN_INTERVAL, SLOW_EVERY_N_CYCLES

_LOGGER = logging.getLogger(__name__)


class NioCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Poll NIO endpoints; fast ones every cycle, slow ones every Nth cycle."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: NioApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self._cycle = 0

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        names = [
            name
            for name, endpoint in ENDPOINTS.items()
            if not endpoint.slow or self._cycle % SLOW_EVERY_N_CYCLES == 0
        ]
        self._cycle += 1
        results = await asyncio.gather(
            *(self.api.fetch(name) for name in names), return_exceptions=True
        )

        data = dict(self.data or {})
        failures = 0
        for name, result in zip(names, results, strict=True):
            if isinstance(result, NioAuthError):
                raise ConfigEntryAuthFailed("NIO authentication failed") from None
            if isinstance(result, BaseException):
                if not isinstance(result, Exception):
                    raise result
                failures += 1
                _LOGGER.debug("Fetching %s failed", name)
            elif result:
                # Change records are sparse, so keep fields the new record lacks.
                data[name] = {**data.get(name, {}), **result}
        if failures == len(names):
            raise UpdateFailed("All NIO requests failed")
        return data
