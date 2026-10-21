"""Tests for coordinator and entities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nio_open.api import NioApiError, NioAuthError
from custom_components.nio_open.const import DOMAIN, ENDPOINTS

VIN = "SQETEST000123456"

DATA = {
    "vehicle_status": {"speed": 0, "mileage": 12345.6, "vehl_state": "PARKED_VEHICLE"},
    "soc_status": {"soc": 76.5, "remaining_range": 310},
    "door_status": {
        "door_ajars": {"door_ajar_frnt_le_sts": "AJAR_OPENED", "door_ajar_frnt_ri_sts": "AJAR_CLOSED"},
        "door_locks": {"door_lock_frnt_le_sts": "LOCK_LOCKED"},
        "vehicle_lock_status": "FULLY_LOCKED",
        "charge_port_status": [{"charge_port_sn": 1, "ajar_status": "AJAR_CLOSED"}],
    },
    "position_status": {"posng_valid_type": "VALID", "latitude": 52.5, "longitude": 13.4},
    "window_status": {"window_positions": {"win_frnt_le_posn": 20}},
}


def make_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=VIN,
        data={"vin": VIN, "auth_implementation": DOMAIN, "token": {}},
    )


async def setup(hass: HomeAssistant, fetch) -> MockConfigEntry:
    entry = make_entry()
    entry.add_to_hass(hass)
    with (
        patch("custom_components.nio_open.async_get_config_entry_implementation"),
        patch("custom_components.nio_open.OAuth2Session", MagicMock()),
        patch("custom_components.nio_open.api.NioApi.fetch", side_effect=fetch),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def fetch_ok(name: str):
    return DATA.get(name)


async def test_entities(hass: HomeAssistant) -> None:
    entry = await setup(hass, fetch_ok)
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.nio_123456_battery").state == "76.5"
    assert hass.states.get("sensor.nio_123456_front_left_window_position").state == "20"
    assert hass.states.get("binary_sensor.nio_123456_front_left_door").state == "on"
    assert hass.states.get("binary_sensor.nio_123456_front_right_door").state == "off"
    assert hass.states.get("binary_sensor.nio_123456_vehicle_lock").state == "off"
    assert hass.states.get("binary_sensor.nio_123456_charge_port").state == "off"
    tracker = hass.states.get("device_tracker.nio_123456_location")
    assert tracker.attributes["latitude"] == 52.5


async def test_tracker_ignores_invalid_position(hass: HomeAssistant) -> None:
    async def fetch(name):
        if name == "position_status":
            return {"posng_valid_type": "INVALID", "latitude": 1.0, "longitude": 2.0}
        return DATA.get(name)

    await setup(hass, fetch)
    assert "latitude" not in hass.states.get("device_tracker.nio_123456_location").attributes


async def test_partial_failure_keeps_setup(hass: HomeAssistant) -> None:
    async def fetch(name):
        if name == "door_status":
            raise NioApiError("boom")
        return DATA.get(name)

    entry = await setup(hass, fetch)
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.nio_123456_battery").state == "76.5"
    assert hass.states.get("binary_sensor.nio_123456_front_left_door").state == "unavailable"


async def test_all_failures_retry_setup(hass: HomeAssistant) -> None:
    async def fetch(name):
        raise NioApiError("down")

    entry = await setup(hass, fetch)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_auth_failure_starts_reauth(hass: HomeAssistant) -> None:
    async def fetch(name):
        raise NioAuthError("denied")

    entry = await setup(hass, fetch)
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert any(hass.config_entries.flow.async_progress_by_handler(DOMAIN))


async def test_slow_endpoints_polled_every_nth_cycle(hass: HomeAssistant) -> None:
    calls: list[str] = []

    async def fetch(name):
        calls.append(name)
        return DATA.get(name)

    entry = await setup(hass, fetch)
    first = set(calls)
    assert first == set(ENDPOINTS)
    calls.clear()
    with patch("custom_components.nio_open.api.NioApi.fetch", side_effect=fetch):
        await entry.runtime_data.async_refresh()
    assert set(calls) == {n for n, e in ENDPOINTS.items() if not e.slow}
