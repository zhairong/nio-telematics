# NIO Open Platform — Home Assistant Integration (HACS) Design

## Goal
A HACS custom repository (type: Integration, repo `nio-telematics`) that shows the user's NIO vehicle data in Home Assistant (http://192.168.31.211:8123/), read-only, using the NIO EU Open Platform.

## API facts (from open-eu.nio.com docs / `/portal-api/spec/vehicles`)
- Auth base: `https://open-eu.nio.com`; data base: `https://open-api-eu.nio.com`.
- OAuth2 authorization code (+PKCE): `GET /oauth2/authorize`, `POST /api/2/oauth/token` (Basic `client_id:client_secret`, grants: authorization_code, refresh_token, client_credentials), `GET /api/2/oauth/userinfo`.
- Data: `GET /api/1/telematics/vehicles/{vin}/<x>/changes?start_time&end_time` (ms, default window 10 min) for window_status, trip_status, soc_status, position_status, light_status, hvac_status, heating_status, fridge_status, extremum_data, driving_motor, driving_data, door_status, cell_status, alarm_signal, vehicle_status; plus `vehicle_status/latest`; aftersales: recalls, odometer_reports.
- Responses use envelope `{request_id, result_code, server_time, data}`; business errors may be HTTP 200 with non-`success` `result_code`.
- Scopes: vehicle:{dynamics,energy,body,location,cabin,powertrain,connectivity,diagnostics}:read, aftersales:read.

## Decisions
- Standard HA OAuth2 (`application_credentials` + `config_entry_oauth2_flow`), redirect_uri `https://my.home-assistant.io/redirect/oauth` (fallback `http://192.168.31.211:8123/auth/external/callback`); both must be registered on the NIO client.
- client_id/secret entered once in HA UI (never committed); VIN entered in config flow.
- Read-only. Out of scope: ADAS snapshot/event downloads, vehicle control.
- One `DataUpdateCoordinator`, default poll 5 min (options-configurable), concurrent endpoint calls, per-endpoint failure isolation, backoff on 429.
- `*/changes` endpoints: query `[now-window, now]`, take the last sample as current value; keep previous value when window is empty.

## Layout
```
custom_components/nio_open/
  manifest.json  const.py  api.py  application_credentials.py
  config_flow.py  coordinator.py  sensor.py  binary_sensor.py
  device_tracker.py  strings.json  translations/
hacs.json  README.md  tests/
```

## Entities
- sensor: SOC, remaining range, charge state, charge target SOC, odometer/speed, temps, HVAC, fridge, heating, motor, battery extremum, recalls, odometer reports (complex fields in attributes).
- binary_sensor: doors/hood/tailgate/charge port ajar, windows, lights, vehicle lock, alarms, cell connectivity.
- device_tracker: position.

## Error handling
Token refresh via HA OAuth2 session; auth failure → reauth flow; API/envelope errors → `UpdateFailed`; entities go unavailable on failure.

## Testing
pytest with mocked aiohttp responses (envelope parsing, window logic, entity mapping, token refresh). Manual verification: copy to HA host via ssh, add integration, authorize, confirm entities.
