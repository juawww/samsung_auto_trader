from typing import Any, Dict, List

from api_client import KisApiClient
from config import split_account
from logger import log


BALANCE_PATH = "/uapi/domestic-stock/v1/trading/inquire-balance"
BALANCE_TR_ID = "VTTC8434R"


def get_balance(client: KisApiClient) -> Dict[str, Any]:
    """모의투자 계좌 잔고와 보유종목을 조회한다."""
    cano, acnt_prdt_cd = split_account(client.config.account)

    params = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    data = client.get(
        path=BALANCE_PATH,
        tr_id=BALANCE_TR_ID,
        params=params,
    )

    holdings_raw: List[Dict[str, Any]] = data.get("output1", [])
    summary_raw = data.get("output2", [])

    holdings = []

    for item in holdings_raw:
        stock_code = item.get("pdno")
        quantity = item.get("hldg_qty", "0")

        if not stock_code or quantity == "0":
            continue

        holdings.append(
            {
                "stock_code": stock_code,
                "name": item.get("prdt_name", ""),
                "quantity": quantity,
                "average_price": item.get("pchs_avg_pric", ""),
                "current_price": item.get("prpr", ""),
                "evaluation_amount": item.get("evlu_amt", ""),
                "profit_loss": item.get("evlu_pfls_amt", ""),
                "profit_rate": item.get("evlu_pfls_rt", ""),
            }
        )

    summary = summary_raw[0] if isinstance(summary_raw, list) and summary_raw else {}

    result = {
        "holdings": holdings,
        "summary": {
            "total_evaluation": summary.get("tot_evlu_amt", ""),
            "purchase_amount": summary.get("pchs_amt_smtl_amt", ""),
            "profit_loss": summary.get("evlu_pfls_smtl_amt", ""),
            "deposit": summary.get("dnca_tot_amt", ""),
        },
        "raw": data,
    }

    log(f"잔고 조회 완료: 보유종목 {len(holdings)}개")

    return result

def get_holding_quantity(balance: Dict[str, Any], stock_code: str) -> int:
    """잔고 조회 결과에서 특정 종목의 보유 수량을 찾는다."""
    holdings = balance.get("holdings", [])

    for item in holdings:
        if item.get("stock_code") == stock_code:
            return int(item.get("quantity", "0"))

    return 0

def get_holding_info(balance: Dict[str, Any], stock_code: str) -> Dict[str, Any]:
    """잔고 조회 결과에서 특정 종목의 보유 수량과 평균매입가를 찾는다."""
    holdings = balance.get("holdings", [])

    for item in holdings:
        if item.get("stock_code") == stock_code:
            quantity = int(item.get("quantity", "0"))
            average_price = float(item.get("average_price", "0"))

            return {
                "quantity": quantity,
                "average_price": average_price,
            }

    return {
        "quantity": 0,
        "average_price": 0.0,
    }