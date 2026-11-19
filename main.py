# ============================================================
#  mini_npu.py  -  Mini NPU 시뮬레이터 (통합본)
#
#  [섹션 구성]
#   1. data_structure  : Pattern 클래스 (N×N → 1D float 리스트)
#   2. json_loader     : 라벨 정규화 + data.json 로딩
#   3. mac             : MAC(Multiply-Accumulate) 연산
#   4. judge           : epsilon 기반 판정 + PASS/FAIL
#   5. input_handler   : 사용자 입력 처리
#   6. performance     : 성능(시간) 측정  ※ 원본 미제공 → 새로 작성
#   7. main            : 모드 1/2 실행 + 메인 루프
#
#  실행: python mini_npu.py   (같은 폴더에 data.json 필요)
# ============================================================

import json
import time


# ============================================================
#  섹션 1. data_structure  (원본: data_structure.py)
# ============================================================
class Pattern:
    """
    N×N 2D 배열을 1D float 리스트로 관리하는 클래스
    """

    def __init__(self, n: int):
        self.n    = n
        self.data = [0.0] * (n * n)   # n×n 크기, 0.0으로 초기화

    def set(self, row: int, col: int, value: float):
        """(row, col) 위치에 값을 저장합니다"""
        index = row * self.n + col
        self.data[index] = float(value)

    def get(self, row: int, col: int) -> float:
        """(row, col) 위치의 값을 가져옵니다"""
        index = row * self.n + col
        return self.data[index]

    @classmethod
    def load_from_list(cls, grid: list) -> "Pattern":
        """2D 리스트를 받아서 Pattern 객체를 만듭니다"""
        n       = len(grid)
        pattern = cls(n)
        for r in range(n):
            for c in range(n):
                pattern.set(r, c, grid[r][c])
        return pattern

    def to_2d_list(self) -> list:
        """1D data를 2D 리스트로 변환 (확인용)"""
        return [
            [self.get(r, c) for c in range(self.n)]
            for r in range(self.n)
        ]

    def __repr__(self):
        return f"Pattern(n={self.n})"


# ============================================================
#  섹션 2. json_loader  (원본: json_loader.py)
# ============================================================

# ── 라벨 정규화 테이블 ──────────────────────────────────────
LABEL_MAP = {
    "+":      "Cross",
    "cross":  "Cross",
    "Cross":  "Cross",
    "CROSS":  "Cross",
    "x":      "X",
    "X":      "X",
}


def normalize_label(raw: str) -> str:
    """
    JSON의 다양한 라벨을 'Cross' 또는 'X' 로 통일합니다
    """
    label = LABEL_MAP.get(raw.strip())
    if label is None:
        raise ValueError(f"알 수 없는 라벨입니다: '{raw}'")
    return label


def load_data(filepath: str) -> dict:
    """
    data.json을 읽어서 filters와 patterns를 반환합니다

    반환 형식:
    {
        "filters": {
            5:  {"Cross": Pattern, "X": Pattern},
            13: {"Cross": Pattern, "X": Pattern},
            25: {"Cross": Pattern, "X": Pattern},
        },
        "patterns": [
            {"name": "size_5_1", "pattern": Pattern, "expected": "Cross"},
            ...
        ]
    }
    """
    # 1) 파일 읽기
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: '{filepath}'")

    # 2) filters 변환
    filters = {}
    for key, val in raw["filters"].items():
        # key 예시: "size_5" → n = 5
        n = int(key.split("_")[1])
        filters[n] = {
            "Cross": Pattern.load_from_list(val["cross"]),
            "X":     Pattern.load_from_list(val["x"]),
        }

    # 3) patterns 변환
    patterns = []
    for name, val in raw["patterns"].items():
        patterns.append({
            "name":     name,
            "pattern":  Pattern.load_from_list(val["input"]),
            "expected": normalize_label(val["expected"]),
        })

    return {"filters": filters, "patterns": patterns}


# ============================================================
#  섹션 3. mac  (원본: mac.py)
# ============================================================
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


# ============================================================
#  섹션 4. judge  (원본: judge.py)
# ============================================================
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


# ============================================================
#  섹션 5. input_handler  (원본: input_handler.py)
# ============================================================
def get_size_input(valid_sizes: list) -> int:
    """
    유효한 크기(5, 13, 25)를 입력받을 때까지 반복합니다
    """
    size_str = ", ".join(str(s) for s in valid_sizes)  # "5, 13, 25"

    while True:
        raw = input(f"\n  패턴 크기를 입력하세요 ({size_str}): ").strip()

        # 1) 숫자인지 확인
        if not raw.isdigit():
            print(f"  ⚠ 숫자를 입력하세요. (예: 5)")
            continue

        n = int(raw)

        # 2) 유효한 크기인지 확인
        if n not in valid_sizes:
            print(f"  ⚠ {size_str} 중 하나를 입력하세요.")
            continue

        return n


def get_matrix_input(n: int) -> list:
    """
    n×n 행렬을 한 줄씩 입력받습니다
    반환값: 2D 리스트 (float)
    """
    print(f"\n  {n}×{n} 행렬을 입력하세요.")
    print(f"  (한 줄에 {n}개 숫자를 공백으로 구분)")
    print(f"  예) 0 0 1 0 0")

    grid = []

    for r in range(n):
        while True:
            raw = input(f"  {r+1}행: ").strip()
            tokens = raw.split()

            # 1) 개수 확인
            if len(tokens) != n:
                print(f"  ⚠ {n}개의 숫자를 입력하세요. (현재 {len(tokens)}개)")
                continue

            # 2) 숫자인지 확인
            try:
                row = [float(t) for t in tokens]
            except ValueError:
                print(f"  ⚠ 숫자만 입력하세요.")
                continue

            grid.append(row)
            break

    return grid


# ============================================================
#  섹션 6. performance  (원본 파일 미제공 → 새로 작성)
#  main.py의 호출 방식에 맞춤:
#     measure_performance(filter_p, input_p, repeat=100) -> 평균 시간(ms)
#  이미 만들어 둔 performance.py가 있으면 이 섹션을 교체하세요.
# ============================================================
def measure_performance(filter_p: Pattern, input_p: Pattern, repeat: int = 100) -> float:
    """
    MAC 연산을 repeat회 반복 실행하여 1회 평균 시간(ms)을 반환합니다
    """
    mac(filter_p, input_p)                 # 워밍업 1회 (측정 제외)

    start = time.perf_counter()
    for _ in range(repeat):
        mac(filter_p, input_p)
    elapsed = time.perf_counter() - start

    return (elapsed / repeat) * 1000       # 초 → ms


# ============================================================
#  섹션 7. main  (원본: main.py)
# ============================================================

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