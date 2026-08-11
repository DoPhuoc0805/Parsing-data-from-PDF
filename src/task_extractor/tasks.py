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

import logging
import re

from .hierarchy import (
    check_paths,
    dedupe_paths,
    derive_parent_paths,
    nearest_existing_ancestor,
    parse_absolute_paths,
    parse_relative_paths,
)
from .profiles import NUMBER_LETTER, Profile

INHERITABLE_FIELDS = ["don_vi_chu_tri", "don_vi_phoi_hop", "san_pham", "thoi_han"]

# Dòng không giao việc cho đơn vị nào thì không thể là một nhiệm vụ được giao.
ASSIGNMENT_FIELDS = ["don_vi_chu_tri", "don_vi_phoi_hop"]

# Luật "dòng cha không kèm sản phẩm là nhãn nhóm" chỉ đáng tin khi cột sản phẩm
# được điền nghiêm túc. Dưới ngưỡng này ở các dòng lá là dấu hiệu cột bị bỏ bê,
# lúc đó kết quả vẫn chạy nhưng phải cảnh báo để người dùng kiểm lại.
DELIVERABLE_COVERAGE_THRESHOLD = 0.5

logger = logging.getLogger(__name__)
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


def _has_assignment(row: dict) -> bool:
    return any(row.get(field) for field in ASSIGNMENT_FIELDS)


def _number_flat_document(paths: list) -> list:
    """Văn bản không có cột mã phân cấp nào thì đánh số thứ tự theo thứ tự dòng.

    Mọi dòng đều là nhiệm vụ ngang hàng, nhưng vẫn cần mã ổn định để tham
    chiếu tới — nhất là khi kết quả được đưa cho hệ thống khác hoặc AI agent
    dùng. Chỉ áp dụng khi KHÔNG dòng nào đọc được mã, để số thứ tự sinh ra
    không đụng phải mã thật của văn bản có phân cấp.
    """
    if any(paths):
        return paths
    return [(str(index),) for index in range(1, len(paths) + 1)]


def _column_exists(rows: list, field: str) -> bool:
    """Cột vắng hẳn khỏi văn bản khác với cột có mà ô để trống: phần đọc file
    chỉ tạo trường cho cột thật sự có trong header, nên kiểm tra bằng key."""
    return any(field in row for row in rows)


def _warn_if_deliverable_is_sparse(leaf_rows: list, field: str) -> None:
    if not leaf_rows:
        return
    filled = sum(1 for row in leaf_rows if row.get(field))
    coverage = filled / len(leaf_rows)
    if coverage < DELIVERABLE_COVERAGE_THRESHOLD:
        logger.warning(
            "Cot %r chi duoc dien o %d/%d nhiem vu (%.0f%%) - dung lam dau hieu "
            "nhan nhom co the loai nham; nen kiem lai ket qua",
            field, filled, len(leaf_rows), coverage * 100,
        )


def _is_group_label(row: dict, profile: Profile, use_deliverable: bool) -> bool:
    """Dòng có nhiệm vụ con nằm dưới: là nhãn nhóm hay là nhiệm vụ tổng thật?"""
    if not profile.keep_parent_as_task:
        return True
    if not _has_assignment(row):
        return True
    if use_deliverable and not row.get(profile.deliverable_field):
        return True
    return False


def detect_profile(rows: list, candidates) -> Profile:
    """Chọn profile đọc được nhiều dòng nhất trong các ứng viên của định dạng file.

    Mỗi kiểu mã hóa dùng một cột mã khác nhau, nên profile sai gần như không
    đọc nổi dòng nào — số dòng dựng được path là tín hiệu đủ rõ để tự chọn.
    Khi không ứng viên nào đọc được (văn bản không có cột mã phân cấp), giữ
    ứng viên đầu tiên để mọi dòng đi qua nguyên trạng thay vì bị loại.
    """
    candidates = list(candidates)
    if not candidates:
        raise ValueError("Khong co profile ung vien nao cho dinh dang nay")

    best = candidates[0]
    best_score = 0
    for profile in candidates:
        score = sum(1 for path in _parse_paths(rows, profile) if path)
        if score > best_score:
            best, best_score = profile, score
    return best


def build_tasks(rows: list, profile: Profile = NUMBER_LETTER) -> list:
    """Dựng danh sách nhiệm vụ chuẩn từ các dòng thô đã đọc được."""
    paths = dedupe_paths(_number_flat_document(_parse_paths(rows, profile)))
    check_paths(paths)

    parent_paths = derive_parent_paths(paths)
    row_by_path = {path: row for path, row in zip(paths, rows) if path}

    deliverable = profile.deliverable_field
    use_deliverable = bool(deliverable) and _column_exists(rows, deliverable)
    if use_deliverable:
        _warn_if_deliverable_is_sparse(
            [row for row, path in zip(rows, paths) if path and path not in parent_paths],
            deliverable,
        )

    # Xác định trước dòng nào là nhãn nhóm, để con trỏ cha chỉ trỏ tới nhiệm vụ
    # thật sự có mặt trong kết quả — nhãn nhóm bị loại thì không thể tra được.
    is_label = [
        bool(path) and path in parent_paths and _is_group_label(row, profile, use_deliverable)
        for row, path in zip(rows, paths)
    ]
    task_paths = {path for path, label in zip(paths, is_label) if path and not label}

    result = []
    for row, path, label in zip(rows, paths, is_label):
        if label:
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
            parent = nearest_existing_ancestor(path, task_paths)
            task["nhom_nhiem_vu"] = root.get("ten_nhiem_vu") if root else None
            task["so_nhom_nhiem_vu"] = path[0]
            task["ma_nhiem_vu"] = profile.join_with.join(path)
            task["ma_nhiem_vu_cha"] = profile.join_with.join(parent) if parent else None
            task["cap_do"] = len(path)
            task["co_nhiem_vu_con"] = path in parent_paths
        else:
            task["nhom_nhiem_vu"] = None
            task["so_nhom_nhiem_vu"] = None
            task["ma_nhiem_vu"] = None
            task["ma_nhiem_vu_cha"] = None
            task["cap_do"] = None
            task["co_nhiem_vu_con"] = False

        for field in profile.drop_fields:
            task.pop(field, None)

        for field in TEXT_FIELDS_TO_CLEAN:
            if field in task:
                task[field] = _rejoin_wrapped_lines(task[field])

        result.append(task)

    return result
