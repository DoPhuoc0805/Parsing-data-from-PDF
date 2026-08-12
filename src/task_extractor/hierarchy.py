"""
Mô hình đường dẫn phân cấp (path) — cơ chế dùng chung cho mọi loại văn bản.

Mỗi dòng được quy về **một đường dẫn**: tuple các đoạn thể hiện vị trí của nó
trong cây nhiệm vụ (vd ("12", "b") hay ("KH20_TT_N01", "1", "1")). Từ path,
mọi kết luận đều suy ra được bằng logic chung, không cần luật riêng cho từng
loại văn bản:

- mã nhiệm vụ      = path nối lại
- cha              = path bỏ đoạn cuối
- cấp độ           = độ dài path
- **là nhiệm vụ cha hay không = có dòng nào khác nằm dưới nó hay không**

Điểm cuối cùng là mấu chốt: thay vì khai báo luật "dòng thế nào là nhóm cha"
cho từng loại văn bản, ta **suy ra từ chính dữ liệu**. Nhờ vậy các trường hợp
mập mờ tự tan biến — vd trong PDF, "8" là nhiệm vụ độc lập còn "1" là tiêu đề
nhóm, khác nhau chỉ vì "1" có dòng con còn "8" thì không.

Chỉ có 2 họ cách đọc mã, đủ cho mọi văn bản đã gặp:

- **Tuyệt đối**: mã tự chứa đủ đường dẫn, tách theo dấu phân cách
  (vd "KH20_TT_N01.1.1", "13.10").
- **Tương đối**: mã chỉ chứa đoạn cuối, cấp được xác định theo kiểu ký tự rồi
  ghép với ngăn xếp đang chạy (vd PDF: "12" là cấp 1, "b)" là cấp 2).

Dòng không đọc được mã (vd văn bản không có cột mã phân cấp nào) nhận path
None và đi qua nguyên trạng, không thuộc cây.
"""

from __future__ import annotations

import logging
import string
from collections import Counter

logger = logging.getLogger(__name__)


def parse_absolute_paths(codes: list, separator: str = ".", self_segment=None) -> list:
    """Mã tự chứa đủ đường dẫn — tách theo dấu phân cách.

    self_segment: đoạn cuối mang nghĩa "chính nó" chứ không phải 1 cấp con
    (vd test_3 dùng "1.0" để chỉ nhiệm vụ số 1, không phải con thứ 0 của nó).
    """
    paths: list = []
    for code in codes:
        text = str(code).strip() if code is not None else ""
        if not text:
            paths.append(None)
            continue
        segments = text.split(separator)
        if self_segment is not None and len(segments) > 1 and segments[-1] == self_segment:
            segments = segments[:-1]
        paths.append(tuple(segments))
    return paths


def parse_relative_paths(codes: list, level_patterns: list) -> list:
    """Mã chỉ chứa đoạn cuối — cấp xác định theo mẫu ký tự, ghép với ngăn xếp.

    level_patterns[i] là regex của cấp i+1; nhóm bắt đầu tiên là đoạn path.
    Dòng có cấp n nhưng chưa có đủ tổ tiên cấp n-1 phía trên thì không dựng
    được path (trả None) thay vì bịa ra đoạn rỗng.
    """
    paths = []
    stack: list = []
    for code in codes:
        text = str(code).strip() if code is not None else ""
        segment = None
        level = 0
        for index, pattern in enumerate(level_patterns):
            match = pattern.match(text)
            if match:
                segment = match.group(1)
                level = index + 1
                break

        if segment is None or len(stack) < level - 1:
            paths.append(None)
            continue

        stack = stack[: level - 1] + [segment]
        paths.append(tuple(stack))
    return paths


def dedupe_paths(paths: list) -> list:
    """Thêm hậu tố a/b/c... vào các path trùng nhau để mã nhiệm vụ dùng được
    làm khóa chính. Mã trùng là lỗi đánh số ở văn bản gốc, không phải lỗi đọc
    file — nên chỉ cảnh báo rồi chạy tiếp, không chặn cả tài liệu."""
    counts = Counter(path for path in paths if path)
    duplicated = {path for path, count in counts.items() if count > 1}
    if not duplicated:
        return paths

    seen: Counter = Counter()
    result = []
    for path in paths:
        if path is None or path not in duplicated:
            result.append(path)
            continue
        index = seen[path]
        seen[path] += 1
        suffix = string.ascii_lowercase[index] if index < 26 else str(index + 1)
        renamed = path[:-1] + (path[-1] + suffix,)
        logger.warning("Ma trung lap %r -> doi thanh %r", path, renamed)
        result.append(renamed)
    return result


def derive_parent_paths(paths: list) -> set:
    """Tập các path có ít nhất 1 nhiệm vụ con nằm dưới."""
    parents = set()
    for path in paths:
        if not path:
            continue
        for depth in range(1, len(path)):
            parents.add(path[:depth])
    return parents


def nearest_existing_ancestor(path: tuple, known: set):
    """Tổ tiên gần nhất nằm trong tập `known`.

    Một tổ tiên có thể vắng mặt vì hai lý do: văn bản sót cấp trung gian (vd có
    N05 và N05.1.1 nhưng thiếu N05.1), hoặc dòng đó chỉ là nhãn nhóm nên không
    vào kết quả. Cả hai trường hợp đều phải bỏ qua để khóa ngoại luôn tra được
    — thay vì để con trỏ treo hoặc bịa ra một nhiệm vụ không có thật. Truyền
    vào tập mã **thực sự có trong kết quả**, không phải mọi mã đọc được.
    """
    for depth in range(len(path) - 1, 0, -1):
        if path[:depth] in known:
            return path[:depth]
    return None


def check_paths(paths: list) -> None:
    """Cảnh báo về các cấp trung gian bị thiếu trong văn bản gốc."""
    known = {path for path in paths if path}
    for path in sorted(known):
        if len(path) > 1 and path[:-1] not in known:
            logger.warning("Ma %r tham chieu cap cha %r khong ton tai", path, path[:-1])
