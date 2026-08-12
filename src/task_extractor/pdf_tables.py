"""
Xác định vị trí (số trang) chứa bảng nhiệm vụ trong file PDF.

Việc nhận diện "bảng nào là bảng phân công nhiệm vụ" dùng chung cơ chế ánh xạ
trường chuẩn ở fields.py; module này chỉ lo phần đặc thù PDF: quét trang, dò
bảng bằng pdfplumber, và xử lý bảng bị ngắt qua nhiều trang.

Vì bảng có thể bị ngắt qua nhiều trang mà không lặp lại header, thuật toán
còn nhận diện "bảng nối tiếp" (continuation): trang không có header khớp
nhưng có cùng số cột với bảng mục tiêu ở trang liền trước thì được gộp vào,
thừa hưởng cùng column_mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pdfplumber

from .fields import clean, count_header_rows, is_task_header, match_header_fields

MIN_COLUMNS = 4

# Header có thể trải qua nhiều dòng do ô bị chia tầng (vd "Stt" ở dòng 1,
# "TT"/"Chi tiết" ở dòng 2) — quét 2 dòng đầu để không bỏ sót từ khóa rơi
# xuống dòng thứ 2.
HEADER_ROW_SCAN_LIMIT = 2

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
    header_row_count: int  # số dòng đầu của rows là header, cần bỏ qua khi lấy dữ liệu
    rows: list  # toàn bộ dữ liệu thô (kể cả header) của bảng trên trang này


def find_task_tables(pdf_path: str, min_columns: int = MIN_COLUMNS) -> list:
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

                header_row = [clean(c) for c in data[0]]
                column_mapping = match_header_fields(data[:HEADER_ROW_SCAN_LIMIT])
                is_header = is_task_header(column_mapping)
                is_continuation = (
                    not is_header
                    and last_target_cols is not None
                    and n_cols == last_target_cols
                )

                if is_header or is_continuation:
                    header_row_count = (
                        count_header_rows(data[:HEADER_ROW_SCAN_LIMIT]) if is_header else 0
                    )
                    locations.append(
                        TableLocation(
                            page_index=page_index,
                            table_index=table_index,
                            bbox=table.bbox,
                            n_cols=n_cols,
                            header_row=header_row,
                            is_continuation=is_continuation,
                            column_mapping=column_mapping if is_header else (last_target_mapping or {}),
                            header_row_count=header_row_count,
                            rows=data,
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


def get_task_page_range(locations: list) -> Optional[tuple]:
    """Trả về (trang_bắt_đầu, trang_kết_thúc) 0-indexed, hoặc None nếu không tìm thấy."""
    if not locations:
        return None
    pages = [loc.page_index for loc in locations]
    return min(pages), max(pages)


if __name__ == "__main__":
    import sys

    default_path = "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else default_path

    locs = find_task_tables(pdf_path)
    for loc in locs:
        kind = "continuation" if loc.is_continuation else "header"
        print(f"page {loc.page_index + 1} | table {loc.table_index} | cols={loc.n_cols} | {kind} | mapping={loc.column_mapping}")

    rng = get_task_page_range(locs)
    if rng:
        print(f"\n=> Bang phan cong nhiem vu nam tu trang {rng[0] + 1} den trang {rng[1] + 1}")
    else:
        print("Khong tim thay bang muc tieu.")
