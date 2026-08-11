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

from .profiles import PROFILES_BY_SUFFIX
from .read_excel import read_excel
from .read_pdf import read_pdf
from .tasks import build_tasks, detect_profile
from .views import group_tasks, write_csv, write_json

BRONZE = "bronze"
SILVER = "silver"
GOLD = "gold"

READERS = {
    ".pdf": read_pdf,
    ".xlsx": read_excel,
    ".xlsm": read_excel,
}


def _bronze_path(data_dir, name) -> Path:
    return Path(data_dir) / BRONZE / f"{name}.json"


def read_source(input_path: str) -> list:
    """Đọc file nguồn thành danh sách dòng thô, tự chọn cách đọc theo đuôi file."""
    suffix = Path(input_path).suffix.lower()
    reader = READERS.get(suffix)
    if reader is None:
        supported = ", ".join(sorted(READERS))
        raise ValueError(f"Chua ho tro dinh dang {suffix!r}; hien doc duoc: {supported}")
    return reader(input_path)


def run_pipeline(input_path: str, data_dir: str = "data", from_bronze: bool = False) -> list:
    """Chạy toàn bộ pipeline, ghi ra cả 3 tầng, trả về danh sách nhiệm vụ (silver)."""
    name = Path(input_path).stem
    suffix = Path(input_path).suffix.lower()

    if from_bronze:
        with open(_bronze_path(data_dir, name), encoding="utf-8") as f:
            rows = json.load(f)
    else:
        rows = read_source(input_path)
        write_json(rows, _bronze_path(data_dir, name))

    profile = detect_profile(rows, PROFILES_BY_SUFFIX[suffix])
    tasks = build_tasks(rows, profile)

    # Nguồn gốc chỉ tầng này biết; cần cho việc truy vết và để AI agent trích dẫn.
    for task in tasks:
        task["nguon_tai_lieu"] = Path(input_path).name
    write_csv(tasks, Path(data_dir) / SILVER / f"{name}.csv")
    write_json(tasks, Path(data_dir) / SILVER / f"{name}.json")
    write_json(group_tasks(tasks), Path(data_dir) / GOLD / f"{name}.json")

    return tasks
