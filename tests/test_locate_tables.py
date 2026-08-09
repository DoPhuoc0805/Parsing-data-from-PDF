"""Unit test cho locate_tables.py trên cả 2 dạng file mẫu (KH277 và CV6582)."""

from pathlib import Path

from src.pdf_task_extractor.locate_tables import (
    _match_header_fields,
    find_target_tables,
    get_target_page_range,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
KH277_PDF = DATA_DIR / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
CV6582_PDF = DATA_DIR / "CV 6582.pdf"


def test_kh277_finds_expected_page_range():
    locations = find_target_tables(str(KH277_PDF))
    # Bảng Phụ lục nằm từ trang 5 đến trang 12 (1-indexed) -> 4..11 (0-indexed)
    assert get_target_page_range(locations) == (4, 11)


def test_kh277_excludes_non_table_pages():
    locations = find_target_tables(str(KH277_PDF))
    detected_pages = {loc.page_index for loc in locations}
    # Trang 0-3 (1-4) là nội dung công văn, không có bảng nhiệm vụ
    assert detected_pages.isdisjoint({0, 1, 2, 3})


def test_cv6582_finds_migration_table_only():
    locations = find_target_tables(str(CV6582_PDF))
    # Bảng "Kế hoạch sơ bộ di trú dữ liệu" nằm ở trang 8-9 (1-indexed) -> 7..8 (0-indexed)
    assert get_target_page_range(locations) == (7, 8)


def test_cv6582_excludes_infra_config_table():
    locations = find_target_tables(str(CV6582_PDF))
    detected_pages = {loc.page_index for loc in locations}
    # Trang 3-6 (4-7) chứa bảng cấu hình hạ tầng, không phải bảng phân công
    assert detected_pages.isdisjoint({3, 4, 5, 6})


def test_all_detected_tables_have_required_column_mapping():
    for pdf_path in (KH277_PDF, CV6582_PDF):
        locations = find_target_tables(str(pdf_path))
        assert locations, f"Khong tim thay bang nao trong {pdf_path.name}"
        for loc in locations:
            assert "don_vi_chu_tri" in loc.column_mapping.values()
            assert "don_vi_phoi_hop" in loc.column_mapping.values()


def test_match_header_fields_finds_required_field_on_second_row():
    # Mô phỏng header 2 tầng, nơi "Đơn vị chủ trì" rơi xuống dòng thứ 2
    row0 = ["Stt", None, "Tên nhiệm vụ", None, "Đơn vị phối hợp", "Sản phẩm", "Thời hạn"]
    row1 = ["TT", "Chi tiết", None, "Đơn vị chủ trì", None, None, None]

    mapping = _match_header_fields([row0, row1])

    assert mapping[3] == "don_vi_chu_tri"
    assert mapping[4] == "don_vi_phoi_hop"


def test_match_header_fields_is_case_insensitive():
    row0 = ["TT", "CÔNG VIỆC", "ĐƠN VỊ CHỦ TRÌ", "ĐƠN VỊ PHỐI HỢP"]

    mapping = _match_header_fields([row0])

    assert mapping[2] == "don_vi_chu_tri"
    assert mapping[3] == "don_vi_phoi_hop"
