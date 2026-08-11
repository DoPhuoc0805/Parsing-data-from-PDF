"""Unit test cho read_excel.py trên 2 file Excel mẫu có cấu trúc khác nhau."""

from datetime import datetime
from pathlib import Path

from src.task_extractor.read_excel import _cell_to_text, read_excel

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
TEST2_XLSX = DATA_DIR / "test_2.xlsx"
TEST3_XLSX = DATA_DIR / "test_3.xlsx"


def test_test2_reads_every_data_row():
    rows = read_excel(str(TEST2_XLSX))
    assert len(rows) == 178


def test_test3_reads_every_data_row():
    rows = read_excel(str(TEST3_XLSX))
    assert len(rows) == 375


def test_header_is_found_below_the_title_rows():
    # Bang cua test_2 bat dau o dong 2, cua test_3 o dong 3 (phia tren la tieu de).
    assert read_excel(str(TEST2_XLSX))[0]["ma_goc"] == "KH20_TT_N01"
    assert read_excel(str(TEST3_XLSX))[0]["tt"] == "1.0"


def test_lead_unit_column_is_not_stolen_by_similar_column():
    # test_2 co ca "Don vi chu tri" va "Phong, don vi chu tri"; cot thu hai chi
    # chua cum tu khoa nhu mot phan ten nen khong duoc tranh mat truong.
    row = read_excel(str(TEST2_XLSX))[1]
    assert row["don_vi_chu_tri"] == "Sở Khoa học và Công nghệ"


def test_extra_columns_are_kept_for_agent_use():
    rows = read_excel(str(TEST2_XLSX))
    assert "ghi_chu" in rows[0]
    assert "ket_qua" in rows[0]
    # Cac cot thong ke theo tuan cua test_3 khong duoc anh xa.
    assert all("tuan" not in field for field in read_excel(str(TEST3_XLSX))[0])


def test_merged_cell_value_is_filled_across_its_range():
    # O "Ghi chu" cua test_2 bi gop qua 3 dong (Excel K17:K19). openpyxl chi tra
    # gia tri o o goc tren-trai, 2 o con lai la None -> phai duoc dien ra ca vung.
    rows = read_excel(str(TEST2_XLSX))
    merged = [r for r in rows if r["ma_goc"] in ("KH20_TT_N02.3.1", "KH20_TT_N02.3.2", "KH20_TT_N02.3.3")]

    assert len(merged) == 3
    notes = {r["ghi_chu"] for r in merged}
    assert len(notes) == 1
    assert notes.pop().startswith("Sau đợt 1, không có đơn vị đề xuất")


def test_cell_values_are_converted_to_text_for_json():
    assert _cell_to_text(None) is None
    assert _cell_to_text("  Sở Y tế  ") == "Sở Y tế"
    # Phan thap phan cua so chinh la cap trong ma phan cap -> phai giu.
    assert _cell_to_text(1.0) == "1.0"
    assert _cell_to_text(13.1) == "13.1"
    # Ngay thang doi ve dung dinh dang cac o cung cot duoc go tay.
    assert _cell_to_text(datetime(2026, 2, 5)) == "05/02/2026"
