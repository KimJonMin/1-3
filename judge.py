def judge(score_cross: float, score_x: float, epsilon: float = 1e-9) -> str:
    """
    두 점수를 비교해 판정 결과를 반환합니다
    반환값: 'Cross' / 'X' / 'UNDECIDED'
    """
    diff = score_cross - score_x

    if abs(diff) < epsilon:
        return "UNDECIDED"
    elif diff > 0:
        return "Cross"
    else:
        return "X"


def check_pass_fail(judge_result: str, expected_label: str) -> str:
    """
    판정 결과와 정답을 비교해 PASS/FAIL을 반환합니다
    """
    if judge_result == "UNDECIDED":
        return "FAIL"
    elif judge_result == expected_label:
        return "PASS"
    else:
        return "FAIL"