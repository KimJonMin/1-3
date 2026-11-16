# main.py

from json_loader    import load_data
from mac            import mac
from judge          import judge, check_pass_fail
from input_handler  import get_matrix_input
from performance    import measure_performance
from data_structure import Pattern


# ── 성능 분석 표 출력 ────────────────────────────────────────
def print_performance_table(data: dict):
    """
    3×3 포함 크기별 MAC 연산 시간 표를 출력합니다
    (요구사항: 크기별 10회 이상 반복 측정)
    """
    print("\n" + "=" * 52)
    print("  성능 분석 표 (각 크기별 100회 반복 측정)")
    print("=" * 52)
    print(f"  {'크기':<10} {'평균 시간(ms)':<18} {'연산횟수(N²)'}")
    print("-" * 52)

    filters = data["filters"]

    # 3×3 : data.json에 없으므로 임시 패턴 생성
    dummy_filter_3 = Pattern(3)
    dummy_input_3  = Pattern(3)
    for r in range(3):
        for c in range(3):
            dummy_filter_3.set(r, c, 1.0)
            dummy_input_3.set(r, c, 1.0)
    avg_3 = measure_performance(dummy_filter_3, dummy_input_3, repeat=100)
    print(f"  {'3×3':<10} {avg_3:<18.6f} {3*3}")

    # 5×5, 13×13, 25×25
    for n in sorted(filters.keys()):
        f_cross = filters[n]["Cross"]
        # 해당 크기의 첫 번째 패턴 찾기
        sample_pat = None
        for item in data["patterns"]:
            if item["pattern"].n == n:
                sample_pat = item["pattern"]
                break
        if sample_pat is None:
            sample_pat = Pattern(n)   # 없으면 빈 패턴

        avg_ms = measure_performance(f_cross, sample_pat, repeat=100)
        print(f"  {f'{n}×{n}':<10} {avg_ms:<18.6f} {n*n}")

    print("=" * 52)


# ── 모드 1: 사용자 입력 (3×3) ───────────────────────────────
def run_mode1():
    """
    3×3 필터 A, B와 패턴을 직접 입력받아 MAC 연산 및 판정
    """
    print("\n" + "=" * 50)
    print("  모드 1: 사용자 입력 (3×3)")
    print("=" * 50)

    n = 3

    # 필터 A 입력
    print("\n  [필터 A 입력]")
    grid_a   = get_matrix_input(n)
    filter_a = Pattern.load_from_list(grid_a)
    print("  ✅ 필터 A 저장 완료!")

    # 필터 B 입력
    print("\n  [필터 B 입력]")
    grid_b   = get_matrix_input(n)
    filter_b = Pattern.load_from_list(grid_b)
    print("  ✅ 필터 B 저장 완료!")

    # 패턴 입력
    print("\n  [패턴 입력]")
    grid_p  = get_matrix_input(n)
    pattern = Pattern.load_from_list(grid_p)
    print("  ✅ 패턴 저장 완료!")

    # MAC 연산
    score_a = mac(filter_a, pattern)
    score_b = mac(filter_b, pattern)

    # 판정 (A vs B)
    diff = score_a - score_b
    if abs(diff) < 1e-9:
        result = "판정 불가 (UNDECIDED)"
    elif diff > 0:
        result = "A"
    else:
        result = "B"

    # 성능 측정
    avg_ms = measure_performance(filter_a, pattern, repeat=100)

    # 결과 출력
    print("\n" + "-" * 50)
    print("  [결과]")
    print(f"  필터 A 점수 : {score_a:.4f}")
    print(f"  필터 B 점수 : {score_b:.4f}")
    print(f"  판정 결과   : {result}")
    print(f"  평균 시간   : {avg_ms:.6f} ms")
    print("-" * 50)


# ── 모드 2: data.json 자동 배치 검사 ────────────────────────
def run_mode2(data: dict):
    """
    data.json의 모든 패턴을 자동으로 검사합니다
    """
    print("\n" + "=" * 50)
    print("  모드 2: data.json 자동 배치 검사")
    print("=" * 50)

    filters      = data["filters"]
    patterns     = data["patterns"]
    total        = 0
    passed       = 0
    failed       = 0
    failed_cases = []   # 실패 케이스 목록

    for item in patterns:
        name     = item["name"]
        pat      = item["pattern"]
        expected = item["expected"]
        n        = pat.n

        # 크기 불일치 검증
        if n not in filters:
            reason = f"필터 없음 (size_{n} 미존재)"
            print(f"\n  [{name}]  ❌ FAIL - {reason}")
            total  += 1
            failed += 1
            failed_cases.append((name, reason))
            continue

        f_cross = filters[n]["Cross"]
        f_x     = filters[n]["X"]

        # 필터-패턴 크기 불일치 검증
        if f_cross.n != pat.n:
            reason = f"크기 불일치 (필터 {f_cross.n}×{f_cross.n} ≠ 패턴 {pat.n}×{pat.n})"
            print(f"\n  [{name}]  ❌ FAIL - {reason}")
            total  += 1
            failed += 1
            failed_cases.append((name, reason))
            continue

        # MAC 연산
        score_cross = mac(f_cross, pat)
        score_x     = mac(f_x,     pat)

        # 판정
        result    = judge(score_cross, score_x)
        pass_fail = check_pass_fail(result, expected)

        # 성능 측정
        avg_ms = measure_performance(f_cross, pat, repeat=100)

        # 결과 출력
        icon = "✅" if pass_fail == "PASS" else "❌"
        print(f"\n  [{name}]")
        print(f"  크기       : {n}×{n}")
        print(f"  Cross 점수 : {score_cross:.4f}")
        print(f"  X     점수 : {score_x:.4f}")
        print(f"  판정       : {result}")
        print(f"  정답       : {expected}")
        print(f"  결과       : {icon} {pass_fail}")
        print(f"  평균 시간  : {avg_ms:.6f} ms")

        total += 1
        if pass_fail == "PASS":
            passed += 1
        else:
            failed += 1
            reason = f"판정={result}, 정답={expected}"
            failed_cases.append((name, reason))

    # ── 결과 요약 ──────────────────────────────────────────
    print("\n" + "=" * 50)
    print(f"  총 {total}개 | ✅ PASS: {passed} | ❌ FAIL: {failed}")
    print("=" * 50)

    # 실패 케이스 목록 출력
    if failed_cases:
        print("\n  [실패 케이스 목록]")
        print("-" * 50)
        for case_name, reason in failed_cases:
            print(f"  ❌ {case_name} : {reason}")
        print("-" * 50)
    else:
        print("\n  🎉 모든 케이스 PASS!")
        print("  (라벨 정규화 + epsilon 정책 덕분에 실패 0개)")

    # 성능 분석 표 출력
    print_performance_table(data)


# ── 메인 함수 ───────────────────────────────────────────────
def main():
    print("=" * 50)
    print("   Mini NPU 시뮬레이터")
    print("=" * 50)

    # data.json 로드
    print("\ndata.json 로딩 중...")
    try:
        data = load_data("data.json")
        print("✅ 로딩 완료!")
    except FileNotFoundError as e:
        print(f"❌ 오류: {e}")
        return
    except ValueError as e:
        print(f"❌ 오류: {e}")
        return

        # 모드 선택 루프
    while True:
        print("\n" + "-" * 50)
        print("  모드를 선택하세요")
        print("  1. 사용자 입력 (3×3 필터 A/B + 패턴 직접 입력)")
        print("  2. data.json 자동 배치 검사")
        print("  3. 종료")
        print("-" * 50)

        choice = input("  선택 (1/2/3): ").strip()

        if choice == "1":
            run_mode1()
        elif choice == "2":
            run_mode2(data)
        elif choice == "3":
            print("\n  프로그램을 종료합니다. 수고하셨습니다! 👋")
            break
        else:
            print("  ⚠ 1, 2, 3 중 하나를 입력하세요.")


if __name__ == "__main__":
    main()