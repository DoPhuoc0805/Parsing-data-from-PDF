"""Unit test cho normalize.py: loại dòng nhóm cha, kế thừa cột dùng chung."""

from pathlib import Path

from src.pdf_task_extractor.extract_tables import extract_from_pdf
from src.pdf_task_extractor.normalize import apply_group_inheritance

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
KH277_PDF = DATA_DIR / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
CV6582_PDF = DATA_DIR / "CV 6582.pdf"


def _normalized_kh277():
    return apply_group_inheritance(extract_from_pdf(str(KH277_PDF)))


def _by_ma(records, ma_nhiem_vu):
    return next(r for r in records if r["ma_nhiem_vu"] == ma_nhiem_vu)


def test_kh277_drops_exactly_the_pure_group_headers():
    raw = extract_from_pdf(str(KH277_PDF))
    normalized = apply_group_inheritance(raw)
    # 8 nhom co header thuan tuy (1,2,3,4,5,6,7,12) bi loai khoi ket qua.
    assert len(normalized) == len(raw) - 8


def test_tt_and_chi_tiet_columns_are_removed():
    normalized = _normalized_kh277()
    for record in normalized:
        assert "tt" not in record
        assert "chi_tiet" not in record


def test_group_with_shared_coordination_and_deadline_is_inherited():
    normalized = _normalized_kh277()
    children = [r for r in normalized if (r.get("nhom_nhiem_vu") or "").startswith("Làm sạch")]

    assert len(children) == 8
    for record in children:
        assert record["don_vi_phoi_hop"] == "Sở Khoa học và Công nghệ"
        assert record["thoi_han"] == "30/8/2026"
        assert record["nhom_so_thu_tu"] == "1"

    # Don vi chu tri van rieng theo tung dong con, khong bi ghi de.
    assert _by_ma(children, "1a")["don_vi_chu_tri"] == "Sở Tài chính"
    assert _by_ma(children, "1g")["don_vi_chu_tri"] == "Sở Y tế"


def test_group_2_uses_its_own_group_number_not_global_tt():
    normalized = _normalized_kh277()
    # Cac dong con nay co "tt" toan cuc la 9,10 nhung phai dung so nhom cua no (2), khong phai 9/10.
    assert _by_ma(normalized, "2a")["ten_nhiem_vu"].startswith("Đối với khoảng 3,2 triệu")
    assert _by_ma(normalized, "2b")["ten_nhiem_vu"].startswith("Đối với khoảng 950.000")


def test_no_row_is_left_without_a_task_code():
    # Dong bi ngat trang (khong co tt/chi_tiet) da duoc gop lai o extract_tables,
    # nen sau normalize khong con dong nao thieu ma_nhiem_vu.
    normalized = _normalized_kh277()
    assert all(r["ma_nhiem_vu"] is not None for r in normalized)


def test_group_with_shared_lead_unit_is_inherited():
    normalized = _normalized_kh277()
    expected_chu_tri = "Các Sở, ban, ngành; UBND các xã, phường"
    assert _by_ma(normalized, "12a")["don_vi_chu_tri"] == expected_chu_tri
    assert _by_ma(normalized, "12b")["don_vi_chu_tri"] == expected_chu_tri


def test_children_with_own_values_are_not_overwritten():
    normalized = _normalized_kh277()
    assert _by_ma(normalized, "2a")["thoi_han"] == "30/7/2026"
    assert _by_ma(normalized, "2b")["thoi_han"] == "30/8/2026"


def test_standalone_task_uses_itself_as_its_own_group():
    normalized = _normalized_kh277()
    record = _by_ma(normalized, "8")
    assert record["nhom_nhiem_vu"] == record["ten_nhiem_vu"]
    assert record["nhom_so_thu_tu"] == "8"
    assert record["don_vi_chu_tri"] == "Sở Văn hóa và Thể thao"


def test_wrapped_lines_are_rejoined_but_bullets_are_kept_separate():
    normalized = _normalized_kh277()
    record = _by_ma(normalized, "4a")
    lines = record["san_pham"].split("\n")

    # 3 gach dau dong that su, moi gach lien mach khong con bi ngat giua dong.
    assert len(lines) == 3
    assert all(line.startswith("-") for line in lines)
    assert "thời gian giải quyết, 50% thành phần hồ sơ." in lines[-1]


_ADDED_FIELDS = ["nhom_nhiem_vu", "nhom_so_thu_tu", "ma_nhiem_vu"]
_DROPPED_FIELDS = ["tt", "chi_tiet"]


def test_cv6582_records_have_no_group_context():
    raw = extract_from_pdf(str(CV6582_PDF))
    normalized = apply_group_inheritance(raw)

    assert len(normalized) == len(raw) == 12
    for result in normalized:
        assert all(result[field] is None for field in _ADDED_FIELDS)
        assert all(field not in result for field in _DROPPED_FIELDS)


def test_cv6582_wrapped_unit_names_are_rejoined():
    normalized = apply_group_inheritance(extract_from_pdf(str(CV6582_PDF)))
    record = normalized[0]
    # Ten don vi bi PDF wrap chu (vd "Sở KHCN,\nTập đoàn\nViettel") duoc noi lien.
    assert "\n" not in record["don_vi_phoi_hop"]
    assert record["don_vi_phoi_hop"] == "Sở KHCN, Tập đoàn Viettel"
