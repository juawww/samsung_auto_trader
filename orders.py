from typing import Any, Dict

from api_client import KisApiClient
from config import split_account
from logger import log


ORDER_PATH = "/uapi/domestic-stock/v1/trading/order-cash"

BUY_TR_ID = "VTTC0802U"
SELL_TR_ID = "VTTC0801U"


def place_order(
    client: KisApiClient,
    stock_code: str,
    quantity: int,
    price: int,
    side: str,
) -> Dict[str, Any]:
    """모의투자 매수 또는 매도 주문을 요청한다."""
    cano, acnt_prdt_cd = split_account(client.config.account)

    if side == "buy":
        tr_id = BUY_TR_ID
        side_name = "매수"
    elif side == "sell":
        tr_id = SELL_TR_ID
        side_name = "매도"
    else:
        raise ValueError("side must be 'buy' or 'sell'")

    payload = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "PDNO": stock_code,
        "ORD_DVSN": "00",  # 지정가
        "ORD_QTY": str(quantity),
        "ORD_UNPR": str(price),
    }

    log(f"{side_name} 주문 요청: {stock_code}, 수량={quantity}, 가격={price:,}원")

    data = client.post(
        path=ORDER_PATH,
        tr_id=tr_id,
        payload=payload,
    )

    result = {
        "side": side,
        "stock_code": stock_code,
        "quantity": quantity,
        "price": price,
        "result_code": data.get("rt_cd"),
        "message_code": data.get("msg_cd"),
        "message": data.get("msg1"),
        "raw": data,
    }

    log(f"{side_name} 주문 응답: {result}")

    return result