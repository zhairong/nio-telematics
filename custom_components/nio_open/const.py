"""Constants for the NIO Open Platform integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final

DOMAIN: Final = "nio_open"
PLATFORMS: Final = ["sensor", "binary_sensor", "device_tracker"]

OAUTH_BASE_URL: Final = "https://open-eu.nio.com"
AUTHORIZE_URL: Final = f"{OAUTH_BASE_URL}/oauth2/authorize"
TOKEN_URL: Final = f"{OAUTH_BASE_URL}/api/2/oauth/token"
API_BASE_URL: Final = "https://open-api-eu.nio.com/api/1/telematics"

CONF_VIN: Final = "vin"

# vehicle:connectivity:read and aftersales:read make NIO reject the whole
# authorization with invalid_scope, so they are intentionally not requested.
OAUTH_SCOPES: Final = (
    "vehicle:read",
    "vehicle:dynamics:read",
    "vehicle:location:read",
    "vehicle:energy:read",
    "vehicle:body:read",
    "vehicle:cabin:read",
    "vehicle:powertrain:read",
    "vehicle:diagnostics:read",
)

SCAN_INTERVAL: Final = timedelta(seconds=60)
SLOW_EVERY_N_CYCLES: Final = 5


@dataclass(frozen=True)
class Endpoint:
    """A telematics endpoint under /vehicles/{vin}/."""

    path: str
    slow: bool = False


# `*/changes` endpoints return sparse change records for the last 10 minutes
# when no window is given; vehicle_status/latest returns one full snapshot.
ENDPOINTS: Final[dict[str, Endpoint]] = {
    "vehicle_status": Endpoint("vehicle_status/latest"),
    "soc_status": Endpoint("soc_status/changes"),
    "position_status": Endpoint("position_status/changes"),
    "door_status": Endpoint("door_status/changes"),
    "window_status": Endpoint("window_status/changes", slow=True),
    "light_status": Endpoint("light_status/changes", slow=True),
    "hvac_status": Endpoint("hvac_status/changes", slow=True),
    "heating_status": Endpoint("heating_status/changes", slow=True),
    "fridge_status": Endpoint("fridge_status/changes", slow=True),
    "extremum_data": Endpoint("extremum_data/changes", slow=True),
    "driving_motor": Endpoint("driving_motor/changes", slow=True),
    "driving_data": Endpoint("driving_data/changes", slow=True),
    "trip_status": Endpoint("trip_status/changes", slow=True),
    "alarm_signal": Endpoint("alarm_signal/changes", slow=True),
}

# NIO sends 0 for these temperatures when the vehicle has not sampled them, so
# a 0 is treated as missing and the last real reading is kept.
PLACEHOLDER_ZERO_FIELDS: Final[dict[str, frozenset[str]]] = {
    "hvac_status": frozenset({"amb_temp_c", "outside_temp_c"}),
    "fridge_status": frozenset({"fridge_set_temp"}),
}
