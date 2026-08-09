"""Unit test cho locate_tables.py: kiểm tra xác định đúng trang chứa bảng nhiệm vụ."""

from pathlib import Path

from src.pdf_task_extractor.locate_tables import find_target_tables, get_target_page_range

SAMPLE_PDF = Path(__file__).resolve().parents[1] / "data" / "raw" / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"


def test_finds_expected_page_range():
    locations = find_target_tables(str(SAMPLE_PDF))
    page_range = get_target_page_range(locations)

    assert page_range is not None
    start, end = page_range
    # File mẫu: bảng Phụ lục nằm từ trang 5 đến trang 12 (1-indexed) -> 4..11 (0-indexed)
    assert start == 4
    assert end == 11


def test_excludes_non_table_pages():
    locations = find_target_tables(str(SAMPLE_PDF))
    detected_pages = {loc.page_index for loc in locations}

    # Trang 0-3 (1-4 theo 1-indexed) là nội dung công văn, không có bảng nhiệm vụ
    assert detected_pages.isdisjoint({0, 1, 2, 3})


def test_all_detected_tables_have_seven_columns():
    locations = find_target_tables(str(SAMPLE_PDF))
    assert all(loc.n_cols == 7 for loc in locations)
