"""
Nối các tầng: raw -> bronze -> silver -> gold.

- bronze: dòng đọc được từ bảng, chưa diễn giải (dùng để chạy lại nhanh và
  để tách bạch lỗi "đọc sai" với lỗi "suy luận sai").
- silver: bảng phẳng, 1 dòng = 1 nhiệm vụ, đã kế thừa cột dùng chung.
- gold: JSON gộp theo nhóm nhiệm vụ, dành cho người đọc và AI agent.

Mọi tầng dùng chung tên file gốc (không đuôi) để truy vết 1 văn bản xuyên
suốt các tầng chỉ bằng tên.
"""

from __future__ import annotations

import json
from pathlib import Path

from .read_pdf import read_pdf
from .tasks import build_tasks
from .views import group_tasks, write_csv, write_json

BRONZE = "bronze"
SILVER = "silver"
GOLD = "gold"


def _bronze_path(data_dir, name) -> Path:
    return Path(data_dir) / BRONZE / f"{name}.json"


def read_source(input_path: str) -> list:
    """Đọc file nguồn thành danh sách dòng thô, chọn cách đọc theo đuôi file."""
    suffix = Path(input_path).suffix.lower()
    if suffix == ".pdf":
        return read_pdf(input_path)
    raise ValueError(f"Chua ho tro dinh dang {suffix!r} (input: {input_path})")


def run_pipeline(input_path: str, data_dir: str = "data", from_bronze: bool = False) -> list:
    """Chạy toàn bộ pipeline, ghi ra cả 3 tầng, trả về danh sách nhiệm vụ (silver)."""
    name = Path(input_path).stem

    if from_bronze:
        with open(_bronze_path(data_dir, name), encoding="utf-8") as f:
            rows = json.load(f)
    else:
        rows = read_source(input_path)
        write_json(rows, _bronze_path(data_dir, name))

    tasks = build_tasks(rows)
    write_csv(tasks, Path(data_dir) / SILVER / f"{name}.csv")
    write_json(tasks, Path(data_dir) / SILVER / f"{name}.json")
    write_json(group_tasks(tasks), Path(data_dir) / GOLD / f"{name}.json")

    return tasks
