"""Tests for the NIO OAuth2 implementation."""

from __future__ import annotations

import base64
import traceback

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2TokenRequestReauthError,
    OAuth2TokenRequestTransientError,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.nio_open.application_credentials import NioOAuth2Implementation
from custom_components.nio_open.const import AUTHORIZE_URL, OAUTH_SCOPES, TOKEN_URL

GOOD = {
    "result_code": "success",
    "data": {
        "access_token": "a",
        "refresh_token": "r",
        "expires_in": 7200,
        "token_type": "Bearer",
    },
}


def impl(hass: HomeAssistant) -> NioOAuth2Implementation:
    return NioOAuth2Implementation(hass, "nio_open", "cid", AUTHORIZE_URL, TOKEN_URL, "sec")


async def test_token_request_uses_basic_auth_and_unwraps(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.post(TOKEN_URL, json=GOOD)
    token = await impl(hass)._token_request(
        {"grant_type": "authorization_code", "code": "c", "client_id": "cid", "client_secret": "sec"}
    )
    assert token["access_token"] == "a"
    _, _, body, headers = aioclient_mock.mock_calls[0]
    assert headers["Authorization"] == "Basic " + base64.b64encode(b"cid:sec").decode()
    assert "client_secret" not in body


async def test_refresh_keeps_old_fields(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.post(TOKEN_URL, json=GOOD)
    token = await impl(hass)._async_refresh_token({"refresh_token": "old", "extra": 1})
    assert token["extra"] == 1
    assert token["refresh_token"] == "r"


async def test_invalid_grant_requires_reauth(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.post(TOKEN_URL, json={"result_code": "invalid_grant"})
    with pytest.raises(OAuth2TokenRequestReauthError):
        await impl(hass)._token_request({"grant_type": "refresh_token"})


@pytest.mark.parametrize(
    "code", ["token=SYNTHETIC_SECRET", {"token": "SYNTHETIC_SECRET"}]
)
async def test_rejected_token_does_not_expose_result_code(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, code
) -> None:
    aioclient_mock.post(TOKEN_URL, status=400, json={"result_code": code})
    with pytest.raises(OAuth2TokenRequestReauthError) as exc:
        await impl(hass)._token_request({"grant_type": "refresh_token"})
    assert "SYNTHETIC_SECRET" not in "".join(traceback.format_exception(exc.value))


async def test_server_error_is_transient(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.post(TOKEN_URL, status=503, json={})
    with pytest.raises(OAuth2TokenRequestTransientError):
        await impl(hass)._token_request({"grant_type": "refresh_token"})


async def test_authorize_data_has_scope(hass: HomeAssistant) -> None:
    data = impl(hass).extra_authorize_data
    assert data["scope"] == " ".join(OAUTH_SCOPES)
    assert "code_challenge" in data
