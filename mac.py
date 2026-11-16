from data_structure import Pattern

def mac(filter_p: Pattern, input_p: Pattern) -> float:
    """
    MAC(Multiply-Accumulate) 연산
    반환값: 두 행렬의 원소별 곱의 합 (float)
    """
    if filter_p.n != input_p.n:
        raise ValueError(
            f"크기가 달라요! filter={filter_p.n}, input={input_p.n}"
        )

    n      = filter_p.n
    result = 0.0

    for r in range(n):
        for c in range(n):
            result += filter_p.get(r, c) * input_p.get(r, c)

    return result
```