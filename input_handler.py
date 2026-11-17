# input_handler.py

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