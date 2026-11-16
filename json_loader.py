import json
from data_structure import Pattern

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
```
