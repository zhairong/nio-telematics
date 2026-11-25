"""Client for the NIO Open Platform telematics API."""

from __future__ import annotations

from typing import Any, Protocol

from .const import API_BASE_URL, ENDPOINTS, PLACEHOLDER_ZERO_FIELDS

AUTH_RESULT_CODES = frozenset(
    {"access_denied", "invalid_token", "unauthorized", "forbidden", "invalid_grant"}
)


class NioApiError(Exception):
    """The NIO API returned an error."""


class NioAuthError(NioApiError):
    """The NIO API rejected the credentials or scope."""


class Requester(Protocol):
    """Subset of HA's OAuth2Session used by the client."""

    async def async_request(self, method: str, url: str, **kwargs: Any) -> Any: ...


def merge_records(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Fold sparse change records into one dict keeping the newest non-null field."""
    if not records:
        return None
    merged: dict[str, Any] = {}
    for record in sorted(records, key=lambda r: r.get("sample_timestamp") or 0):
        merged.update({k: v for k, v in record.items() if v is not None})
    return merged


async def _result_code(response: Any) -> Any:
    try:
        payload = await response.json(content_type=None)
    except Exception:  # noqa: BLE001 - response details may contain private data
        return None
    return payload.get("result_code") if isinstance(payload, dict) else None


class NioApi:
    """Fetch telematics data for one vehicle."""

    def __init__(self, session: Requester, vin: str) -> None:
        self._session = session
        self._vin = vin

    async def fetch(self, endpoint: str) -> dict[str, Any] | None:
        """Return the current merged record of an endpoint, or None if empty."""
        url = f"{API_BASE_URL}/vehicles/{self._vin}/{ENDPOINTS[endpoint].path}"
        try:
            response = await self._session.async_request("get", url)
        except Exception as err:  # noqa: BLE001 - normalised below
            status = getattr(err, "status", None)
            if status in (401, 403):
                raise NioAuthError(f"HTTP {status} from NIO") from None
            raise NioApiError(f"Request to {endpoint} failed") from None

        if response.status in (401, 403):
            raise NioAuthError(f"HTTP {response.status} from NIO")
        if response.status == 404 and await _result_code(response) == "resource_not_found":
            # `*/changes` answers 404 when nothing changed in the window.
            return None
        if response.status >= 400:
            raise NioApiError(f"HTTP {response.status} from {endpoint}")

        try:
            payload = await response.json(content_type=None)
        except Exception:  # noqa: BLE001 - response details may contain private data
            raise NioApiError(f"Invalid response from {endpoint}") from None
        if not isinstance(payload, dict):
            raise NioApiError(f"Unexpected payload from {endpoint}")
        code = payload.get("result_code")
        if code != "success":
            if isinstance(code, str) and code in AUTH_RESULT_CODES:
                raise NioAuthError(f"NIO denied access to {endpoint}")
            raise NioApiError(f"NIO rejected {endpoint} request")

        data = payload.get("data")
        placeholders = PLACEHOLDER_ZERO_FIELDS.get(endpoint, frozenset())

        def clean(record: dict[str, Any]) -> dict[str, Any]:
            return {
                k: v for k, v in record.items() if not (k in placeholders and v == 0)
            }

        if isinstance(data, list):
            return merge_records([clean(r) for r in data if isinstance(r, dict)])
        return clean(data) if isinstance(data, dict) else None
