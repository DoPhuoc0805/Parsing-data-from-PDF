"""
Đọc file PDF thành danh sách dòng thô (tầng bronze).

Với mỗi TableLocation (từ pdf_tables.py), bỏ qua đúng số dòng header
(header_row_count) rồi map các dòng còn lại theo column_mapping. Nhiều
TableLocation của cùng 1 bảng bị ngắt qua nhiều trang được nối lại thành 1
danh sách duy nhất theo thứ tự trang.

Đây là dữ liệu "thô": giữ nguyên giá trị gốc (kể cả None, xuống dòng "\n" do
PDF wrap chữ) — việc xử lý dòng nhóm cha, merged cell, chuẩn hóa nội dung
thuộc về tasks.py.

Một dòng bảng đôi khi rơi đúng ranh giới trang: phần đầu nằm ở cuối trang
trước, phần còn lại (do PDF cắt ngang 1 ô đang wrap chữ) lạc sang đầu trang
sau thành 1 dòng riêng — dòng này không có giá trị ở các cột định danh
(tt/chi_tiet) vì các cột đó chỉ xuất hiện 1 lần ở phần đầu dòng thật. Các
dòng "mảnh vỡ" này được nhận diện (thiếu mọi cột định danh đang có trong
column_mapping) và gộp ngược nội dung vào dòng ngay trước (nối bằng "\n"),
thay vì giữ như 1 dòng riêng biệt vô nghĩa.
"""

from __future__ import annotations

from .pdf_tables import find_task_tables

IDENTIFIER_FIELDS = ["tt", "chi_tiet"]


def _row_to_task(row: list, column_mapping: dict) -> dict:
    """Map 1 dòng dữ liệu thô thành dict {ten_truong_chuan: gia_tri}."""
    return {
        field: (row[col_index] if col_index < len(row) else None)
        for col_index, field in column_mapping.items()
    }


def _is_fragment_row(record: dict) -> bool:
    """Dòng bị lạc do ngắt trang: có ít nhất 1 cột định danh trong mapping,
    nhưng tất cả đều rỗng."""
    present_identifiers = [field for field in IDENTIFIER_FIELDS if field in record]
    if not present_identifiers:
        return False
    return all(not record.get(field) for field in present_identifiers)


def _merge_fragment_into(previous: dict, fragment: dict) -> None:
    for field, value in fragment.items():
        if not value:
            continue
        if previous.get(field):
            previous[field] = f"{previous[field]}\n{value}"
        else:
            previous[field] = value


def read_rows(locations: list) -> list:
    """Gộp dữ liệu thô (đã bỏ header) của toàn bộ TableLocation thành 1 danh sách."""
    records = []
    for location in locations:
        data_rows = location.rows[location.header_row_count :]
        for row in data_rows:
            record = _row_to_task(row, location.column_mapping)
            if not any(value not in (None, "") for value in record.values()):
                continue
            if records and _is_fragment_row(record):
                _merge_fragment_into(records[-1], record)
            else:
                records.append(record)
    return records


def read_pdf(pdf_path: str) -> list:
    """Xác định bảng nhiệm vụ trong PDF rồi đọc ra danh sách dòng thô."""
    locations = find_task_tables(pdf_path)
    return read_rows(locations)


if __name__ == "__main__":
    import json
    import sys

    # Console Windows mac dinh dung codepage khong ho tro tieng Viet.
    sys.stdout.reconfigure(encoding="utf-8")

    default_path = "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else default_path

    records = read_pdf(pdf_path)
    print(json.dumps(records, ensure_ascii=False, indent=2))
    print(f"\n=> Tong so dong: {len(records)}", file=sys.stderr)
