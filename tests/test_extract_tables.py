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
    # tay khớp với nội dung Phụ lục gốc. 42 dòng vật lý trừ đi 1 dòng bị PDF
    # ngắt trang (đã gộp lại vào dòng 14/a ngay trước) = 41.
    assert len(records) == 41


def test_kh277_merges_row_split_across_page_break():
    records = extract_from_pdf(str(KH277_PDF))
    record_14 = next(r for r in records if r.get("tt") == "14")
    # Phan dau o cuoi trang truoc, phan sau ("thoi gian giai quyet...") bi
    # PDF tach sang dau trang ke tiep nhu 1 dong rieng - phai duoc gop lai.
    assert "Phê duyệt phương án tái cấu trúc" in record_14["san_pham"]
    assert "thời gian giải quyết, 50% thành" in record_14["san_pham"]


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
