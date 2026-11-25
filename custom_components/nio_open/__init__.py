"""The NIO Open Platform integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
    OAuth2Session,
    async_get_config_entry_implementation,
)

from .api import NioApi
from .const import CONF_VIN, PLATFORMS
from .coordinator import NioCoordinator, data_store

type NioConfigEntry = ConfigEntry[NioCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: NioConfigEntry) -> bool:
    """Set up NIO Open Platform from a config entry."""
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady("OAuth implementation unavailable") from err

    api = NioApi(OAuth2Session(hass, entry, implementation), entry.data[CONF_VIN])
    coordinator = NioCoordinator(hass, entry, api)
    await coordinator.async_restore()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NioConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: NioConfigEntry) -> None:
    """Delete the saved vehicle data."""
    await data_store(hass, entry).async_remove()
