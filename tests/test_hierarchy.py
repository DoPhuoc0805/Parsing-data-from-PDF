"""Unit test cho hierarchy.py — mô hình path dùng chung.

Các mã dùng trong test là **mã thật** lấy từ 3 nguồn hiện có, để cơ chế được
kiểm chứng trên dữ liệu thật ngay cả trước khi phần đọc Excel được viết.
"""

import logging

from src.task_extractor.hierarchy import (
    check_paths,
    dedupe_paths,
    derive_parent_paths,
    nearest_existing_ancestor,
    parse_absolute_paths,
    parse_relative_paths,
)
from src.task_extractor.profiles import NUMBER_LETTER

PDF_LEVEL_PATTERNS = list(NUMBER_LETTER.level_patterns)


# --------------------------------------------------------------- mã tương đối (PDF)
def test_relative_paths_build_from_running_stack():
    paths = parse_relative_paths(["1", "a)", "b)", "2", "a)"], PDF_LEVEL_PATTERNS)
    assert paths == [("1",), ("1", "a"), ("1", "b"), ("2",), ("2", "a")]


def test_relative_paths_use_group_number_not_global_counter():
    # Dòng con của nhóm 2 phải ra "2a", không phải theo số thứ tự toàn cục.
    paths = parse_relative_paths(["1", "a)", "2", "a)"], PDF_LEVEL_PATTERNS)
    assert "".join(paths[-1]) == "2a"


def test_relative_paths_return_none_for_unreadable_code():
    # CV6582 không có cột mã phân cấp -> mọi dòng đều None, đi qua nguyên trạng.
    assert parse_relative_paths([None, "", "khong phai ma"], PDF_LEVEL_PATTERNS) == [
        None,
        None,
        None,
    ]


def test_relative_paths_reject_child_without_parent_above():
    # Chữ cái xuất hiện trước khi có cấp 1 nào -> không dựng được path, không bịa đoạn rỗng.
    assert parse_relative_paths(["a)"], PDF_LEVEL_PATTERNS) == [None]


# --------------------------------------------------------------- mã tuyệt đối (Excel)
def test_absolute_paths_split_dotted_code():
    # Mã thật của test_2.xlsx
    codes = ["KH20_TT_N05", "KH20_TT_N05.1.1", "KH20_TT_N05.2", "TB200_N01"]
    assert parse_absolute_paths(codes) == [
        ("KH20_TT_N05",),
        ("KH20_TT_N05", "1", "1"),
        ("KH20_TT_N05", "2"),
        ("TB200_N01",),
    ]


def test_absolute_paths_treat_trailing_zero_as_self():
    # Mã thật của test_3.xlsx: openpyxl trả 1.0 dạng float, "13.10" dạng chuỗi.
    codes = [1.0, 13.1, "13.10", 3.5]
    assert parse_absolute_paths(codes, self_segment="0") == [
        ("1",),
        ("13", "1"),
        ("13", "10"),
        ("3", "5"),
    ]


# --------------------------------------------------------------- suy ra cây
def test_parent_is_derived_from_data_not_declared():
    # "1" có dòng con nên là nhóm cha; "8" không có con nên là nhiệm vụ độc lập.
    paths = [("1",), ("1", "a"), ("8",)]
    parents = derive_parent_paths(paths)
    assert ("1",) in parents
    assert ("8",) not in parents


def test_parent_set_includes_missing_intermediate_level():
    # test_2 thiếu dòng N05.1 nhưng N05.1.1 tồn tại -> N05.1 vẫn là cấp cha (ảo).
    parents = derive_parent_paths([("KH20_TT_N05",), ("KH20_TT_N05", "1", "1")])
    assert ("KH20_TT_N05", "1") in parents


def test_nearest_ancestor_skips_missing_level():
    known = {("KH20_TT_N05",), ("KH20_TT_N05", "1", "1")}
    ancestor = nearest_existing_ancestor(("KH20_TT_N05", "1", "1"), known)
    assert ancestor == ("KH20_TT_N05",)


def test_nearest_ancestor_is_none_for_top_level():
    assert nearest_existing_ancestor(("8",), {("8",)}) is None


# --------------------------------------------------------------- toàn vẹn
def test_duplicate_codes_get_suffix_and_warning(caplog):
    # test_3 có 3 cặp mã trùng do lỗi đánh số ở văn bản gốc (vd 122 xuất hiện 2 lần).
    with caplog.at_level(logging.WARNING):
        result = dedupe_paths([("122",), ("122",), ("123",)])

    assert result == [("122a",), ("122b",), ("123",)]
    assert "trung lap" in caplog.text


def test_unique_codes_are_left_untouched():
    paths = [("1",), ("1", "a"), ("2",)]
    assert dedupe_paths(paths) == paths


def test_missing_parent_level_is_warned(caplog):
    with caplog.at_level(logging.WARNING):
        check_paths([("KH20_TT_N05",), ("KH20_TT_N05", "1", "1")])

    assert "khong ton tai" in caplog.text


def test_complete_hierarchy_produces_no_warning(caplog):
    with caplog.at_level(logging.WARNING):
        check_paths([("1",), ("1", "a"), ("1", "b")])

    assert caplog.text == ""
