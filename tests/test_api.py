"""Tests for the NIO API client."""

from __future__ import annotations

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
    assert url.endswith("/vehicles/VIN123/vehicle_status/latest")


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
