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