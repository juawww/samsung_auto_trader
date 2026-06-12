import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Config:
    account: str
    app_key: str
    app_secret: str
    base_url: str
    stock_code: str = "005930"
    order_quantity: int = 1
    price_offset: int = 1000
    polling_interval_seconds: int = 300
    take_profit_rate: float = 0.03
    stop_loss_rate: float = 0.02
    

def load_config() -> Config:
    """환경변수에서 설정값을 불러온다."""
    account = os.getenv("GH_ACCOUNT")
    app_key = os.getenv("GH_APPKEY")
    app_secret = os.getenv("GH_APPSECRET")
    base_url = os.getenv(
        "KIS_BASE_URL",
        "https://openapivts.koreainvestment.com:29443",
    )

    missing = []

    if not account:
        missing.append("GH_ACCOUNT")
    if not app_key:
        missing.append("GH_APPKEY")
    if not app_secret:
        missing.append("GH_APPSECRET")

    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    return Config(
        account=account,
        app_key=app_key,
        app_secret=app_secret,
        base_url=base_url,
    )


def split_account(account: str) -> tuple[str, str]:
    """12345678-01 형태의 계좌번호를 앞 8자리와 상품코드로 분리한다."""
    if "-" not in account:
        raise ValueError("GH_ACCOUNT must be like 12345678-01")

    cano, acnt_prdt_cd = account.split("-", 1)
    return cano, acnt_prdt_cd