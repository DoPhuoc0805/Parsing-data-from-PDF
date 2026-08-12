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

Ngay cả khi cờ này bật, dòng cha **không có đơn vị chủ trì lẫn phối hợp** vẫn
bị coi là nhãn nhóm — một dòng không giao việc cho ai thì không thể là nhiệm
vụ. Nhờ vậy văn bản trộn cả hai kiểu (như test_2: nhóm lớn chỉ là tiêu đề,
nhóm con lại là nhiệm vụ tổng thật) được xử lý đúng mà không cần luật riêng.

deliverable_field khai cột "sản phẩm đầu ra" của văn bản, dùng làm dấu hiệu
tinh hơn: dòng có con mà **không kèm sản phẩm** thì là nhãn nhóm, dù có ghi
đơn vị chủ trì. Có văn bản ghi đơn vị chủ trì ở cả dòng tiêu đề chương mục,
nhưng đó là "chương này thuộc trách nhiệm ai" chứ không phải một việc cụ thể.

Không phải văn bản nào cũng có cột này (2/4 văn bản mẫu hiện tại không có),
nên luật chỉ chạy khi cột **thực sự tồn tại** trong văn bản đang đọc — vắng
cột thì quay về dấu hiệu cơ bản là có giao việc cho đơn vị nào không. Không
phán xét bằng một cột không có mặt.
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
    deliverable_field: Optional[str] = None  # cột sản phẩm đầu ra, nếu văn bản có
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

# Excel kiểu "mã phân cấp có tiền tố": KH20_TT_N01 -> N01.1 -> N01.1.1.
# Mã tự chứa đủ đường dẫn nên số La Mã ở cột STT thành thừa — vốn cũng không
# đáng tin (có nhóm bị bỏ trống số La Mã, lại có mã 1 đoạn là nhiệm vụ độc lập).
DOTTED_CODE = Profile(
    name="dotted_code",
    code_field="ma_goc",
    parser="absolute",
    keep_parent_as_task=True,
    deliverable_field="san_pham",
    drop_fields=("ma_goc", "tt"),
)

# Excel kiểu "số thập phân": 13.0 là nhiệm vụ số 13, 13.1 là việc con của nó.
DECIMAL_INDEX = Profile(
    name="decimal_index",
    code_field="tt",
    parser="absolute",
    self_segment="0",
    keep_parent_as_task=True,
    drop_fields=("tt",),
)

# Mọi profile đều là ứng viên cho mọi định dạng file: kiểu mã hóa (số+chữ cái,
# mã có tiền tố, số thập phân) là đặc trưng của CÁCH văn bản đánh mã, không
# phải của định dạng file chứa nó — một PDF vẫn có thể dùng mã kiểu dotted_code
# nếu người soạn làm bảng trong Word/Excel theo cùng quy ước rồi xuất ra PDF.
ALL_PROFILES = (NUMBER_LETTER, DOTTED_CODE, DECIMAL_INDEX)
