"""
Bước 1: Xác định vị trí (số trang) chứa bảng nhiệm vụ trong file PDF.

Các văn bản khác nhau có thể đặt tên cột khác nhau cho cùng một ý nghĩa
(vd "Đơn vị chủ trì" vs "Đơn vị thực hiện"), nên thay vì so khớp từ khóa cố
định, thuật toán ánh xạ mỗi cột header về một "trường chuẩn" (canonical
field) thông qua tập từ đồng nghĩa trong CANONICAL_FIELDS.

Một bảng được coi là "bảng phân công nhiệm vụ" khi header của nó khớp được
CẢ 2 trường bắt buộc: don_vi_chu_tri và don_vi_phoi_hop — đây chính là bản
chất của việc "nhiệm vụ giao cho đơn vị nào". Các bảng khác (vd bảng cấu
hình hạ tầng chỉ có cột Cấu hình/Số lượng) sẽ không khớp và bị loại tự
nhiên, không cần luật loại trừ riêng.

Vì bảng có thể bị ngắt qua nhiều trang mà không lặp lại header, thuật toán
còn nhận diện "bảng nối tiếp" (continuation): trang không có header khớp
nhưng có cùng số cột với bảng mục tiêu ở trang liền trước thì được gộp vào,
thừa hưởng cùng column_mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pdfplumber

CANONICAL_FIELDS = {
    "ten_nhiem_vu": ["Tên nhiệm vụ", "Công việc"],
    "don_vi_chu_tri": ["Đơn vị chủ trì", "Đơn vị thực hiện"],
    "don_vi_phoi_hop": ["Đơn vị phối hợp"],
    "san_pham": ["Sản phẩm"],
    "thoi_han": ["Thời hạn", "Số ngày dự kiến"],
}

REQUIRED_FIELDS = ["don_vi_chu_tri", "don_vi_phoi_hop"]

MIN_COLUMNS = 4

# snap_x_tolerance lớn hơn mặc định để gộp các đường kẻ dọc bị lệch nhẹ
# (artifact khi xuất PDF từ Word) — nếu không, một cột logic có thể bị tách
# nhầm thành nhiều cột do các đường kẻ thừa sát nhau.
TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_x_tolerance": 15,
}


@dataclass
class TableLocation:
    page_index: int  # 0-indexed
    table_index: int  # thứ tự bảng trong page.find_tables()
    bbox: tuple
    n_cols: int
    header_row: list
    is_continuation: bool
    column_mapping: dict  # {vị trí cột: tên trường chuẩn}


def _clean(cell: Optional[str]) -> str:
    return (cell or "").strip()


def _normalize_header_text(cell: Optional[str]) -> str:
    """Gộp xuống dòng trong header (do wrap chữ) thành khoảng trắng để so khớp từ khóa."""
    return " ".join(_clean(cell).split())


def _match_header_fields(header_row: list) -> dict:
    """Ánh xạ {vị trí cột: trường chuẩn} cho các cột khớp CANONICAL_FIELDS."""
    mapping = {}
    for col_index, cell in enumerate(header_row):
        text = _normalize_header_text(cell)
        for field, synonyms in CANONICAL_FIELDS.items():
            if any(syn in text for syn in synonyms):
                mapping[col_index] = field
                break
    return mapping


def _is_target_header(column_mapping: dict) -> bool:
    matched_fields = set(column_mapping.values())
    return all(field in matched_fields for field in REQUIRED_FIELDS)


def find_target_tables(pdf_path: str, min_columns: int = MIN_COLUMNS) -> list:
    """Quét toàn bộ PDF, trả về danh sách TableLocation của các bảng phân công nhiệm vụ."""
    locations: list = []
    last_target_cols: Optional[int] = None
    last_target_mapping: Optional[dict] = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            tables = page.find_tables(table_settings=TABLE_SETTINGS)
            page_had_target = False

            for table_index, table in enumerate(tables):
                data = table.extract()
                if not data or not data[0]:
                    continue

                n_cols = len(data[0])
                if n_cols < min_columns:
                    continue

                header_row = [_clean(c) for c in data[0]]
                column_mapping = _match_header_fields(data[0])
                is_header = _is_target_header(column_mapping)
                is_continuation = (
                    not is_header
                    and last_target_cols is not None
                    and n_cols == last_target_cols
                )

                if is_header or is_continuation:
                    locations.append(
                        TableLocation(
                            page_index=page_index,
                            table_index=table_index,
                            bbox=table.bbox,
                            n_cols=n_cols,
                            header_row=header_row,
                            is_continuation=is_continuation,
                            column_mapping=column_mapping if is_header else last_target_mapping,
                        )
                    )
                    last_target_cols = n_cols
                    if is_header:
                        last_target_mapping = column_mapping
                    page_had_target = True

            if not page_had_target:
                last_target_cols = None
                last_target_mapping = None

    return locations


def get_target_page_range(locations: list) -> Optional[tuple]:
    """Trả về (trang_bắt_đầu, trang_kết_thúc) 0-indexed, hoặc None nếu không tìm thấy."""
    if not locations:
        return None
    pages = [loc.page_index for loc in locations]
    return min(pages), max(pages)


if __name__ == "__main__":
    import sys

    default_path = "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else default_path

    locs = find_target_tables(pdf_path)
    for loc in locs:
        kind = "continuation" if loc.is_continuation else "header"
        print(f"page {loc.page_index + 1} | table {loc.table_index} | cols={loc.n_cols} | {kind} | mapping={loc.column_mapping}")

    rng = get_target_page_range(locs)
    if rng:
        print(f"\n=> Bang phan cong nhiem vu nam tu trang {rng[0] + 1} den trang {rng[1] + 1}")
    else:
        print("Khong tim thay bang muc tieu.")
