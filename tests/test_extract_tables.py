"""Unit test cho extract_tables.py trên cả 2 file mẫu (KH277 và CV6582)."""

from pathlib import Path

from src.pdf_task_extractor.extract_tables import extract_from_pdf

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
KH277_PDF = DATA_DIR / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
CV6582_PDF = DATA_DIR / "CV 6582.pdf"


def test_cv6582_extracts_all_12_migration_tasks():
    records = extract_from_pdf(str(CV6582_PDF))
    assert len(records) == 12

    first = records[0]
    assert first["tt"] == "1"
    assert first["don_vi_chu_tri"] == "Sở Y tế"
    assert "Xây dựng kế hoạch di trú" in first["ten_nhiem_vu"]

    last = records[-1]
    assert last["tt"] == "12"
    assert last["don_vi_chu_tri"] == "Sở Y tế"


def test_kh277_extracts_expected_number_of_rows():
    records = extract_from_pdf(str(KH277_PDF))
    # Gồm cả dòng nhóm cha (tt rỗng, chi_tiet là số nhóm) và dòng chi tiết
    # (tt là số thứ tự chi tiết, chi_tiet là a)/b)/c)...) — đã đối chiếu bằng
    # tay khớp với nội dung Phụ lục gốc.
    assert len(records) == 42


def test_kh277_header_rows_are_not_included_as_data():
    records = extract_from_pdf(str(KH277_PDF))
    for record in records:
        assert record.get("ten_nhiem_vu") not in (None, "Tên nhiệm vụ")
        assert record.get("tt") != "TT"


def test_kh277_detail_row_content_matches_source_document():
    records = extract_from_pdf(str(KH277_PDF))
    detail_rows = [r for r in records if r.get("tt") == "1" and r.get("chi_tiet") == "a)"]

    assert len(detail_rows) == 1
    assert detail_rows[0]["don_vi_chu_tri"] == "Sở Tài chính"
    assert "Dữ liệu đầu tư công" in detail_rows[0]["ten_nhiem_vu"]
