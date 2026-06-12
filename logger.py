from datetime import datetime


def log(message: str) -> None:
    """중요한 동작을 시간과 함께 출력한다."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}")