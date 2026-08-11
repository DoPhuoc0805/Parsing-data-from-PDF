"""
Cấu hình cách đọc phân cấp cho từng kiểu mã hóa văn bản.

Profile được đặt tên theo **cách mã hóa**, không theo tên file — nhờ vậy một
văn bản mới dùng cùng kiểu mã sẽ tự khớp profile có sẵn, không phải viết
thêm gì.

Cờ keep_parent_as_task là điểm duy nhất máy không tự suy ra được: dòng nhiệm
vụ cha ở PDF là **ô merge dùng chung** (giá trị áp cho các dòng con, bản thân
nó không phải việc được giao), còn ở một số file Excel lại là **nhiệm vụ tổng
thật** có đơn vị chủ trì và thời hạn riêng. Hai trường hợp này nhìn từ dữ liệu
là như nhau nên phải khai báo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Profile:
    name: str
    code_field: str  # tên trường chuẩn chứa mã phân cấp
    parser: str  # "relative" hoặc "absolute"
    join_with: str = "."  # ghép các đoạn path thành mã nhiệm vụ
    separator: str = "."  # dấu tách khi đọc mã tuyệt đối
    self_segment: Optional[str] = None  # đoạn cuối mang nghĩa "chính nó" (mã tuyệt đối)
    level_patterns: tuple = ()  # regex từng cấp (mã tương đối)
    keep_parent_as_task: bool = False
    drop_fields: tuple = ()  # cột chỉ dùng nội bộ, không đưa xuống tầng silver


# PDF: cấp 1 là số trần ("12"), cấp 2 là chữ cái kèm ngoặc ("b)").
# Ghép không dấu phân cách để ra mã quen thuộc "12b" thay vì "12.b".
NUMBER_LETTER = Profile(
    name="number_letter",
    code_field="chi_tiet",
    parser="relative",
    join_with="",
    level_patterns=(
        re.compile(r"^(\d+)$"),
        re.compile(r"^([a-zđ])\)$"),
    ),
    keep_parent_as_task=False,
    drop_fields=("tt", "chi_tiet"),
)
