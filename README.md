Mini NPU 시뮬레이터 구현 가이드 🎓
📚 목차
이 프로젝트가 뭔가요?
핵심 개념 3가지
파일 구조
STEP별 코드 설명
data.json 읽는 법
전체 흐름 한눈에 보기
자주 하는 실수
테스트 체크리스트
1. 이 프로젝트가 뭔가요?
🤔 한 줄 요약
그림이 십자가(+) 모양인지, X 모양인지 판별하는 프로그램

🧠 AI가 그림을 인식하는 원리
AI가 그림을 인식할 때 "필터" 라는 도구를 사용합니다.


입력 패턴 (내가 그린 그림)     필터 (정답 모양 틀)
┌─────────────┐              ┌─────────────┐
│ 0  0  1  0  0 │            │ 0  0  1  0  0 │
│ 0  0  1  0  0 │    VS      │ 0  0  1  0  0 │
│ 1  1  1  1  1 │            │ 1  1  1  1  1 │
│ 0  0  1  0  0 │            │ 0  0  1  0  0 │
│ 0  0  1  0  0 │            │ 0  0  1  0  0 │
└─────────────┘              └─────────────┘
     내 그림                   Cross 필터
같은 위치의 숫자를 곱해서 더하면 → 점수가 나옵니다
점수가 높을수록 "더 비슷하다"는 뜻입니다!

2. 핵심 개념 3가지
개념 1️⃣ : MAC 연산이란?
MAC = Multiply(곱하기) + Accumulate(누적 더하기)

쉽게 말하면: "같은 위치끼리 곱하고, 다 더한다"


예시: 3×3 행렬

필터:          입력:          곱하기:
0  0  1        0  0  1        0×0  0×0  1×1
0  1  0   ×   0  1  0   =   0×0  1×1  0×0
1  0  0        1  0  0        1×1  0×0  0×0

결과: 0+0+1 + 0+1+0 + 1+0+0 = 3.0  ← 이게 MAC 점수!


개념 2️⃣ : 왜 필터가 필요한가?

Cross 필터로 계산 → Cross 점수: 9.0
X 필터로 계산     → X 점수:     1.0

9.0 > 1.0 이므로 → "이 그림은 Cross입니다!"
필터는 "이 모양이 맞으면 점수를 높게 주는 채점표" 입니다.

개념 3️⃣ : 라벨 정규화란?
JSON 파일에는 "+", "x" 처럼 다양하게 쓰여 있습니다.
프로그램 안에서는 통일된 이름을 써야 합니다.


JSON에 있는 값    →    프로그램 안에서 쓰는 값
"+"              →    "Cross"
"cross"          →    "Cross"
"x"              →    "X"
"X"              →    "X"


3. 파일 구조

mini_npu/
│
├── main.py              ← 프로그램 시작점 (여기서 실행!)
├── data_structure.py    ← Pattern 클래스 (데이터 저장 방식)
├── mac.py               ← MAC 연산 함수
├── judge.py             ← 점수 비교 → 판정
├── input_handler.py     ← 사용자 입력 처리
├── json_loader.py       ← data.json 읽기
├── performance.py       ← 실행 시간 측정
└── data.json            ← 테스트 데이터
💡 파일을 만드는 순서: data_structure → mac → judge → input_handler → json_loader → performance → main


4. STEP별 코드 설명
STEP 1: data_structure.py - 데이터 저장 방식
🤔 왜 이게 필요한가요?
5×5 행렬을 저장할 때 2D 리스트를 쓰면 편하지만,
실제 NPU 하드웨어는 1D(일렬)로 메모리에 저장합니다.
이 클래스는 그 방식을 흉내냅니다.

📐 2D → 1D 변환 원리

2D 행렬:              1D 리스트:
[1, 2, 3]            [1, 2, 3, 4, 5, 6, 7, 8, 9]
[4, 5, 6]     →       ↑           ↑           ↑
[7, 8, 9]           row=0       row=1       row=2

위치 계산 공식: index = row × n + col
예) row=1, col=2, n=3 → index = 1×3+2 = 5 → 값: 6


💻 코드

# data_structure.py

class Pattern:
    """
    N×N 2D 배열을 1D float 리스트로 관리하는 클래스
    """

    def __init__(self, n: int):
        # n: 행렬의 크기 (예: 5이면 5×5)
        self.n = n
        # n×n 크기의 1D 리스트를 0.0으로 초기화
        self.data = [0.0] * (n * n)

    def set(self, row: int, col: int, value: float):
        """(row, col) 위치에 값을 저장합니다"""
        # 2D 위치 → 1D 인덱스 변환
        index = row * self.n + col
        self.data[index] = float(value)

    def get(self, row: int, col: int) -> float:
        """(row, col) 위치의 값을 가져옵니다"""
        index = row * self.n + col
        return self.data[index]

    @classmethod
    def load_from_list(cls, grid: list) -> "Pattern":
        """
        2D 리스트를 받아서 Pattern 객체를 만듭니다
        
        사용 예시:
        grid = [[0, 1], [1, 0]]
        p = Pattern.load_from_list(grid)
        """
        n = len(grid)           # 행 개수 = 크기
        pattern = cls(n)        # Pattern 객체 생성
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


✅ 테스트 해보기

# 터미널에서 python 실행 후 테스트

p = Pattern(3)
p.set(0, 0, 1.0)   # 0행 0열에 1.0 저장
p.set(1, 1, 1.0)   # 1행 1열에 1.0 저장
print(p.get(0, 0)) # 출력: 1.0
print(p.get(0, 1)) # 출력: 0.0

# load_from_list 테스트
grid = [[1, 0], [0, 1]]
p2 = Pattern.load_from_list(grid)
print(p2.to_2d_list())  # 출력: [[1.0, 0.0], [0.0, 1.0]]


STEP 2: mac.py - 핵심 연산
🤔 이 함수가 하는 일

filter의 각 위치 값  ×  input의 같은 위치 값  →  다 더하기

💻 코드
# mac.py

from data_structure import Pattern

def mac(filter_p: Pattern, input_p: Pattern) -> float:
    """
    MAC(Multiply-Accumulate) 연산
    
    filter_p: 필터 Pattern 객체
    input_p : 입력 Pattern 객체
    반환값  : 두 행렬의 원소별 곱의 합 (float)
    """
    # 크기가 다르면 계산 불가
    if filter_p.n != input_p.n:
        raise ValueError(
            f"크기가 달라요! filter={filter_p.n}, input={input_p.n}"
        )

    n = filter_p.n
    result = 0.0  # 누적 합산 변수

    # 이중 for문으로 모든 위치를 순회
    for r in range(n):
        for c in range(n):
            # 같은 위치의 값을 곱해서 result에 더함
            result += filter_p.get(r, c) * input_p.get(r, c)

    return result


✅ 손으로 계산해서 확인하기

Cross 필터 (5×5):          Cross 패턴 입력:
0  0  1  0  0              0  0  1  0  0
0  0  1  0  0              0  0  1  0  0
1  1  0.9 1  1     ×       1  1  1  1  1
0  0  1  0  0              0  0  1  0  0
0  0  1  0  0              0  0  1  0  0

계산:
- (0,2): 1×1 = 1.0
- (1,2): 1×1 = 1.0
- (2,0): 1×1 = 1.0
- (2,1): 1×1 = 1.0
- (2,2): 0.9×1 = 0.9  ← 중심은 0.9!
- (2,3): 1×1 = 1.0
- (2,4): 1×1 = 1.0
- (3,2): 1×1 = 1.0
- (4,2): 1×1 = 1.0
나머지는 모두 0

합계 = 8.9  ← Cross 점수


STEP 3: judge.py - 판정
🤔 이 함수가 하는 일

Cross 점수 vs X 점수 비교
→ 높은 쪽이 이긴다!
→ 같으면 UNDECIDED (판정 불가)

💻 코드
# judge.py

def judge(score_cross: float, score_x: float, epsilon: float = 1e-9) -> str:
    """
    두 점수를 비교해 판정 결과를 반환합니다
    
    score_cross : Cross 필터로 계산한 점수
    score_x     : X 필터로 계산한 점수
    epsilon     : 동점 판정 기준 (매우 작은 수)
    
    반환값: 'Cross', 'X', 'UNDECIDED' 중 하나
    """
    diff = score_cross - score_x

    # abs()는 절댓값 함수
    # 두 점수 차이가 아주 작으면 동점으로 봄
    if abs(diff) < epsilon:
        return "UNDECIDED"
    elif diff > 0:
        return "Cross"   # Cross 점수가 더 높음
    else:
        return "X"       # X 점수가 더 높음


def check_pass_fail(judge_result: str, expected_label: str) -> str:
    """
    판정 결과와 정답을 비교해 PASS/FAIL을 반환합니다
    
    judge_result  : judge() 함수의 반환값
    expected_label: 정규화된 정답 라벨 ('Cross' 또는 'X')
    
    반환값: 'PASS' 또는 'FAIL'
    """
    if judge_result == "UNDECIDED":
        return "FAIL"   # 판정 못하면 무조건 FAIL
    elif judge_result == expected_label:
        return "PASS"   # 정답과 일치
    else:
        return "FAIL"   # 정답과 불일치

✅ 판정 흐름 예시

예시 1) Cross 패턴 입력
  Cross 점수: 8.9
  X 점수    : 0.0
  → judge()  : "Cross"
  → 정답     : "Cross"
  → PASS ✅

예시 2) 애매한 패턴 입력
  Cross 점수: 3.0
  X 점수    : 3.0
  → judge()  : "UNDECIDED"
  → FAIL ❌


STEP 4: input_handler.py - 사용자 입력
🤔 이 함수가 하는 일

사용자가 숫자를 잘못 입력해도 프로그램이 죽지 않고
"다시 입력하세요"라고 안내합니다.

#### 💻 코드

```python
# input_handler.py

def get_size_input(valid_sizes: list) -> int:
    """
    사용자로부터 패턴 크기(N)를 입력받습니다
    
    valid_sizes: 허용되는 크기 목록 (예: [5, 13, 25])
    반환값     : 선택한 크기 (int)
    
    잘못 입력하면 다시 물어봅니다
    """
    while True:  # 올바른 입력이 들어올 때까지 반복
        raw = input(f"패턴 크기를 입력하세요 {valid_sizes}: ").strip()
        try:
            n = int(raw)  # 문자열 → 정수 변환 시도
            if n in valid_sizes:
                return n  # 올바른 값이면 반환
            else:
                print(f"  ⚠ {valid_sizes} 중 하나를 입력하세요.")
        except ValueError:
            # int() 변환 실패 시 (예: "abc" 입력)
            print("  ⚠ 숫자(정수)를 입력하세요.")


def get_matrix_input(n: int) -> list:
    """
    사용자로부터 n×n 행렬을 입력받습니다
    
    n      : 행렬 크기
    반환값 : 2D 리스트 (float)
    
    입력 예시 (5×5):
      행 1/5: 1.0 0.0 0.0 0.0 1.0
      행 2/5: 0.0 1.0 0.0 1.0 0.0
      ...
    """
    print(f"\n{n}×{n} 행렬을 입력하세요.")
    print(f"각 행마다 공백으로 구분해서 {n}개 숫자를 입력하세요.")
    print(f"예시: 1.0 0.0 0.0 0.0 1.0\n")

    grid = []
    r = 0
    while r < n:  # n개 행을 모두 입력받을 때까지 반복
        raw = input(f"  행 {r+1}/{n}: ").strip()
        try:
            # 공백으로 나눠서 각각 float으로 변환
            row = [float(x) for x in raw.split()]

            if len(row) != n:
                # 숫자 개수가 맞지 않으면 재입력
                print(f"  ⚠ {n}개의 숫자가 필요합니다. "
                      f"(지금 입력: {len(row)}개) 다시 입력하세요.")
                continue  # r을 증가시키지 않고 다시 입력받음

            grid.append(row)
            r += 1  # 성공적으로 입력받으면 다음 행으로

        except ValueError:
            # float() 변환 실패 시 (예: "a b c" 입력)
            print("  ⚠ 숫자만 입력 가능합니다. 다시 입력하세요.")

    return grid


✅ 입력 흐름 예시

패턴 크기를 입력하세요 [5, 13, 25]: abc
  ⚠ 숫자(정수)를 입력하세요.
패턴 크기를 입력하세요 [5, 13, 25]: 7
  ⚠ [5, 13, 25] 중 하나를 입력하세요.
패턴 크기를 입력하세요 [5, 13, 25]: 5   ← 올바른 입력!

5×5 행렬을 입력하세요.
  행 1/5: 1.0 0.0        ← 숫자 부족!
  ⚠ 5개의 숫자가 필요합니다. (지금 입력: 2개) 다시 입력하세요.
  행 1/5: 1.0 0.0 0.0 0.0 1.0   ← 올바른 입력!
  행 2/5: ...


STEP 5: json_loader.py - JSON 파일 읽기

🤔 data.json 구조 다시 보기

data.json
├── filters
│   ├── size_5
│   │   ├── cross  ← 5×5 Cross 필터
│   │   └── x      ← 5×5 X 필터
│   ├── size_13
│   │   ├── cross  ← 13×13 Cross 필터
│   │   └── x      ← 13×13 X 필터
│   └── size_25
│       ├── cross  ← 25×25 Cross 필터
│       └── x      ← 25×25 X 필터
└── patterns
    ├── size_5_1   → expected: "x"  (정규화 후 "X")
    ├── size_5_2   → expected: "+"  (정규화 후 "Cross")
    ├── size_13_1  → expected: "x"
    ├── size_13_2  → expected: "+"
    ├── size_25_1  → expected: "x"
    └── size_25_2  → expected: "+"
🔑 키 이름에서 숫자 추출하는 법

# "size_5"  → split("_") → ["size", "5"]  → [1] → "5" → int → 5
# "size_13" → split("_") → ["size", "13"] → [1] → "13" → int → 13
# "size_25" → split("_") → ["size", "25"] → [1] → "25" → int → 25

size_key = "size_13"
n = int(size_key.split("_")[1])  # → 13

💻 코드

# json_loader.py

import json
from data_structure import Pattern

# ── 라벨 정규화 테이블 ──────────────────────────
# JSON에 있는 다양한 표현을 통일된 이름으로 바꿉니다
LABEL_MAP = {
    "+":     "Cross",
    "cross": "Cross",
    "Cross": "Cross",
    "CROSS": "Cross",
    "x":     "X",
    "X":     "X",
}


def normalize_label(raw: str) -> str:
    """
    다양한 라벨을 'Cross' 또는 'X'로 정규화합니다
    
    예시:
      normalize_label("+")     → "Cross"
      normalize_label("cross") → "Cross"
      normalize_label("x")     → "X"
    """
    result = LABEL_MAP.get(raw)
    if result is None:
        raise ValueError(f"알 수 없는 라벨입니다: '{raw}'")
    return result


def load_data(filepath: str = "data.json") -> dict:
    """
    data.json을 읽어서 필터와 패턴을 반환합니다
    
    반환 형식:
    {
        "filters": {
            5:  {"Cross": Pattern객체, "X": Pattern객체},
            13: {"Cross": Pattern객체, "X": Pattern객체},
            25: {"Cross": Pattern객체, "X": Pattern객체},
        },
        "patterns": [
            {
                "name"    : "size_5_1",
                "n"       : 5,
                "pattern" : Pattern객체,
                "expected": "X"          ← 정규화된 라벨
            },
            ...
        ]
    }
    """
    # ── JSON 파일 열기 ──────────────────────────
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)  # JSON → 파이썬 딕셔너리
    except FileNotFoundError:
        raise FileNotFoundError(
            f"파일을 찾을 수 없습니다: '{filepath}'\n"
            f"main.py와 같은 폴더에 data.json이 있는지 확인하세요."
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 형식이 잘못되었습니다: {e}")

    # ── 필터 로드 ───────────────────────────────
    filters = {}

    for size_key, shape_dict in raw["filters"].items():
        # "size_5" → 5, "size_13" → 13, "size_25" → 25
        n = int(size_key.split("_")[1])
        filters[n] = {}

        for shape_key, grid in shape_dict.items():
            # shape_key: "cross" 또는 "x"
            # grid: 2D 리스트 (JSON에서 읽은 값)
            label = normalize_label(shape_key)  # "cross" → "Cross"
            filters[n][label] = Pattern.load_from_list(grid)

    # ── 패턴 로드 ───────────────────────────────
    patterns = []

    for pat_name, pat_data in raw["patterns"].items():
        # "size_5_1"  → split("_") → ["size","5","1"] → [1] → 5
        # "size_13_2" → split("_") → ["size","13","2"] → [1] → 13
        n = int(pat_name.split("_")[1])

        pattern_obj = Pattern.load_from_list(pat_data["input"])
        expected    = normalize_label(pat_data["expected"])

        patterns.append({
            "name"    : pat_name,
            "n"       : n,
            "pattern" : pattern_obj,
            "expected": expected,
        })

    return {"filters": filters, "patterns": patterns}


✅ 로드 결과 확인하기

# 터미널에서 테스트
from json_loader import load_data

data = load_data("data.json")

# 필터 확인
print(data["filters"].keys())       # dict_keys([5, 13, 25])
print(data["filters"][5]["Cross"])  # Pattern(n=5)

# 패턴 확인
for p in data["patterns"]:
    print(p["name"], p["n"], p["expected"])

# 출력 예시:
# size_5_1  5  X
# size_5_2  5  Cross
# size_13_1 13 X
# size_13_2 13 Cross
# size_25_1 25 X
# size_25_2 25 Cross


STEP 6: performance.py - 실행 시간 측정
🤔 왜 시간을 측정하나요?
NPU(Neural Processing Unit)는 속도가 중요합니다.
같은 연산을 여러 번 반복해서 평균 시간을 구합니다.


repeat=100 이면:
MAC 연산을 100번 실행 → 총 시간 ÷ 100 = 평균 시간(ms)
💻 코드

# performance.py

import time
from data_structure import Pattern
from mac import mac


def measure_performance(
    filter_p: Pattern,
    input_p : Pattern,
    repeat  : int = 100
) -> float:
    """
    MAC 연산을 repeat번 반복해서 평균 실행 시간을 반환합니다
    
    filter_p : 필터 Pattern 객체
    input_p  : 입력 Pattern 객체
    repeat   : 반복 횟수 (기본값: 100)
    반환값   : 평균 실행 시간 (밀리초, ms)
    
    예시:
      avg_ms = measure_performance(f_cross, pat, repeat=100)
      print(f"{avg_ms:.6f} ms")  → 0.002341 ms
    """
    start = time.perf_counter()  # 시작 시간 기록

    for _ in range(repeat):
        mac(filter_p, input_p)   # repeat번 반복 실행

    end = time.perf_counter()    # 종료 시간 기록

    total_sec = end - start                  # 총 걸린 시간 (초)
    avg_ms    = (total_sec / repeat) * 1000  # 평균 시간 (밀리초)

    return avg_ms


STEP 7: main.py - 전체 통합
🤔 main.py가 하는 일

프로그램 시작
    ↓
모드 선택 화면 출력
    ↓
모드 1 선택 → JSON 패턴 자동 검사
모드 2 선택 → 사용자가 직접 입력해서 검사
모드 3 선택 → 종료

💻 코드

# main.py

from json_loader   import load_data
from data_structure import Pattern
from mac            import mac
from judge          import judge, check_pass_fail
from input_handler  import get_matrix_input, get_size_input
from performance    import measure_performance


# ── 모드 1: JSON 자동 검사 ──────────────────────────────────
def run_mode1(data: dict):
    """data.json의 모든 패턴을 자동으로 검사합니다"""

    print("\n" + "=" * 50)
    print("  모드 1: 자동 배치 검사")
    print("=" * 50)

    filters  = data["filters"]
    patterns = data["patterns"]

    total  = 0
    passed = 0
    failed = 0

    for item in patterns:
        name     = item["name"]
        n        = item["n"]
        pat      = item["pattern"]
        expected = item["expected"]

        # 해당 크기의 필터가 없으면 건너뜀
        if n not in filters:
            print(f"[{name}] ⚠ 크기 {n}에 맞는 필터 없음 → SKIP")
            continue

        f_cross = filters[n]["Cross"]
        f_x     = filters[n]["X"]

        # MAC 연산으로 점수 계산
        score_cross = mac(f_cross, pat)
        score_x     = mac(f_x,     pat)

        # 판정
        result    = judge(score_cross, score_x)
        pass_fail = check_pass_fail(result, expected)

        # 성능 측정
        avg_ms = measure_performance(f_cross, pat, repeat=100)

        # 결과 출력
        print(f"\n[{name}]")
        print(f"  크기       : {n}×{n}")
        print(f"  Cross 점수 : {score_cross:.4f}")
        print(f"  X 점수     : {score_x:.4f}")
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
    valid_sizes = sorted(filters.keys())  # [5, 13, 25]

    while True:
        # 1) 크기 선택
        n = get_size_input(valid_sizes)

        # 2) 행렬 입력
        grid = get_matrix_input(n)
        pat  = Pattern.load_from_list(grid)

        # 3) MAC 연산
        f_cross = filters[n]["Cross"]
        f_x     = filters[n]["X"]

        score_cross = mac(f_cross, pat)
        score_x     = mac(f_x,     pat)

        # 4) 판정
        result = judge(score_cross, score_x)

        # 5) 성능 측정
        avg_ms = measure_performance(f_cross, pat, repeat=100)

        # 6) 결과 출력
        print(f"\n  Cross 점수 : {score_cross:.4f}")
        print(f"  X 점수     : {score_x:.4f}")
        print(f"  판정 결과  : {result}")
        print(f"  평균 시간  : {avg_ms:.6f} ms")

        # 7) 계속 할지 물어보기
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
            print("\n프로그램을 종료합니다. 수고하셨습니다! 👋")
            break
        else:
            print("  ⚠ 1, 2, 3 중 하나를 입력하세요.")


# ── 프로그램 시작점 ─────────────────────────────────────────
if __name__ == "__main__":
    main()

5. data.json 읽는 법
📄 실제 JSON 구조와 코드 연결

data.json                          파이썬 코드
─────────────────────────────────────────────────────
{
  "filters": {
    "size_5": {                 →  filters[5]
      "cross": [[...], ...]    →  filters[5]["Cross"]  (Pattern 객체)
      "x":     [[...], ...]    →  filters[5]["X"]      (Pattern 객체)
    },
    "size_13": { ... }         →  filters[13]
    "size_25": { ... }         →  filters[25]
  },
  "patterns": {
    "size_5_1": {              →  patterns[0]
      "input":    [[...], ...] →  patterns[0]["pattern"]  (Pattern 객체)
      "expected": "x"          →  patterns[0]["expected"] = "X" (정규화)
    },
    ...
  }
}


🔄 라벨 정규화 흐름

JSON 값    normalize_label()    프로그램 내부
─────────────────────────────────────────────
"+"      ──────────────────→   "Cross"
"cross"  ──────────────────→   "Cross"
"x"      ──────────────────→   "X"
"X"      ──────────────────→   "X"


6. 전체 흐름 한눈에 보기

프로그램 시작 (main.py)
        │
        ▼
data.json 로드 (json_loader.py)
  ├── filters  → Pattern 객체로 변환
  └── patterns → Pattern 객체로 변환
        │
        ▼
모드 선택
  ├── 모드 1: 자동 검사
  │     │
  │     ▼
  │   패턴 하나씩 꺼내기
  │     │
  │     ▼
  │   MAC 연산 (mac.py)
  │   ├── score_cross = mac(f_cross, pat)
  │   └── score_x     = mac(f_x,     pat)
  │     │
  │     ▼
  │   판정 (judge.py)
  │   ├── judge()          → "Cross" / "X" / "UNDECIDED"
  │   └── check_pass_fail() → "PASS" / "FAIL"
  │     │
  │     ▼
  │   성능 측정 (performance.py)
  │   └── measure_performance() → 평균 ms
  │     │
  │     ▼
  │   결과 출력
  │
  └── 모드 2: 수동 검사
        │
        ▼
      크기 입력 (input_handler.py)
        │
        ▼
      행렬 입력 (input_handler.py)
        │
        ▼
      MAC → 판정 → 성능 측정 → 결과 출력
        │
        ▼
      다시 할지 선택


7. 자주 하는 실수
❌ 실수 1: 파일 위치 오류
오류 메시지:
  FileNotFoundError: 파일을 찾을 수 없습니다: 'data.json'

원인:
  main.py와 data.json이 다른 폴더에 있음

해결:
  mini_npu/
  ├── main.py       ← 여기서 실행
  ├── data.json     ← 같은 폴더에 있어야 함
  └── ...

❌ 실수 2: import 오류
오류 메시지:
  ModuleNotFoundError: No module named 'data_structure'

원인:
  파일 이름이 다르거나 같은 폴더에 없음

해결:
  모든 .py 파일이 같은 폴더에 있는지 확인
  파일 이름 오타 확인 (data_structure.py ← 언더바!)

❌ 실수 3: 크기 불일치 오류
오류 메시지:
  ValueError: 크기가 달라요! filter=5, input=13

원인:
  5×5 필터로 13×13 패턴을 계산하려 함

해결:
  패턴의 n값과 필터의 n값이 같은지 확인
  json_loader.py에서 n을 올바르게 추출했는지 확인

❌ 실수 4: 라벨 오류
오류 메시지:
  ValueError: 알 수 없는 라벨입니다: 'Cross Shape'

원인:
  LABEL_MAP에 없는 라벨이 JSON에 있음

해결:
  LABEL_MAP에 해당 라벨 추가
  예) "Cross Shape": "Cross"

❌ 실수 5: 외부 라이브러리 사용
# ❌ 금지! numpy 사용
import numpy as np
result = np.dot(filter_arr, input_arr)

# ✅ 올바른 방법: 이중 for문 사용
result = 0.0
for r in range(n):
    for c in range(n):
        result += filter_p.get(r, c) * input_p.get(r, c)


8. 테스트 체크리스트
📋 제출 전 확인 사항

파일 구조 확인
  □ data_structure.py 있음
  □ mac.py 있음
  □ judge.py 있음
  □ input_handler.py 있음
  □ json_loader.py 있음
  □ performance.py 있음
  □ main.py 있음
  □ data.json 있음

기능 확인
  □ 모드 1 실행 시 6개 패턴 모두 출력됨
  □ 모드 1 실행 시 PASS/FAIL 결과 나옴
  □ 모드 2 실행 시 잘못된 크기 입력해도 재입력 요청함
  □ 모드 2 실행 시 잘못된 행렬 입력해도 재입력 요청함
  □ 모드 3 선택 시 프로그램 종료됨
  □ 평균 실행 시간(ms)이 출력됨

코드 규칙 확인
  □ numpy, scipy 등 외부 라이브러리 미사용
  □ MAC 연산에 이중 for문 사용
  □ Pattern 클래스의 1D 리스트 사용


🖥️ 예상 실행 결과 (모드 1)

==================================================
   Mini NPU 시뮬레이터
==================================================

data.json 로딩 중...
✅ 로딩 완료!

--------------------------------------------------
  모드를 선택하세요
  1. 자동 배치 검사 (data.json 전체 패턴)
  2. 수동 입력 검사 (직접 패턴 입력)
  3. 종료
--------------------------------------------------
  선택 (1/2/3): 1

==================================================
  모드 1: 자동 배치 검사
==================================================

[size_5_1]
  크기       : 5×5
  Cross 점수 : 0.0000
  X 점수     : 8.9000
  판정       : X
  정답       : X
  결과       : PASS ✅
  평균 시간  : 0.002341 ms

[size_5_2]
  크기       : 5×5
  Cross 점수 : 8.9000
  X 점수     : 0.0000
  판정       : Cross
  정답       : Cross
  결과       : PASS ✅
  평균 시간  : 0.002187 ms

...

==================================================
  총 6개 | ✅ PASS: 6 | ❌ FAIL: 0
==================================================
💪 여기까지 완성했다면 Mini NPU 시뮬레이터 구현 완료입니다!
막히는 부분이 있으면 각 STEP의 테스트 해보기 섹션을 먼저 실행해보세요.
작은 단위로 테스트하면 오류를 빠르게 찾을 수 있습니다! 🎉


---

전체 `.md` 파일이 완성되었습니다! 🎉

## 📌 파일 저장 방법
파일 이름: mini_npu_guide.md
저장 위치: mini_npu/ 폴더 안 (다른 .py 파일들과 같은 위치)


## 📌 이 가이드의 구성 요약

| 섹션 | 내용 |
|------|------|
| 1~2장 | 프로젝트 개념 + 핵심 원리 3가지 |
| 3장 | 파일 구조 + 작성 순서 |
| 4장 | 7개 파일 코드 + 상세 설명 |
| 5장 | data.json 구조 연결 방법 |
| 6장 | 전체 흐름 다이어그램 |
| 7장 | 자주 하는 실수 5가지 |
| 8장 | 제출 전 체크리스트 |
