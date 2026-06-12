import time
from datetime import datetime, time as dt_time
from typing import Any, Dict

from account import get_balance, get_holding_info
from market_data import get_current_price, get_moving_average_signal
from api_client import KisApiClient
from logger import log
from orders import place_order


TRADING_START = dt_time(9, 10)
TRADING_END = dt_time(15, 30)


def is_before_trading_time() -> bool:
    return datetime.now().time() < TRADING_START


def is_trading_time() -> bool:
    now = datetime.now().time()
    return TRADING_START <= now <= TRADING_END

def wait_until_trading_time() -> None:
    """09:10 전이면 대기한다."""
    while is_before_trading_time():
        log("아직 자동매매 시작 전입니다. 09:10까지 대기합니다.")
        time.sleep(60)


def balance_changed(before: Dict[str, Any], after: Dict[str, Any]) -> bool:
    """주문 전후 잔고 정보가 달라졌는지 단순 비교한다."""
    return before.get("holdings") != after.get("holdings") or before.get("summary") != after.get("summary")


def run_once(client: KisApiClient) -> None:
    """이동평균, 보유 수량, 익절/손절 기준을 반영한 자동매매 1회 실행."""
    config = client.config

    log("자동매매 1회 실행 시작")

    # 1. 현재가 조회
    current_price = get_current_price(client, config.stock_code)

    # 2. 이동평균 전략 계산
    strategy = get_moving_average_signal(client, config.stock_code)
    signal = strategy["signal"]
    ma5 = strategy["ma5"]
    ma20 = strategy["ma20"]

    log(f"전략 신호: {signal}, 5일선={ma5:,.2f}, 20일선={ma20:,.2f}")

    # 3. 주문 전 잔고 조회
    before_balance = get_balance(client)
    holding_info = get_holding_info(before_balance, config.stock_code)

    holding_quantity = holding_info["quantity"]
    average_price = holding_info["average_price"]

    log(f"주문 전 보유 수량: {holding_quantity}주")
    log(f"평균매입가: {average_price:,.0f}원")
    log(f"주문 전 보유종목: {before_balance['holdings']}")
    log(f"주문 전 요약: {before_balance['summary']}")

    buy_result = None
    sell_result = None

    # 4. 보유 중인 경우 수익률 계산
    profit_rate = 0.0

    if holding_quantity > 0 and average_price > 0:
        profit_rate = (current_price - average_price) / average_price
        log(f"현재 수익률: {profit_rate * 100:.2f}%")

    # 5. 매수 조건
    if holding_quantity == 0 and signal == "buy":
        buy_price = current_price - config.price_offset

        log("매수 조건 충족: 보유 수량 0주 + 5일선 > 20일선")
        log(f"현재가보다 {config.price_offset:,}원 낮은 {buy_price:,}원에 매수 주문을 요청합니다.")

        buy_result = place_order(
            client=client,
            stock_code=config.stock_code,
            quantity=config.order_quantity,
            price=buy_price,
            side="buy",
        )

    # 6. 익절 조건
    elif holding_quantity > 0 and profit_rate >= config.take_profit_rate:
        sell_price = current_price + config.price_offset

        log(f"익절 조건 충족: 수익률 {profit_rate * 100:.2f}%")
        log(f"현재가보다 {config.price_offset:,}원 높은 {sell_price:,}원에 매도 주문을 요청합니다.")

        sell_result = place_order(
            client=client,
            stock_code=config.stock_code,
            quantity=holding_quantity,
            price=sell_price,
            side="sell",
        )

    # 7. 손절 조건
    elif holding_quantity > 0 and profit_rate <= -config.stop_loss_rate:
        sell_price = current_price

        log(f"손절 조건 충족: 수익률 {profit_rate * 100:.2f}%")
        log(f"손실 확대를 막기 위해 현재가 {sell_price:,}원에 매도 주문을 요청합니다.")

        sell_result = place_order(
            client=client,
            stock_code=config.stock_code,
            quantity=holding_quantity,
            price=sell_price,
            side="sell",
        )

    # 8. 추세 약화 매도 조건
    elif holding_quantity > 0 and signal == "sell":
        sell_price = current_price + config.price_offset

        log("추세 약화 조건 충족: 보유 수량 있음 + 5일선 < 20일선")
        log(f"현재가보다 {config.price_offset:,}원 높은 {sell_price:,}원에 매도 주문을 요청합니다.")

        sell_result = place_order(
            client=client,
            stock_code=config.stock_code,
            quantity=holding_quantity,
            price=sell_price,
            side="sell",
        )

    # 9. 관망
    else:
        log("매수/매도 조건이 충족되지 않아 관망합니다.")

    # 10. 주문 후 잔고 재조회
    time.sleep(3)

    after_balance = get_balance(client)

    log(f"주문 후 보유종목: {after_balance['holdings']}")
    log(f"주문 후 요약: {after_balance['summary']}")

    # 11. 주문 결과 확인
    if buy_result is not None:
        if buy_result.get("result_code") == "0":
            log("매수 주문이 정상 접수되었습니다.")
        else:
            log(f"매수 주문이 거절되었거나 실패했습니다: {buy_result.get('message')}")

    if sell_result is not None:
        if sell_result.get("result_code") == "0":
            log("매도 주문이 정상 접수되었습니다.")
        else:
            log(f"매도 주문이 거절되었거나 실패했습니다: {sell_result.get('message')}")

    # 12. 주문 전후 잔고 비교
    if balance_changed(before_balance, after_balance):
        log("주문 전후 잔고가 달라졌습니다. 체결 또는 계좌 상태 변화 가능성이 있습니다.")
    else:
        log("주문 전후 잔고가 동일합니다. 미체결, 주문 거절, 관망, 또는 장외 제한 가능성이 있습니다.")

    log("자동매매 1회 실행 종료")
        
def run_trading_loop(client: KisApiClient) -> None:
    """09:10~15:30 사이에만 자동매매 루프를 실행한다."""
    config = client.config

    log("삼성전자 모의 자동매매 프로그램 시작")
    log(f"거래 대상: 삼성전자({config.stock_code})")
    log(f"거래 시간: {TRADING_START} ~ {TRADING_END}")
    log(f"반복 간격: {config.polling_interval_seconds}초")
    log("주의: 본 프로그램은 모의투자 환경 전용입니다.")

    wait_until_trading_time()

    while True:
        if not is_trading_time():
            log("자동매매 가능 시간이 종료되었습니다. 프로그램을 종료합니다.")
            break

        run_once(client)

        log(f"{config.polling_interval_seconds}초 동안 대기합니다.")
        time.sleep(config.polling_interval_seconds)