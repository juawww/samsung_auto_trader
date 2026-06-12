from api_client import KisApiClient
from logger import log


CURRENT_PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"
CURRENT_PRICE_TR_ID = "FHKST01010100"


def get_current_price(client: KisApiClient, stock_code: str) -> int:
    """국내주식 현재가를 조회한다."""
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
    }

    data = client.get(
        path=CURRENT_PRICE_PATH,
        tr_id=CURRENT_PRICE_TR_ID,
        params=params,
    )

    output = data.get("output", {})
    price_text = output.get("stck_prpr")

    if price_text is None:
        raise ValueError(f"Current price field not found: {data}")

    price = int(price_text)

    log(f"현재가 조회: {stock_code} = {price:,}원")

    return price

DAILY_PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
DAILY_PRICE_TR_ID = "FHKST01010400"


def get_recent_closing_prices(
    client: KisApiClient,
    stock_code: str,
    count: int = 20,
) -> list[int]:
    """최근 일봉 종가를 조회한다."""
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "0",
    }

    data = client.get(
        path=DAILY_PRICE_PATH,
        tr_id=DAILY_PRICE_TR_ID,
        params=params,
    )

    output = data.get("output", [])

    if not output:
        raise ValueError(f"Daily price data not found: {data}")

    closes: list[int] = []

    for item in output:
        close_text = item.get("stck_clpr")

        if close_text:
            closes.append(int(close_text))

        if len(closes) >= count:
            break

    if len(closes) < count:
        raise ValueError(f"Not enough closing prices. Need {count}, got {len(closes)}")

    log(f"최근 종가 {count}개 조회 완료: {closes[:5]} ...")

    return closes


def average(values: list[int]) -> float:
    """숫자 리스트의 평균을 계산한다."""
    return sum(values) / len(values)


def get_moving_average_signal(
    client: KisApiClient,
    stock_code: str,
) -> dict:
    """5일/20일 이동평균선을 이용해 매수/매도/관망 신호를 만든다."""
    closes = get_recent_closing_prices(client, stock_code, count=20)

    ma5 = average(closes[:5])
    ma20 = average(closes[:20])

    if ma5 > ma20:
        signal = "buy"
        reason = "5일 이동평균선이 20일 이동평균선보다 높아 상승 추세로 판단"
    elif ma5 < ma20:
        signal = "sell"
        reason = "5일 이동평균선이 20일 이동평균선보다 낮아 약세 또는 하락 추세로 판단"
    else:
        signal = "hold"
        reason = "5일 이동평균선과 20일 이동평균선이 같아 관망"

    result = {
        "ma5": ma5,
        "ma20": ma20,
        "signal": signal,
        "reason": reason,
    }

    log(f"이동평균 전략 결과: {result}")

    return result