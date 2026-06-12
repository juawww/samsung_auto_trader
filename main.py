from api_client import KisApiClient
from config import load_config
from trader import run_trading_loop


def main() -> None:
    config = load_config()
    client = KisApiClient(config)
    run_trading_loop(client)


if __name__ == "__main__":
    main()