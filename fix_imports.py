"""Script tự động thêm import pandas vào các file cần"""
from pathlib import Path

FILES = [
    "modules/charts.py",
    "modules/metrics.py",
    "modules/exporter.py",
]

for f in FILES:
    p = Path(f)
    if not p.exists():
        print(f"[SKIP] {f} không tồn tại")
        continue

    content = p.read_text(encoding="utf-8")

    if "import pandas as pd" in content:
        print(f"[OK] {f} đã có pandas")
        continue

    # Thêm import pandas sau dòng docstring đầu tiên
    lines = content.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('"""') and i > 0:
            # tìm dòng kết thúc docstring
            for j in range(i + 1, len(lines)):
                if '"""' in lines[j]:
                    insert_idx = j + 1
                    break
            break
        elif not line.strip().startswith('"""') and line.strip():
            insert_idx = i
            break

    lines.insert(insert_idx, "import pandas as pd")
    p.write_text("\n".join(lines), encoding="utf-8")
    print(f"[FIX] Đã thêm pandas vào {f}")