"""
Hàm main nối các bước: locate_tables (qua extract_tables) -> extract_tables ->
normalize, rồi xuất kết quả cuối cùng ra CSV/JSON.

Bước validate chưa được nối vào đây — module validate.py hiện mới có
docstring, sẽ thêm vào run_pipeline khi được implement.
"""

from __future__ import annotations

from .extract_tables import extract_from_pdf
from .normalize import apply_group_inheritance, export_records


def run_pipeline(pdf_path: str, output_path: str) -> list:
    """Chạy Bước 1-2-3, xuất kết quả ra output_path (CSV hoặc JSON theo đuôi file).

    Trả về danh sách record đã chuẩn hóa để gọi tiếp nếu cần (vd validate).
    """
    records = extract_from_pdf(pdf_path)
    normalized = apply_group_inheritance(records)
    export_records(normalized, output_path)
    return normalized
