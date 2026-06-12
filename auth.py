import json
from datetime import date
from pathlib import Path
from typing import Optional

import requests

from config import Config
from logger import log


TOKEN_CACHE_FILE = Path("token_cache.json")


def load_cached_token() -> Optional[str]:
    """오늘 발급받은 토큰이 있으면 재사용한다."""
    if not TOKEN_CACHE_FILE.exists():
        return None

    try:
        data = json.loads(TOKEN_CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    if data.get("date") == date.today().isoformat():
        token = data.get("access_token")
        if token:
            log("기존 access token을 재사용합니다.")
            return token

    return None


def save_token(token: str) -> None:
    """새로 발급받은 토큰을 token_cache.json에 저장한다."""
    data = {
        "date": date.today().isoformat(),
        "access_token": token,
    }

    TOKEN_CACHE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_access_token(config: Config) -> str:
    """KIS Open API access token을 발급받거나 재사용한다."""
    cached_token = load_cached_token()

    if cached_token:
        return cached_token

    log("새 access token을 발급받습니다.")

    url = f"{config.base_url}/oauth2/tokenP"

    payload = {
        "grant_type": "client_credentials",
        "appkey": config.app_key,
        "appsecret": config.app_secret,
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

    data = response.json()
    token = data["access_token"]

    save_token(token)

    log("새 access token 저장 완료")

    return token