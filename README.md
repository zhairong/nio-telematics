# NIO Open Platform for Home Assistant

Read-only Home Assistant integration (HACS custom repository, type **Integration**) that shows your NIO vehicle via the [NIO EU Open Platform](https://open-eu.nio.com/).

## Entities
- **Sensors**: battery %, range, charging state, speed, odometer, temperatures, battery/cell data, window positions, seat heating/ventilation, fridge, trip, driving mode, …
- **Binary sensors**: doors, hood, tailgate, charge port, locks, lights, air conditioning.
- **Device tracker**: vehicle position (only while NIO reports a valid fix).

Many diagnostic entities are disabled by default; enable them in the entity registry.
Polling: every 60 s for core data (battery, vehicle status, position, doors); other endpoints every 5 minutes.

## Setup
1. In the NIO Open Platform console, register these redirect URIs on your application:
   - `https://my.home-assistant.io/redirect/oauth` (preferred; set your HA URL on my.home-assistant.io)
   - `http://<your-ha-host>:8123/auth/external/callback` (fallback)
2. HACS → ⋮ → **Custom repositories** → add this repository, category **Integration**, then install and restart Home Assistant.
3. Settings → Devices & services → **Add integration → NIO Open Platform**. Enter your `client_id` / `client_secret` when prompted (application credentials), authorize at NIO, then enter your VIN.

## Notes
- Requested scopes: `vehicle:read` plus dynamics, location, energy, body, cabin, powertrain and diagnostics (`:read`). `vehicle:connectivity:read` and `aftersales:read` are not requested because NIO rejects the whole authorization with `invalid_scope` when they are included.
- Personal NIO applications cannot use `client_credentials`; the authorization-code flow is required.
- Do not run this alongside another NIO integration using the same application unless you want to share NIO's rate limit.

## Development
```
python3 -m venv .venv && .venv/bin/pip install pytest-homeassistant-custom-component
.venv/bin/python -m pytest
```
