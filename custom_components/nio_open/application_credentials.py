"""Application credentials and OAuth2 implementation for NIO Open Platform."""

from __future__ import annotations

from typing import Any, override

from aiohttp import ClientError, encode_basic_auth
from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2Implementation,
    LocalOAuth2ImplementationWithPkce,
    OAuth2TokenRequestError,
    OAuth2TokenRequestReauthError,
    OAuth2TokenRequestTransientError,
)

from .const import AUTHORIZE_URL, OAUTH_SCOPES, TOKEN_URL

REAUTH_CODES = frozenset({"invalid_grant", "invalid_token", "access_denied"})
TOKEN_FIELDS = ("access_token", "refresh_token", "expires_in", "token_type")


class NioOAuth2Implementation(LocalOAuth2ImplementationWithPkce):
    """PKCE flow where NIO wants Basic client auth and an enveloped response."""

    @property
    @override
    def extra_authorize_data(self) -> dict[str, str]:
        return {**super().extra_authorize_data, "scope": " ".join(OAUTH_SCOPES)}

    def _error(
        self, kind: type[OAuth2TokenRequestError], status: int, message: str
    ) -> OAuth2TokenRequestError:
        # Built without the request headers so credentials never reach logs.
        return kind(
            request_info=None,
            status=status,
            message=message,
            domain=self.domain,
        )

    @override
    async def _async_refresh_token(self, token: dict[str, Any]) -> dict[str, Any]:
        new_token = await self._token_request(
            {"grant_type": "refresh_token", "refresh_token": token["refresh_token"]}
        )
        return {**token, **new_token}

    @override
    async def _token_request(self, data: dict[str, Any]) -> dict[str, Any]:
        # HA adds client_id/secret to the body; NIO expects them as Basic auth.
        data = {k: v for k, v in data.items() if k not in ("client_id", "client_secret")}
        session = async_get_clientsession(self.hass)
        try:
            response = await session.post(
                self.token_url,
                data=data,
                headers={
                    "Accept": "application/json",
                    "Authorization": encode_basic_auth(self.client_id, self.client_secret),
                },
            )
            payload = await response.json(content_type=None)
        except (ClientError, TimeoutError):
            raise self._error(
                OAuth2TokenRequestTransientError, 0, "NIO token service unreachable"
            ) from None
        except (ValueError, TypeError):
            payload = None

        status = response.status
        if status == 429 or status >= 500:
            raise self._error(
                OAuth2TokenRequestTransientError, status, "NIO token service busy"
            )
        code = payload.get("result_code") if isinstance(payload, dict) else None
        token = payload.get("data") if isinstance(payload, dict) else None
        if code == "success" and isinstance(token, dict):
            if all(token.get(f) for f in TOKEN_FIELDS):
                return dict(token)
            raise self._error(OAuth2TokenRequestError, status, "Incomplete token")
        if (isinstance(code, str) and code in REAUTH_CODES) or 400 <= status < 500:
            raise self._error(
                OAuth2TokenRequestReauthError, status, "NIO rejected token request"
            )
        raise self._error(OAuth2TokenRequestError, status, "Invalid token response")


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return the NIO authorization server."""
    return AuthorizationServer(authorize_url=AUTHORIZE_URL, token_url=TOKEN_URL)


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> AbstractOAuth2Implementation:
    """Return the NIO OAuth2 implementation for a credential."""
    return NioOAuth2Implementation(
        hass,
        auth_domain,
        credential.client_id,
        AUTHORIZE_URL,
        TOKEN_URL,
        credential.client_secret,
    )
