"""Tests for the NIO API client."""

from __future__ import annotations

import traceback
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.nio_open.api import (
    NioApi,
    NioApiError,
    NioAuthError,
    merge_records,
)


def make_session(payload, status=200):
    response = MagicMock()
    response.status = status
    response.json = AsyncMock(return_value=payload)
    session = MagicMock()
    session.async_request = AsyncMock(return_value=response)
    return session


def test_merge_records_keeps_newest_non_null_field():
    records = [
        {"sample_timestamp": 2, "soc": None, "remaining_range": 300},
        {"sample_timestamp": 1, "soc": 80, "remaining_range": 310},
    ]
    assert merge_records(records) == {
        "sample_timestamp": 2,
        "soc": 80,
        "remaining_range": 300,
    }


def test_merge_records_empty():
    assert merge_records([]) is None


async def test_fetch_dict_and_url():
    session = make_session(
        {"result_code": "success", "data": {"soc": 55, "speed": 0}}
    )
    api = NioApi(session, "VIN123")
    assert await api.fetch("vehicle_status") == {"soc": 55, "speed": 0}
    url = session.async_request.await_args.args[1]
    assert session.async_request.await_args.args[0] == "get"
    assert url.endswith("/vehicles/VIN123/vehicle_status/latest")
    assert "?" not in url
    assert "#" not in url


async def test_fetch_list_is_merged():
    session = make_session(
        {"result_code": "success", "data": [{"sample_timestamp": 1, "soc": 50}]}
    )
    assert await NioApi(session, "V").fetch("soc_status") == {
        "sample_timestamp": 1,
        "soc": 50,
    }


async def test_fetch_empty_list_is_none():
    session = make_session({"result_code": "success", "data": []})
    assert await NioApi(session, "V").fetch("soc_status") is None


async def test_non_success_raises_api_error():
    session = make_session({"result_code": "server_error"})
    with pytest.raises(NioApiError):
        await NioApi(session, "V").fetch("soc_status")


@pytest.mark.parametrize(
    ("payload", "status"),
    [({"result_code": "access_denied"}, 200), ({}, 401), ({}, 403)],
)
async def test_auth_errors(payload, status):
    session = make_session(payload, status)
    with pytest.raises(NioAuthError):
        await NioApi(session, "V").fetch("soc_status")


@pytest.mark.parametrize("status", [None, 401, 403])
async def test_request_errors_do_not_expose_sensitive_details(status):
    sensitive = "VIN_SYNTHETIC token=SYNTHETIC_SECRET user@example.invalid 192.0.2.1"
    error = RuntimeError(sensitive)
    error.status = status
    session = make_session({})
    session.async_request.side_effect = error
    error_type = NioAuthError if status in (401, 403) else NioApiError
    with pytest.raises(error_type) as exc:
        await NioApi(session, "V").fetch("soc_status")
    assert sensitive not in "".join(traceback.format_exception(exc.value))


async def test_invalid_json_does_not_expose_response_or_url():
    sensitive = "VIN_SYNTHETIC latitude=12.345 token=SYNTHETIC_SECRET"
    session = make_session({})
    session.async_request.return_value.json.side_effect = ValueError(sensitive)
    with pytest.raises(NioApiError) as exc:
        await NioApi(session, "V").fetch("soc_status")
    assert sensitive not in "".join(traceback.format_exception(exc.value))


@pytest.mark.parametrize(
    "code", ["token=SYNTHETIC_SECRET", {"token": "SYNTHETIC_SECRET"}]
)
async def test_unknown_result_code_is_not_exposed(code):
    session = make_session({"result_code": code})
    with pytest.raises(NioApiError) as exc:
        await NioApi(session, "V").fetch("soc_status")
    assert "SYNTHETIC_SECRET" not in "".join(traceback.format_exception(exc.value))


async def test_placeholder_zero_temperatures_are_dropped():
    # NIO reports 0 for HVAC/fridge temperatures it has not sampled.
    session = make_session(
        {
            "result_code": "success",
            "data": [
                {"sample_timestamp": 1, "amb_temp_c": 7.5, "outside_temp_c": 6.0},
                {"sample_timestamp": 2, "amb_temp_c": 0, "outside_temp_c": 0.0, "pm2p5cabin": 0},
            ],
        }
    )
    assert await NioApi(session, "V").fetch("hvac_status") == {
        "sample_timestamp": 2,
        "amb_temp_c": 7.5,
        "outside_temp_c": 6.0,
        "pm2p5cabin": 0,
    }


async def test_placeholder_zero_fridge_temperature_is_dropped():
    session = make_session(
        {"result_code": "success", "data": [{"sample_timestamp": 1, "fridge_set_temp": 0}]}
    )
    assert await NioApi(session, "V").fetch("fridge_status") == {"sample_timestamp": 1}


async def test_no_recent_changes_is_none():
    session = make_session({"result_code": "resource_not_found"}, 404)
    assert await NioApi(session, "V").fetch("soc_status") is None


async def test_other_404_raises_api_error():
    session = make_session({"result_code": "not_found_other"}, 404)
    with pytest.raises(NioApiError):
        await NioApi(session, "V").fetch("soc_status")
