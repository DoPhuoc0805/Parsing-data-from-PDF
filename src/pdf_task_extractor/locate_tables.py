"""
Bước 1: Xác định vị trí (số trang) chứa bảng nhiệm vụ trong file PDF.

Thuật toán kết hợp 2 tín hiệu để tránh chỉ dựa vào 1 dấu hiệu duy nhất:

1. Tín hiệu cấu trúc: dùng pdfplumber.Page.find_tables() để lấy các bảng
   ứng viên trên mỗi trang; loại ngay các bảng có quá ít cột (bảng nhiệm vụ
   luôn có >= 4 cột: TT/Chi tiết, Tên nhiệm vụ, Đơn vị chủ trì, ..., Thời hạn).

2. Tín hiệu từ khóa: dòng đầu tiên (header) của bảng ứng viên có chứa
   >= 2 trong số các từ khóa đặc trưng ("Đơn vị chủ trì", "Đơn vị phối hợp",
   "Sản phẩm", "Thời hạn") thì coi đây là bảng mục tiêu.

Vì bảng nhiệm vụ thường bị ngắt qua nhiều trang và header không lặp lại ở
mọi trang, thuật toán còn xử lý "bảng nối tiếp" (continuation): nếu một
trang có bảng không khớp từ khóa nhưng có CÙNG số cột với bảng mục tiêu ở
trang liền trước, thì coi là phần nối tiếp của cùng một bảng logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pdfplumber

DEFAULT_HEADER_KEYWORDS = [
    "Đơn vị chủ trì",
    "Đơn vị phối hợp",
    "Sản phẩm",
    "Thời hạn",
]

MIN_COLUMNS = 4
MIN_KEYWORD_HITS = 2


@dataclass
class TableLocation:
    page_index: int  # 0-indexed
    table_index: int  # thứ tự bảng trong page.find_tables()
    bbox: tuple
    n_cols: int
    header_row: list
    is_continuation: bool  # True nếu bảng này không có header khớp mà được suy ra là nối tiếp


def _clean(cell: Optional[str]) -> str:
    return (cell or "").strip()


def _row_text(row: list) -> str:
    return " ".join(_clean(c) for c in row)


def _looks_like_header(row: list, keywords: list[str], min_hits: int = MIN_KEYWORD_HITS) -> bool:
    text = _row_text(row)
    hits = sum(1 for kw in keywords if kw in text)
    return hits >= min_hits


def find_target_tables(
    pdf_path: str,
    keywords: Optional[list[str]] = None,
    min_columns: int = MIN_COLUMNS,
) -> list[TableLocation]:
    """Quét toàn bộ PDF, trả về danh sách TableLocation của các bảng nhiệm vụ.

    Bao gồm cả các bảng "nối tiếp" (không có header nhưng cùng số cột với
    bảng mục tiêu ngay trước đó).
    """
    if keywords is None:
        keywords = DEFAULT_HEADER_KEYWORDS

    locations: list[TableLocation] = []
    last_target_cols: Optional[int] = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            tables = page.find_tables()
            page_had_target = False

            for table_index, table in enumerate(tables):
                data = table.extract()
                if not data or not data[0]:
                    continue

                n_cols = len(data[0])
                if n_cols < min_columns:
                    continue

                header_row = [_clean(c) for c in data[0]]
                is_header = _looks_like_header(data[0], keywords)
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
                        )
                    )
                    last_target_cols = n_cols
                    page_had_target = True

            if not page_had_target:
                # Trang không có bảng mục tiêu -> reset chuỗi nối tiếp để
                # tránh gộp nhầm bảng không liên quan ở các trang xa nhau.
                last_target_cols = None

    return locations


def get_target_page_range(locations: list[TableLocation]) -> Optional[tuple[int, int]]:
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
        print(f"page {loc.page_index + 1} | table {loc.table_index} | cols={loc.n_cols} | {kind}")

    rng = get_target_page_range(locs)
    if rng:
        print(f"\n=> Bang nhiem vu nam tu trang {rng[0] + 1} den trang {rng[1] + 1}")
    else:
        print("Khong tim thay bang muc tieu.")
