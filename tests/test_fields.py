"""Unit test cho fields.py: ánh xạ tiêu đề cột về trường chuẩn."""

from src.task_extractor.fields import is_task_header, match_header_fields


def test_match_header_fields_finds_required_field_on_second_row():
    # Mô phỏng header 2 tầng, nơi "Đơn vị chủ trì" rơi xuống dòng thứ 2
    row0 = ["Stt", None, "Tên nhiệm vụ", None, "Đơn vị phối hợp", "Sản phẩm", "Thời hạn"]
    row1 = ["TT", "Chi tiết", None, "Đơn vị chủ trì", None, None, None]

    mapping = match_header_fields([row0, row1])

    assert mapping[3] == "don_vi_chu_tri"
    assert mapping[4] == "don_vi_phoi_hop"


def test_match_header_fields_is_case_insensitive():
    row0 = ["TT", "CÔNG VIỆC", "ĐƠN VỊ CHỦ TRÌ", "ĐƠN VỊ PHỐI HỢP"]

    mapping = match_header_fields([row0])

    assert mapping[2] == "don_vi_chu_tri"
    assert mapping[3] == "don_vi_phoi_hop"


def test_is_task_header_requires_both_units():
    assert is_task_header({0: "don_vi_chu_tri", 1: "don_vi_phoi_hop"})
    assert not is_task_header({0: "don_vi_chu_tri", 1: "san_pham"})
