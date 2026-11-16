from json_loader    import load_data
from mac            import mac
from judge          import judge, check_pass_fail
from input_handler  import get_size_input, get_matrix_input
from performance    import measure_performance
from data_structure import Pattern


# ── 모드 1: 자동 배치 검사 ──────────────────────────────────
def run_mode1(data: dict):
    """data.json의 모든 패턴을 자동으로 검사합니다"""

    print("\n" + "=" * 50)
    print("  모드 1: 자동 배치 검사")
    print("=" * 50)

    filters  = data["filters"]
    patterns = data["patterns"]

    total = passed = failed = 0

    for item in patterns:
        name     = item["name"]
        pat      = item["pattern"]
        expected = item["expected"]
        n        = pat.n

        # MAC 연산
        f_cross     = filters[n]["Cross"]
        f_x         = filters[n]["X"]
        score_cross = mac(f_cross, pat)
        score_x     = mac(f_x,     pat)

        # 판정
        result    = judge(score_cross, score_x)
        pass_fail = check_pass_fail(result, expected)

        # 성능 측정
        avg_ms = measure_performance(f_cross, pat, repeat=100)

        # 결과 출력
        print(f"\n  [{name}]")
        print(f"  크기       : {n}×{n}")
        print(f"  Cross 점수 : {score_cross:.4f}")
        print(f"  X     점수 : {score_x:.4f}")
        print(f"  판정       : {result}")
        print(f"  정답       : {expected}")
        print(f"  결과       : {pass_fail}")
        print(f"  평균 시간  : {avg_ms:.6f} ms")

        total += 1
        if pass_fail == "PASS":
            passed += 1
        else:
            failed += 1

    # 최종 요약
    print("\n" + "=" * 50)
    print(f"  총 {total}개 | ✅ PASS: {passed} | ❌ FAIL: {failed}")
    print("=" * 50)


# ── 모드 2: 수동 입력 검사 ──────────────────────────────────
def run_mode2(data: dict):
    """사용자가 직접 패턴을 입력해서 검사합니다"""

    print("\n" + "=" * 50)
    print("  모드 2: 수동 입력 검사")
    print("=" * 50)

    filters     = data["filters"]
    valid_sizes = sorted(filters.keys())   # [5, 13, 25]

    while True:
        # 1) 크기 선택
        n = get_size_input(valid_sizes)

        # 2) 행렬 입력
        grid = get_matrix_input(n)
        pat  = Pattern.load_from_list(grid)

        # 3) MAC 연산
        f_cross     = filters[n]["Cross"]
        f_x         = filters[n]["X"]
        score_cross = mac(f_cross, pat)
        score_x     = mac(f_x,     pat)

        # 4) 판정
        result = judge(score_cross, score_x)

        # 5) 성능 측정
        avg_ms = measure_performance(f_cross, pat, repeat=100)

        # 6) 결과 출력
        print(f"\n  Cross 점수 : {score_cross:.4f}")
        print(f"  X     점수 : {score_x:.4f}")
        print(f"  판정 결과  : {result}")
        print(f"  평균 시간  : {avg_ms:.6f} ms")

        # 7) 계속 여부
        again = input("\n  다시 입력하시겠습니까? (y/n): ").strip().lower()
        if again != "y":
            break


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
        print("  1. 자동 배치 검사 (data.json 전체 패턴)")
        print("  2. 수동 입력 검사 (직접 패턴 입력)")
        print("  3. 종료")
        print("-" * 50)

        choice = input("  선택 (1/2/3): ").strip()

        if choice == "1":
            run_mode1(data)
        elif choice == "2":
            run_mode2(data)
        elif choice == "3":
            print("\n  프로그램을 종료합니다. 수고하셨습니다! 👋")
            break
        else:
            print("  ⚠ 1, 2, 3 중 하나를 입력하세요.")


if __name__ == "__main__":
    main()