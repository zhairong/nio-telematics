# NIO Open Platform for Home Assistant

Read-only Home Assistant integration that shows your NIO vehicle via the [NIO EU Open Platform](https://open-eu.nio.com/).

Repository: [zhairong/nio-telematics](https://github.com/zhairong/nio-telematics). This repository is currently private. Its layout is prepared for HACS, but standard HACS installation requires a public repository; use the manual installation below until it is made public.

## Entities
- **Sensors**: battery %, range, charging state, speed, odometer, temperatures, battery/cell data, window positions, seat heating/ventilation, fridge, trip, driving mode, …
- **Binary sensors**: doors, hood, tailgate, charge port, locks, lights, air conditioning.
- **Device tracker**: vehicle position (only while NIO reports a valid fix).

Many diagnostic entities are disabled by default; enable them in the entity registry.
Polling: every 60 s for core data (battery, vehicle status, position, doors); other endpoints every 5 minutes.

## Installation

### Manual installation (private repository)
1. With an account that has repository access, download the reviewed integration branch or merged default branch.
2. Copy `custom_components/nio_open` into `<your-ha-config>/custom_components/nio_open`.
3. Restart Home Assistant, then follow the setup below. Do not copy credentials or your Home Assistant configuration into this repository.

### HACS (after the repository becomes public)
HACS → ⋮ → **Custom repositories** → add `https://github.com/zhairong/nio-telematics`, category **Integration**, then install and restart Home Assistant. The current private repository is not a standard HACS installation source and is not listed in the default HACS store.

## Setup
1. In the NIO Open Platform console, register these redirect URIs on your application:
   - `https://my.home-assistant.io/redirect/oauth` (preferred; set your HA URL on my.home-assistant.io)
   - `http://<your-ha-host>:8123/auth/external/callback` (fallback)
2. Settings → Devices & services → **Add integration → NIO Open Platform**. Enter your `client_id` / `client_secret` when prompted (application credentials), authorize at NIO, then enter your VIN.

## Notes
- Requested scopes: `vehicle:read` plus dynamics, location, energy, body, cabin, powertrain and diagnostics (`:read`). `vehicle:connectivity:read` and `aftersales:read` are not requested because NIO rejects the whole authorization with `invalid_scope` when they are included.
- Personal NIO applications cannot use `client_credentials`; the authorization-code flow is required.
- Do not run this alongside another NIO integration using the same application unless you want to share NIO's rate limit.

## Development
Offline tests have been verified with Python 3.14.6, Home Assistant 2026.10.2, and `pytest-homeassistant-custom-component==0.13.373`. Older Home Assistant versions and live vehicle authorization have not been verified for this release.

```
python3.14 -m venv .venv
.venv/bin/pip install pytest-homeassistant-custom-component==0.13.373
.venv/bin/python -m pytest
```
