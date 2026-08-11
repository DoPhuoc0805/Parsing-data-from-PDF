"""Unit test cho views.py: gộp nhiệm vụ theo nhóm để xuất tầng gold."""

from pathlib import Path

from src.task_extractor.read_pdf import read_pdf
from src.task_extractor.tasks import build_tasks
from src.task_extractor.views import group_tasks

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
KH277_PDF = DATA_DIR / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"


def _kh277_grouped():
    return group_tasks(build_tasks(read_pdf(str(KH277_PDF))))


def test_group_tasks_groups_children_under_their_group():
    tasks = build_tasks(read_pdf(str(KH277_PDF)))
    grouped = group_tasks(tasks)

    assert sum(len(group["data"]) for group in grouped) == len(tasks)

    group_1 = next(g for g in grouped if g["so_nhom_nhiem_vu"] == "1")
    assert len(group_1["data"]) == 8
    assert all(t["ma_nhiem_vu"].startswith("1") for t in group_1["data"])
    for task in group_1["data"]:
        assert "nhom_nhiem_vu" not in task
        assert "so_nhom_nhiem_vu" not in task


def test_group_tasks_standalone_task_becomes_group_of_one():
    group_8 = next(g for g in _kh277_grouped() if g["so_nhom_nhiem_vu"] == "8")
    assert len(group_8["data"]) == 1
    assert group_8["data"][0]["ma_nhiem_vu"] == "8"


def test_group_tasks_preserves_group_order_of_first_appearance():
    numbers = [g["so_nhom_nhiem_vu"] for g in _kh277_grouped()]
    assert numbers == sorted(numbers, key=int)
