"""
Chuyển dòng thô (bronze) thành bản ghi nhiệm vụ chuẩn (silver).

Việc xác định nhiệm vụ cha/con dùng chung cơ chế path ở hierarchy.py, cấu hình
theo từng kiểu mã hóa ở profiles.py — module này lo phần còn lại: loại dòng
nhãn nhóm, kế thừa cột dùng chung, gắn ngữ cảnh nhóm và làm sạch nội dung.

**Loại dòng nhãn nhóm.** Văn bản thường có dòng chỉ mang tên nhóm, không phải
một việc được giao cho ai. Dòng nào có nhiệm vụ con nằm dưới thì được coi là
nhãn nhóm và không xuất hiện ở kết quả cuối — trừ khi profile khai
keep_parent_as_task, dành cho văn bản mà dòng cha thực sự là một nhiệm vụ tổng
có đơn vị chủ trì riêng.

**Kế thừa cột dùng chung.** Văn bản gốc dùng merged cell theo nhóm: một số cột
(đơn vị chủ trì, đơn vị phối hợp, sản phẩm, thời hạn) chỉ ghi 1 lần ở dòng cha,
các dòng con bị trống dù thực chất áp dụng chung. Dòng con leo ngược lên các
tổ tiên (gần trước, xa sau) để lấy giá trị, nhưng **chỉ điền khi ô của nó đang
rỗng, không bao giờ ghi đè giá trị đã có sẵn** — nhờ quy tắc này mà cùng một
cách xử lý đúng cho cả nhóm dùng chung đơn vị chủ trì lẫn nhóm mà mỗi dòng con
có đơn vị chủ trì riêng.

**Ngữ cảnh nhóm.** Mỗi nhiệm vụ mang theo tên và số hiệu của **tổ tiên gốc**
(đoạn đầu tiên của path). Nhiệm vụ độc lập không có dòng con thì tổ tiên gốc
chính là nó, nên nó tự là một nhóm gồm đúng một nhiệm vụ — không phải "không
thuộc nhóm nào".

**Làm sạch nội dung.** PDF wrap chữ giữa dòng (vd "Sở\nKHCN") không mang ý
nghĩa xuống dòng thật nên được nối bằng khoảng trắng; riêng dòng bắt đầu bằng
"-" (gạch đầu dòng thật, dùng liệt kê nhiều ý trong 1 ô) được giữ nguyên xuống
dòng để không mất định dạng danh sách.
"""

from __future__ import annotations

import re

from .hierarchy import (
    check_paths,
    dedupe_paths,
    derive_parent_paths,
    parse_absolute_paths,
    parse_relative_paths,
)
from .profiles import NUMBER_LETTER, Profile

INHERITABLE_FIELDS = ["don_vi_chu_tri", "don_vi_phoi_hop", "san_pham", "thoi_han"]
TEXT_FIELDS_TO_CLEAN = [
    "ten_nhiem_vu",
    "don_vi_chu_tri",
    "don_vi_phoi_hop",
    "san_pham",
    "thoi_han",
    "nhom_nhiem_vu",
]

_BULLET_PREFIX = re.compile(r"^-\s*")


def _rejoin_wrapped_lines(text):
    """Nối các dòng bị PDF wrap chữ giữa dòng thành 1 dòng liền mạch, giữ
    nguyên các dòng thực sự là gạch đầu dòng riêng (bắt đầu bằng "-")."""
    if not text:
        return text

    merged = []
    for line in text.split("\n"):
        line = line.strip()
        if merged and not _BULLET_PREFIX.match(line):
            merged[-1] = f"{merged[-1]} {line}".strip()
        else:
            merged.append(line)
    return "\n".join(merged)


def _parse_paths(rows: list, profile: Profile) -> list:
    codes = [row.get(profile.code_field) for row in rows]
    if profile.parser == "absolute":
        return parse_absolute_paths(codes, profile.separator, profile.self_segment)
    if profile.parser == "relative":
        return parse_relative_paths(codes, list(profile.level_patterns))
    raise ValueError(f"Profile {profile.name!r} khai parser khong hop le: {profile.parser!r}")


def build_tasks(rows: list, profile: Profile = NUMBER_LETTER) -> list:
    """Dựng danh sách nhiệm vụ chuẩn từ các dòng thô đã đọc được."""
    paths = dedupe_paths(_parse_paths(rows, profile))
    check_paths(paths)

    parent_paths = derive_parent_paths(paths)
    row_by_path = {path: row for path, row in zip(paths, rows) if path}

    result = []
    for row, path in zip(rows, paths):
        is_group_label = path in parent_paths and not profile.keep_parent_as_task
        if is_group_label:
            continue

        task = dict(row)

        if path:
            # Leo ngược lên tổ tiên (gần trước, xa sau) lấy giá trị cho ô đang rỗng.
            for depth in range(len(path) - 1, 0, -1):
                ancestor = row_by_path.get(path[:depth])
                if ancestor is None:
                    continue
                for field in INHERITABLE_FIELDS:
                    if not task.get(field):
                        task[field] = ancestor.get(field)

            root = row_by_path.get(path[:1])
            task["nhom_nhiem_vu"] = root.get("ten_nhiem_vu") if root else None
            task["so_nhom_nhiem_vu"] = path[0]
            task["ma_nhiem_vu"] = profile.join_with.join(path)
        else:
            task["nhom_nhiem_vu"] = None
            task["so_nhom_nhiem_vu"] = None
            task["ma_nhiem_vu"] = None

        for field in profile.drop_fields:
            task.pop(field, None)

        for field in TEXT_FIELDS_TO_CLEAN:
            if field in task:
                task[field] = _rejoin_wrapped_lines(task[field])

        result.append(task)

    return result
