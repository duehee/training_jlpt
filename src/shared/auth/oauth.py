"""Google OAuth 2.0 클라이언트 (인증 인프라, 세션 9 §a).

Authorization Code 흐름을 httpx로 직접 구현(authlib 미사용 — 의존성 최소 + 흐름 명시).
1) build_google_authorize_url(state): 사용자를 Google 동의 화면으로 보낼 URL 생성
2) exchange_code_for_google_user(code): 콜백의 code → 토큰 교환 → userinfo 조회

실 크레덴셜(client_id/secret)은 settings(.env, Q4 차후 주입). 테스트는 이 클라이언트를
의존성으로 교체(가짜)해 실제 Google 호출 없이 검증한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from src.core.config import settings

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@dataclass(frozen=True)
class GoogleUser:
    """Google이 검증한 계정 식별 정보. sub = provider_account_id."""

    sub: str
    email: str
    name: str | None


def build_google_authorize_url(state: str) -> str:
    """동의 화면 URL. state는 콜백에서 CSRF 방지용으로 대조된다."""
    params = {
        "client_id": settings.google_client_id or "",
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}"


class GoogleOAuthClient:
    """code → access token → userinfo 교환. 실제 Google 호출은 여기서만 발생."""

    async def exchange_code(self, code: str) -> GoogleUser:
        """authorization code를 토큰으로 교환하고 사용자 정보를 조회."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id or "",
                    "client_secret": settings.google_client_secret or "",
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]

            userinfo_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_resp.raise_for_status()
            data = userinfo_resp.json()

        return GoogleUser(
            sub=str(data["sub"]),
            email=str(data["email"]),
            name=data.get("name"),
        )


def get_google_oauth_client() -> GoogleOAuthClient:
    """FastAPI 의존성 — 테스트에서 가짜 클라이언트로 교체 가능."""
    return GoogleOAuthClient()
