"""
Bước 3: Loại dòng nhóm cha, kế thừa các cột dùng chung xuống dòng con.

PDF gốc dùng merged cell theo nhóm nhiệm vụ: một số cột (đơn vị chủ trì,
đơn vị phối hợp, sản phẩm, thời hạn) chỉ được ghi 1 lần ở dòng đầu nhóm,
các dòng con bị trống ở đúng những cột đó dù thực chất áp dụng chung. Dòng
nhóm cha được nhận diện bằng "tt" rỗng và "chi_tiet" là số trần (vd "1",
"12") — khác với dòng con dùng "chi_tiet" dạng chữ cái (vd "a)").

Dòng nhóm cha không có đơn vị chủ trì cụ thể nên không phải 1 nhiệm vụ
được giao thực sự; bị loại khỏi kết quả cuối, chỉ giữ tên nhóm làm ngữ
cảnh (field "nhom_nhiem_vu") gắn vào từng dòng con.

Quy tắc kế thừa: chỉ điền giá trị từ dòng cha khi ô của dòng con đang
rỗng, không bao giờ ghi đè giá trị dòng con đã có sẵn — quy tắc này áp
dụng đồng nhất cho cả 4 cột (kể cả đơn vị chủ trì, vì đã kiểm chứng có
nhóm mà đơn vị chủ trì cũng dùng chung, không phải lúc nào cũng riêng
theo từng dòng con).

Chưa xử lý ở bước này: dòng "mồ côi" do PDF tách rời 1 câu bị wrap thành
dòng riêng (không khớp mẫu số trần lẫn chữ cái) — các dòng này đi qua
nguyên trạng.
"""

from __future__ import annotations

import re

INHERITABLE_FIELDS = ["don_vi_chu_tri", "don_vi_phoi_hop", "san_pham", "thoi_han"]

_BARE_NUMBER = re.compile(r"^\d+$")


def _is_bare_number(chi_tiet) -> bool:
    return bool(_BARE_NUMBER.match((chi_tiet or "").strip()))


def apply_group_inheritance(records: list) -> list:
    """Loại dòng nhóm cha, kế thừa các cột dùng chung xuống dòng con cùng nhóm."""
    result = []
    current_group = None

    for record in records:
        is_top_level = _is_bare_number(record.get("chi_tiet"))

        if is_top_level and not record.get("tt"):
            # Dòng nhóm cha thuần túy (có dòng con a)/b)/c)... phía dưới).
            current_group = {field: record.get(field) for field in INHERITABLE_FIELDS}
            current_group["ten_nhiem_vu"] = record.get("ten_nhiem_vu")
            continue

        new_record = dict(record)

        if is_top_level:
            # Nhiệm vụ độc lập (không có dòng con) — không thuộc nhóm nào.
            new_record["nhom_nhiem_vu"] = None
            current_group = None
        elif current_group is not None:
            for field in INHERITABLE_FIELDS:
                if not new_record.get(field):
                    new_record[field] = current_group[field]
            new_record["nhom_nhiem_vu"] = current_group["ten_nhiem_vu"]
        else:
            new_record["nhom_nhiem_vu"] = None

        result.append(new_record)

    return result
