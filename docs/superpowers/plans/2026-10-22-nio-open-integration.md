# NIO Open Platform HA Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline). Steps use checkbox syntax.

**Goal:** HACS-installable HA integration `nio_open` that shows a NIO vehicle's data (read-only) via the NIO EU Open Platform.

**Architecture:** HA `application_credentials` + a custom `LocalOAuth2ImplementationWithPkce` (Basic client auth, envelope-wrapped token response). One `DataUpdateCoordinator` (60 s) fetches endpoints concurrently via `NioApi`; table-driven sensor/binary_sensor/device_tracker platforms read from the merged result.

**Tech Stack:** Python 3.14, Home Assistant 2026.10, aiohttp, pytest-homeassistant-custom-component.

## Global Constraints
- Domain `nio_open`; dir `custom_components/nio_open/`; HACS `hacs.json` at repo root.
- Auth base `https://open-eu.nio.com` (`/oauth2/authorize`, `/api/2/oauth/token`); data base `https://open-api-eu.nio.com/api/1/telematics`.
- Token request: `Authorization: Basic base64(client_id:client_secret)`, form body; response is envelope `{result_code:"success", data:{access_token, refresh_token, expires_in, token_type}}`.
- Scopes (observed on the HA host's existing NIO integration: `vehicle:connectivity:read` and `aftersales:read` cause `invalid_scope` for the whole authorization, so they are NOT requested): `vehicle:read vehicle:dynamics:read vehicle:location:read vehicle:energy:read vehicle:body:read vehicle:cabin:read vehicle:powertrain:read vehicle:diagnostics:read`. Consequently `cell_status` and aftersales endpoints are excluded.
- Poll interval default 60 s. Read-only. No secrets committed (`datas.yaml` is gitignored).
- Envelope: HTTP 200 with `result_code != "success"` is an error.

## File structure
```
hacs.json  README.md  pytest.ini
custom_components/nio_open/
  manifest.json strings.json translations/en.json
  const.py                    constants, ENDPOINTS table
  api.py                      NioApi: envelope parsing, errors, fetch()
  application_credentials.py  NioOAuth2Implementation + async_get_auth_implementation + async_get_authorization_server
  config_flow.py              OAuth2 flow + VIN step + reauth
  coordinator.py              NioCoordinator
  __init__.py                 setup/unload
  entity.py                   NioEntity base (device info)
  sensor.py binary_sensor.py device_tracker.py
tests/ conftest.py test_api.py test_oauth.py test_config_flow.py test_coordinator.py test_entities.py
```

### Task 1: Scaffold + API client
**Files:** `hacs.json`, `manifest.json`, `const.py`, `api.py`, `tests/test_api.py`, `pytest.ini`.
**Produces:** `NioApi(session, vin)` where `session` has `async_request(method, url, **kw)` (HA OAuth2Session); `async fetch(endpoint: str) -> Any|None` returns last item for list payloads; raises `NioAuthError`, `NioApiError`. `ENDPOINTS: dict[str, Endpoint]`, `Endpoint(path, windowed)`.
- [ ] Tests: unwrap (last list item / dict / empty→None), non-success `result_code` → `NioApiError`, `access_denied` or HTTP 401/403 → `NioAuthError`, windowed endpoints send `start_time`/`end_time` ms.
- [ ] Run (fail) → implement → run (pass) → commit.

### Task 2: OAuth implementation
**Files:** `application_credentials.py`, `tests/test_oauth.py`.
- [ ] Tests: token request sends Basic header and returns unwrapped `data`; non-success envelope raises error; authorize data contains PKCE + scope.
- [ ] Implement, run, commit.

### Task 3: Config flow
**Files:** `config_flow.py`, `strings.json`, `translations/en.json`, `tests/test_config_flow.py`.
**Produces:** `NioOAuth2FlowHandler(AbstractOAuth2FlowHandler, domain=DOMAIN)`; after OAuth, step `vin`; unique_id = VIN; reauth.
- [ ] Tests: full flow creates entry; duplicate VIN aborts. Implement, run, commit.

### Task 4: Coordinator + setup
**Files:** `coordinator.py`, `__init__.py`, `tests/test_coordinator.py`.
**Produces:** `NioCoordinator.data: dict[str, Any|None]` keyed by endpoint name; per-endpoint failure keeps previous value; auth error → `ConfigEntryAuthFailed`; all endpoints fail → `UpdateFailed`.
- [ ] Tests, implement, commit.

### Task 5: Entities
**Files:** `entity.py`, `sensor.py`, `binary_sensor.py`, `device_tracker.py`, `tests/test_entities.py`.
- sensor: SOC, range, charge states, speed, mileage, voltage/current, temps, HVAC/heating/fridge/trip/extremum/driving values, window positions.
- binary_sensor: door/hood/tailgate/charge-port ajar (`AJAR_OPENED`), vehicle lock, lights, hvac flags, alarms.
- device_tracker: lat/lon from `position_status` when `posng_valid_type == VALID`.
- [ ] Tests for mapping/states, implement, commit.

### Task 6: Docs + verification
- [ ] README (HACS custom repo install, redirect URIs, credentials, VIN).
- [ ] Full test suite. Copying to the HA host is done only with user go-ahead (host already runs another NIO integration `nio_telematics`).
- [ ] Commit.
