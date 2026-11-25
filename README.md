# NIO Open Platform for Home Assistant

English | [中文](README.zh-CN.md)

Read-only Home Assistant integration that shows your NIO vehicle via the [NIO EU Open Platform](https://open-eu.nio.com/).

Repository: [zhairong/nio-telematics](https://github.com/zhairong/nio-telematics) (public, MIT licensed, HACS-ready).

## Entities
- **Sensors**: battery %, range, charging state, speed, odometer, temperatures, battery/cell data, window positions, seat heating/ventilation, fridge, trip, driving mode, …
- **Binary sensors**: doors, hood, tailgate, charge port, locks, lights, air conditioning.
- **Device tracker**: vehicle position (only while NIO reports a valid fix).

Many diagnostic entities are disabled by default; enable them in the entity registry.
Polling: every 60 s for core data (battery, vehicle status, position, doors); other endpoints every 5 minutes.
Entity names are translated into English, Simplified Chinese, and German, and follow each user's Home Assistant language setting automatically.

## Installation

### HACS (recommended)
HACS → ⋮ → **Custom repositories** → add `https://github.com/zhairong/nio-telematics`, category **Integration** → install → restart Home Assistant.
(This repository is not yet in the default HACS store, so it must be added as a custom repository.)

### Manual installation
1. Download this repository (e.g. `git clone` or download the ZIP of the `main` branch).
2. Copy `custom_components/nio_open` into `<your-ha-config>/custom_components/nio_open`.
3. Restart Home Assistant, then follow the setup below. Do not copy credentials or your Home Assistant configuration into this repository.

## Setup
1. In the NIO Open Platform console, register these redirect URIs on your application:
   - `https://my.home-assistant.io/redirect/oauth` (preferred; set your HA URL on my.home-assistant.io)
   - `http://<your-ha-host>:8123/auth/external/callback` (fallback)
2. Settings → Devices & services → **Add integration → NIO Open Platform**. Enter your `client_id` / `client_secret` when prompted (application credentials), authorize at NIO, then enter your VIN.

## Notes
- Requested scopes: `vehicle:read` plus dynamics, location, energy, body, cabin, powertrain and diagnostics (`:read`). `vehicle:connectivity:read` and `aftersales:read` are not requested because NIO rejects the whole authorization with `invalid_scope` when they are included.
- NIO reports `0` for ambient/outside/fridge temperatures it has not sampled; these are treated as missing (the last real reading is kept, otherwise the sensor is `unknown`). Change endpoints only serve the last 60 minutes, so these sensors refresh only while the vehicle is in use.
- NIO only returns data that changed recently, so a parked car reports nothing new. The last known values are saved in Home Assistant's `.storage` (including position) and restored after a restart; they are deleted when the integration is removed.
- The Open Platform only exposes `position_status/changes`; there is no "latest position" endpoint. NIO only emits a position record when the vehicle's location actually changes, so the device tracker stays `unknown` while the car is parked, even with good GPS reception — this matches what the NIO app shows via its own private API, which this integration cannot access. A position appears once the vehicle is driven again.
- Personal NIO applications cannot use `client_credentials`; the authorization-code flow is required.
- Do not run this alongside another NIO integration using the same application unless you want to share NIO's rate limit.

## Development
Offline tests have been verified with Python 3.14.6, Home Assistant 2026.10.2, and `pytest-homeassistant-custom-component==0.13.373`. Older Home Assistant versions and live vehicle authorization have not been verified for this release.

```
python3.14 -m venv .venv
.venv/bin/pip install pytest-homeassistant-custom-component==0.13.373
.venv/bin/python -m pytest
```
