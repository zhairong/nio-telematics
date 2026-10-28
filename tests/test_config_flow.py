"""Tests for the config flow."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.nio_open.const import DOMAIN, TOKEN_URL

REDIRECT = "https://example.com/auth/external/callback"
TOKEN = {
    "result_code": "success",
    "data": {
        "access_token": "a",
        "refresh_token": "r",
        "expires_in": 7200,
        "token_type": "Bearer",
    },
}


async def setup_credentials(hass: HomeAssistant) -> None:
    assert await async_setup_component(hass, "application_credentials", {})
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential("cid", "sec"), "cred"
    )


async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    current_request_with_host: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    await setup_credentials(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass, {"flow_id": result["flow_id"], "redirect_uri": REDIRECT}
    )
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    assert "scope=vehicle:read+vehicle:dynamics:read" in result["url"]
    assert "code_challenge" in result["url"]
    client = await hass_client_no_auth()
    assert (await client.get(f"/auth/external/callback?code=abcd&state={state}")).status == 200
    aioclient_mock.post(TOKEN_URL, json=TOKEN)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "vin"

    with patch("custom_components.nio_open.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"vin": " sqetest000123456 "}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["vin"] == "SQETEST000123456"
    assert result["data"]["token"]["access_token"] == "a"


async def test_duplicate_vin_aborts(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    current_request_with_host: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    await setup_credentials(hass)
    MockConfigEntry(domain=DOMAIN, unique_id="SQETEST000123456", data={}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass, {"flow_id": result["flow_id"], "redirect_uri": REDIRECT}
    )
    client = await hass_client_no_auth()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")
    aioclient_mock.post(TOKEN_URL, json=TOKEN)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"vin": "SQETEST000123456"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
