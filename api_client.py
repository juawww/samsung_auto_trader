from typing import Any, Dict, Optional

import requests

from auth import get_access_token
from config import Config
from logger import log


class KisApiClient:
    """KIS Open API 요청을 담당하는 공통 클라이언트."""

    def __init__(self, config: Config):
        self.config = config
        self.access_token = get_access_token(config)

    def make_headers(self, tr_id: str) -> Dict[str, str]:
        """API 요청에 필요한 공통 header를 만든다."""
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def get(
        self,
        path: str,
        tr_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """GET 요청을 보낸다."""
        url = f"{self.config.base_url}{path}"

        for attempt in range(1, 3):
            try:
                response = requests.get(
                    url,
                    headers=self.make_headers(tr_id),
                    params=params,
                    timeout=10,
                )
                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                log(f"GET API 오류 발생, attempt={attempt}: {e}")

                if attempt == 2:
                    raise

        raise RuntimeError("GET request failed")

    def post(
        self,
        path: str,
        tr_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """POST 요청을 보낸다."""
        url = f"{self.config.base_url}{path}"

        for attempt in range(1, 3):
            try:
                response = requests.post(
                    url,
                    headers=self.make_headers(tr_id),
                    json=payload,
                    timeout=10,
                )
                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                log(f"POST API 오류 발생, attempt={attempt}: {e}")

                if attempt == 2:
                    raise

        raise RuntimeError("POST request failed")