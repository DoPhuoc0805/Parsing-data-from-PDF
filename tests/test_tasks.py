"""Unit test cho tasks.py: loại dòng nhóm cha, kế thừa cột dùng chung."""

from pathlib import Path

from src.task_extractor.read_pdf import read_pdf
from src.task_extractor.tasks import build_tasks

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
KH277_PDF = DATA_DIR / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
CV6582_PDF = DATA_DIR / "CV 6582.pdf"


def _kh277_tasks():
    return build_tasks(read_pdf(str(KH277_PDF)))


def _by_ma(tasks, ma_nhiem_vu):
    return next(t for t in tasks if t["ma_nhiem_vu"] == ma_nhiem_vu)


def test_kh277_drops_exactly_the_pure_group_headers():
    rows = read_pdf(str(KH277_PDF))
    tasks = build_tasks(rows)
    # 8 nhom co header thuan tuy (1,2,3,4,5,6,7,12) bi loai khoi ket qua.
    assert len(tasks) == len(rows) - 8


def test_tt_and_chi_tiet_columns_are_removed():
    for task in _kh277_tasks():
        assert "tt" not in task
        assert "chi_tiet" not in task


def test_group_with_shared_coordination_and_deadline_is_inherited():
    children = [
        t for t in _kh277_tasks() if (t.get("nhom_nhiem_vu") or "").startswith("Làm sạch")
    ]

    assert len(children) == 8
    for task in children:
        assert task["don_vi_phoi_hop"] == "Sở Khoa học và Công nghệ"
        assert task["thoi_han"] == "30/8/2026"
        assert task["so_nhom_nhiem_vu"] == "1"

    # Don vi chu tri van rieng theo tung dong con, khong bi ghi de.
    assert _by_ma(children, "1a")["don_vi_chu_tri"] == "Sở Tài chính"
    assert _by_ma(children, "1g")["don_vi_chu_tri"] == "Sở Y tế"


def test_group_2_uses_its_own_group_number_not_global_tt():
    tasks = _kh277_tasks()
    # Cac dong con nay co "tt" toan cuc la 9,10 nhung phai dung so nhom cua no (2), khong phai 9/10.
    assert _by_ma(tasks, "2a")["ten_nhiem_vu"].startswith("Đối với khoảng 3,2 triệu")
    assert _by_ma(tasks, "2b")["ten_nhiem_vu"].startswith("Đối với khoảng 950.000")


def test_no_row_is_left_without_a_task_code():
    # Dong bi ngat trang (khong co tt/chi_tiet) da duoc gop lai o read_pdf,
    # nen sau buoc nay khong con dong nao thieu ma_nhiem_vu.
    assert all(t["ma_nhiem_vu"] is not None for t in _kh277_tasks())


def test_group_with_shared_lead_unit_is_inherited():
    tasks = _kh277_tasks()
    expected_chu_tri = "Các Sở, ban, ngành; UBND các xã, phường"
    assert _by_ma(tasks, "12a")["don_vi_chu_tri"] == expected_chu_tri
    assert _by_ma(tasks, "12b")["don_vi_chu_tri"] == expected_chu_tri


def test_children_with_own_values_are_not_overwritten():
    tasks = _kh277_tasks()
    assert _by_ma(tasks, "2a")["thoi_han"] == "30/7/2026"
    assert _by_ma(tasks, "2b")["thoi_han"] == "30/8/2026"


def test_standalone_task_uses_itself_as_its_own_group():
    task = _by_ma(_kh277_tasks(), "8")
    assert task["nhom_nhiem_vu"] == task["ten_nhiem_vu"]
    assert task["so_nhom_nhiem_vu"] == "8"
    assert task["don_vi_chu_tri"] == "Sở Văn hóa và Thể thao"


def test_wrapped_lines_are_rejoined_but_bullets_are_kept_separate():
    task = _by_ma(_kh277_tasks(), "4a")
    lines = task["san_pham"].split("\n")

    # 3 gach dau dong that su, moi gach lien mach khong con bi ngat giua dong.
    assert len(lines) == 3
    assert all(line.startswith("-") for line in lines)
    assert "thời gian giải quyết, 50% thành phần hồ sơ." in lines[-1]


_ADDED_FIELDS = ["nhom_nhiem_vu", "so_nhom_nhiem_vu", "ma_nhiem_vu"]
_DROPPED_FIELDS = ["tt", "chi_tiet"]


def test_cv6582_records_have_no_group_context():
    rows = read_pdf(str(CV6582_PDF))
    tasks = build_tasks(rows)

    assert len(tasks) == len(rows) == 12
    for task in tasks:
        assert all(task[field] is None for field in _ADDED_FIELDS)
        assert all(field not in task for field in _DROPPED_FIELDS)


def test_cv6582_wrapped_unit_names_are_rejoined():
    task = build_tasks(read_pdf(str(CV6582_PDF)))[0]
    # Ten don vi bi PDF wrap chu (vd "Sở KHCN,\nTập đoàn\nViettel") duoc noi lien.
    assert "\n" not in task["don_vi_phoi_hop"]
    assert task["don_vi_phoi_hop"] == "Sở KHCN, Tập đoàn Viettel"
