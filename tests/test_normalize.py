"""Unit test cho normalize.py: loại dòng nhóm cha, kế thừa cột dùng chung."""

from pathlib import Path

from src.pdf_task_extractor.extract_tables import extract_from_pdf
from src.pdf_task_extractor.normalize import apply_group_inheritance

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
KH277_PDF = DATA_DIR / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
CV6582_PDF = DATA_DIR / "CV 6582.pdf"


def _normalized_kh277():
    return apply_group_inheritance(extract_from_pdf(str(KH277_PDF)))


def test_kh277_drops_exactly_the_pure_group_headers():
    raw = extract_from_pdf(str(KH277_PDF))
    normalized = apply_group_inheritance(raw)
    # 8 nhom co header thuan tuy (1,2,3,4,5,6,7,12) bi loai khoi ket qua.
    assert len(normalized) == len(raw) - 8


def test_group_with_shared_coordination_and_deadline_is_inherited():
    normalized = _normalized_kh277()
    children = [r for r in normalized if (r.get("nhom_nhiem_vu") or "").startswith("Làm sạch")]

    assert len(children) == 8
    for record in children:
        assert record["don_vi_phoi_hop"] == "Sở Khoa học và\nCông nghệ"
        assert record["thoi_han"] == "30/8/2026"

    # Don vi chu tri van rieng theo tung dong con, khong bi ghi de.
    chu_tri_values = {r["tt"]: r["don_vi_chu_tri"] for r in children}
    assert chu_tri_values["1"] == "Sở Tài chính"
    assert chu_tri_values["7"] == "Sở Y tế"


def test_group_with_shared_lead_unit_is_inherited():
    normalized = _normalized_kh277()
    record_32 = next(r for r in normalized if r["tt"] == "32")
    record_33 = next(r for r in normalized if r["tt"] == "33")

    expected_chu_tri = "Các Sở, ban, ngành;\nUBND các xã,\nphường"
    assert record_32["don_vi_chu_tri"] == expected_chu_tri
    assert record_33["don_vi_chu_tri"] == expected_chu_tri


def test_children_with_own_values_are_not_overwritten():
    normalized = _normalized_kh277()
    record_9 = next(r for r in normalized if r["tt"] == "9")
    record_10 = next(r for r in normalized if r["tt"] == "10")

    assert record_9["thoi_han"] == "30/7/2026"
    assert record_10["thoi_han"] == "30/8/2026"


def test_standalone_task_has_no_group_context():
    normalized = _normalized_kh277()
    record_28 = next(r for r in normalized if r["tt"] == "28")
    assert record_28["nhom_nhiem_vu"] is None
    assert record_28["don_vi_chu_tri"] == "Sở Văn hóa và\nThể thao"


def test_cv6582_records_unchanged_aside_from_group_field():
    raw = extract_from_pdf(str(CV6582_PDF))
    normalized = apply_group_inheritance(raw)

    assert len(normalized) == len(raw) == 12
    for original, result in zip(raw, normalized):
        assert result["nhom_nhiem_vu"] is None
        without_group_field = {k: v for k, v in result.items() if k != "nhom_nhiem_vu"}
        assert without_group_field == original
