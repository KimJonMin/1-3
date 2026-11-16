# performance.py

import time
from data_structure import Pattern
from mac import mac


def measure_performance(
    filter_p: Pattern,
    input_p:  Pattern,
    repeat:   int = 100
) -> float:
    """
    MAC 연산을 repeat번 반복해서 평균 실행 시간(ms)을 반환합니다
    """
    start = time.perf_counter()

    for _ in range(repeat):
        mac(filter_p, input_p)

    end = time.perf_counter()

    total_ms = (end - start) * 1000   # 초 → 밀리초
    avg_ms   = total_ms / repeat

    return avg_ms


if __name__ == "__main__":
    from json_loader import load_data

    data = load_data("data.json")

    # 첫 번째 크기의 Cross 필터와 첫 번째 패턴으로 테스트
    first_n  = sorted(data["filters"].keys())[0]   # 5
    filter_p = data["filters"][first_n]["Cross"]   # Pattern 객체
    input_p  = data["patterns"][0]["pattern"]      # Pattern 객체

    avg = measure_performance(filter_p, input_p, repeat=100)
    print(f"평균 시간: {avg:.6f} ms")