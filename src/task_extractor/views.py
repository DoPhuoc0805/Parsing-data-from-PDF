"""
Định hình và ghi dữ liệu ra file cho từng tầng.

- Tầng silver giữ dạng **phẳng**: 1 dòng = 1 nhiệm vụ, tiện join/lọc/phân tích.
- Tầng gold giữ dạng **gộp theo nhóm**: mỗi nhóm 1 object gồm tên nhóm, số
  hiệu nhóm, và mảng "data" chứa các nhiệm vụ con — đã bỏ 2 field
  "nhom_nhiem_vu"/"so_nhom_nhiem_vu" khỏi từng nhiệm vụ con vì đã có ở cấp
  nhóm, tránh lặp lại. Nhiệm vụ độc lập trở thành 1 nhóm chỉ có 1 phần tử.

CSV chỉ dùng ở tầng silver vì bảng phẳng không chứa được cấu trúc lồng nhau.
"""

from __future__ import annotations

import json
from pathlib import Path

GROUP_FIELDS = ("nhom_nhiem_vu", "so_nhom_nhiem_vu")


def group_tasks(tasks: list) -> list:
    """Gộp danh sách nhiệm vụ phẳng thành danh sách theo nhóm, giữ đúng thứ tự
    nhóm xuất hiện đầu tiên trong danh sách gốc."""
    groups = []
    group_by_key = {}

    for task in tasks:
        key = tuple(task.get(field) for field in GROUP_FIELDS)
        group = group_by_key.get(key)
        if group is None:
            group = {field: task.get(field) for field in GROUP_FIELDS}
            group["data"] = []
            group_by_key[key] = group
            groups.append(group)

        group["data"].append(
            {field: value for field, value in task.items() if field not in GROUP_FIELDS}
        )

    return groups


def write_json(data, output_path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_csv(rows: list, output_path) -> None:
    import pandas as pd

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
