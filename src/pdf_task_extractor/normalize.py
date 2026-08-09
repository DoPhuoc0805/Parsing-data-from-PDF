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

Ngoài ra, dòng nhóm cha còn giữ **số hiệu nhóm** (chính "chi_tiet" của dòng
cha, vd "1", "12") — dùng để ghép thành mã nhiệm vụ đầy đủ cho dòng con
(field "ma_nhiem_vu", vd "1a", "12b": số hiệu nhóm + chữ cái con, bỏ dấu
")"). Với nhiệm vụ độc lập (không có dòng con), mã nhiệm vụ chính là số
hiệu của nó (vd "8"). Field "nhom_so_thu_tu" giữ số hiệu nhóm dạng số
thuần (tách riêng khỏi "nhom_nhiem_vu" là tên nhóm dạng câu) để dễ
sort/group.

Với nhiệm vụ độc lập (không có dòng con), "nhom_nhiem_vu" và
"nhom_so_thu_tu" được điền bằng chính tên/số của nó — vì nó tự là 1 nhóm
chỉ gồm 1 nhiệm vụ, không phải "không thuộc nhóm nào".

Cột "tt" và "chi_tiet" chỉ dùng nội bộ để phân loại/ghép mã, không xuất
hiện trong kết quả cuối (đã có "ma_nhiem_vu" thay thế).

Chưa xử lý ở bước này: dòng "mồ côi" do PDF tách rời 1 câu bị wrap thành
dòng riêng (không khớp mẫu số trần lẫn chữ cái) — các dòng này đi qua
nguyên trạng, "ma_nhiem_vu" của chúng là None vì không xác định được.
"""

from __future__ import annotations

import re

INHERITABLE_FIELDS = ["don_vi_chu_tri", "don_vi_phoi_hop", "san_pham", "thoi_han"]

_BARE_NUMBER = re.compile(r"^\d+$")
_LETTER_CHI_TIET = re.compile(r"^([a-zđ])\)$")


def _is_bare_number(chi_tiet) -> bool:
    return bool(_BARE_NUMBER.match((chi_tiet or "").strip()))


def _letter_suffix(chi_tiet):
    match = _LETTER_CHI_TIET.match((chi_tiet or "").strip())
    return match.group(1) if match else None


def apply_group_inheritance(records: list) -> list:
    """Loại dòng nhóm cha, kế thừa các cột dùng chung xuống dòng con cùng nhóm."""
    result = []
    current_group = None

    for record in records:
        chi_tiet = record.get("chi_tiet")
        is_top_level = _is_bare_number(chi_tiet)

        if is_top_level and not record.get("tt"):
            # Dòng nhóm cha thuần túy (có dòng con a)/b)/c)... phía dưới).
            current_group = {field: record.get(field) for field in INHERITABLE_FIELDS}
            current_group["ten_nhiem_vu"] = record.get("ten_nhiem_vu")
            current_group["so_thu_tu"] = (chi_tiet or "").strip()
            continue

        new_record = dict(record)
        letter = _letter_suffix(chi_tiet)

        if is_top_level:
            # Nhiệm vụ độc lập (không có dòng con) — tự nó là 1 nhóm.
            ma = (chi_tiet or "").strip()
            new_record["nhom_nhiem_vu"] = record.get("ten_nhiem_vu")
            new_record["nhom_so_thu_tu"] = ma
            new_record["ma_nhiem_vu"] = ma
            current_group = None
        elif current_group is not None:
            for field in INHERITABLE_FIELDS:
                if not new_record.get(field):
                    new_record[field] = current_group[field]
            new_record["nhom_nhiem_vu"] = current_group["ten_nhiem_vu"]
            new_record["nhom_so_thu_tu"] = current_group["so_thu_tu"]
            new_record["ma_nhiem_vu"] = current_group["so_thu_tu"] + letter if letter else None
        else:
            new_record["nhom_nhiem_vu"] = None
            new_record["nhom_so_thu_tu"] = None
            new_record["ma_nhiem_vu"] = None

        new_record.pop("tt", None)
        new_record.pop("chi_tiet", None)
        result.append(new_record)

    return result


if __name__ == "__main__":
    import sys

    import pandas as pd

    from .extract_tables import extract_from_pdf

    default_path = "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    output_path = sys.argv[2] if len(sys.argv) > 2 else "data/output/normalized.csv"

    normalized = apply_group_inheritance(extract_from_pdf(pdf_path))
    pd.DataFrame(normalized).to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Da xuat {len(normalized)} record ra {output_path}", file=sys.stderr)
