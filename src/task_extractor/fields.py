"""
Ánh xạ tiêu đề cột về trường chuẩn — dùng chung cho mọi nguồn (PDF, Excel).

Các văn bản khác nhau có thể đặt tên cột khác nhau cho cùng một ý nghĩa
(vd "Đơn vị chủ trì" vs "Đơn vị thực hiện"), nên thay vì so khớp từ khóa cố
định, thuật toán ánh xạ mỗi cột header về một "trường chuẩn" (canonical
field) thông qua tập từ đồng nghĩa trong CANONICAL_FIELDS.

Một bảng được coi là "bảng phân công nhiệm vụ" khi header của nó khớp được
CẢ 2 trường bắt buộc: don_vi_chu_tri và don_vi_phoi_hop — đây chính là bản
chất của việc "nhiệm vụ giao cho đơn vị nào". Các bảng khác (vd bảng cấu
hình hạ tầng chỉ có cột Cấu hình/Số lượng) sẽ không khớp và bị loại tự
nhiên, không cần luật loại trừ riêng.
"""

from __future__ import annotations

from typing import Optional

CANONICAL_FIELDS = {
    "tt": ["TT"],
    "chi_tiet": ["Chi tiết"],
    "ten_nhiem_vu": ["Tên nhiệm vụ", "Công việc"],
    "don_vi_chu_tri": ["Đơn vị chủ trì", "Đơn vị thực hiện"],
    "don_vi_phoi_hop": ["Đơn vị phối hợp"],
    "san_pham": ["Sản phẩm"],
    "thoi_han": ["Thời hạn", "Số ngày dự kiến"],
}

# Từ khóa ngắn (vd "TT") dễ khớp nhầm vào chuỗi con của từ khác (vd "Viettel"
# chứa "tt") nếu dùng kiểu so khớp substring như các từ khóa dài. Với từ khóa
# có độ dài <= ngưỡng này, yêu cầu khớp CHÍNH XÁC toàn bộ nội dung ô.
EXACT_MATCH_LENGTH_THRESHOLD = 3

REQUIRED_FIELDS = ["don_vi_chu_tri", "don_vi_phoi_hop"]


def clean(cell: Optional[str]) -> str:
    return (cell or "").strip()


def _normalize_header_text(cell: Optional[str]) -> str:
    """Gộp xuống dòng trong header (do wrap chữ) thành khoảng trắng để so khớp từ khóa."""
    return " ".join(clean(cell).split())


def _matches_synonym(text: str, synonym: str) -> bool:
    """So khớp text (đã lower) với 1 từ khóa (chưa lower).

    Từ khóa ngắn (vd "TT") yêu cầu khớp CHÍNH XÁC để tránh khớp nhầm vào
    chuỗi con của từ khác (vd "Viettel" chứa "tt"). Từ khóa dài hơn dùng
    khớp substring như trước.
    """
    syn_lower = synonym.lower()
    if len(syn_lower) <= EXACT_MATCH_LENGTH_THRESHOLD:
        return text == syn_lower
    return syn_lower in text


def match_header_fields(rows: list) -> dict:
    """Ánh xạ {vị trí cột: trường chuẩn} cho các cột khớp CANONICAL_FIELDS.

    Nhận vào nhiều dòng (header có thể trải qua 2 dòng do ô bị chia tầng);
    quét theo thứ tự dòng, cột nào đã khớp ở dòng trước thì không ghi đè
    bởi dòng sau. So khớp không phân biệt hoa/thường.
    """
    mapping = {}
    for row in rows:
        for col_index, cell in enumerate(row):
            if col_index in mapping:
                continue
            text = _normalize_header_text(cell).lower()
            if not text:
                continue
            for field, synonyms in CANONICAL_FIELDS.items():
                if any(_matches_synonym(text, syn) for syn in synonyms):
                    mapping[col_index] = field
                    break
    return mapping


def is_task_header(column_mapping: dict) -> bool:
    """Header có khớp đủ các trường bắt buộc để coi là bảng phân công nhiệm vụ không."""
    matched_fields = set(column_mapping.values())
    return all(field in matched_fields for field in REQUIRED_FIELDS)


def count_header_rows(rows: list) -> int:
    """Số dòng đầu (trong cửa sổ đã quét) thực sự là header, dựa trên số dòng
    liên tiếp từ đầu có ít nhất 1 ô khớp CANONICAL_FIELDS."""
    last_contributing_row = -1
    for row_index, row in enumerate(rows):
        if match_header_fields([row]):
            last_contributing_row = row_index
    return last_contributing_row + 1
