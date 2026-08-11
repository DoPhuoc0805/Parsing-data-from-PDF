"""Unit test cho tasks.py: loại dòng nhóm cha, kế thừa cột dùng chung."""

from pathlib import Path

from src.task_extractor.profiles import (
    DECIMAL_INDEX,
    DOTTED_CODE,
    NUMBER_LETTER,
    PROFILES_BY_SUFFIX,
)
from src.task_extractor.read_excel import read_excel
from src.task_extractor.read_pdf import read_pdf
from src.task_extractor.tasks import build_tasks, detect_profile

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
KH277_PDF = DATA_DIR / "kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
CV6582_PDF = DATA_DIR / "CV 6582.pdf"
TEST2_XLSX = DATA_DIR / "test_2.xlsx"
TEST3_XLSX = DATA_DIR / "test_3.xlsx"


def _kh277_tasks():
    return build_tasks(read_pdf(str(KH277_PDF)))


def _by_ma(tasks, ma_nhiem_vu):
    return next(t for t in tasks if t["ma_nhiem_vu"] == ma_nhiem_vu)


def test_kh277_drops_exactly_the_pure_group_headers():
    rows = read_pdf(str(KH277_PDF))
    tasks = build_tasks(rows)
    # 8 nhom co header thuan tuy (1,2,3,4,5,6,7,12) bi loai khoi ket qua.
    assert len(tasks) == len(rows) - 8


def test_tt_and_chi_tiet_columns_are_removed():
    for task in _kh277_tasks():
        assert "tt" not in task
        assert "chi_tiet" not in task


def test_tt_column_is_no_longer_needed_to_tell_group_from_task():
    # Truoc day phai dua vao cot "tt" de phan biet dong tieu de nhom voi nhiem
    # vu doc lap (ca hai deu co chi_tiet la so tran). Mo hinh path suy ra tu
    # "co dong con hay khong" nen bo han cot tt van cho ket qua y het.
    rows = read_pdf(str(KH277_PDF))
    without_tt = [{k: v for k, v in row.items() if k != "tt"} for row in rows]

    assert build_tasks(without_tt) == build_tasks(rows)


def test_group_with_shared_coordination_and_deadline_is_inherited():
    children = [
        t for t in _kh277_tasks() if (t.get("nhom_nhiem_vu") or "").startswith("Làm sạch")
    ]

    assert len(children) == 8
    for task in children:
        assert task["don_vi_phoi_hop"] == "Sở Khoa học và Công nghệ"
        assert task["thoi_han"] == "30/8/2026"
        assert task["so_nhom_nhiem_vu"] == "1"

    # Don vi chu tri van rieng theo tung dong con, khong bi ghi de.
    assert _by_ma(children, "1a")["don_vi_chu_tri"] == "Sở Tài chính"
    assert _by_ma(children, "1g")["don_vi_chu_tri"] == "Sở Y tế"


def test_group_2_uses_its_own_group_number_not_global_tt():
    tasks = _kh277_tasks()
    # Cac dong con nay co "tt" toan cuc la 9,10 nhung phai dung so nhom cua no (2), khong phai 9/10.
    assert _by_ma(tasks, "2a")["ten_nhiem_vu"].startswith("Đối với khoảng 3,2 triệu")
    assert _by_ma(tasks, "2b")["ten_nhiem_vu"].startswith("Đối với khoảng 950.000")


def test_no_row_is_left_without_a_task_code():
    # Dong bi ngat trang (khong co tt/chi_tiet) da duoc gop lai o read_pdf,
    # nen sau buoc nay khong con dong nao thieu ma_nhiem_vu.
    assert all(t["ma_nhiem_vu"] is not None for t in _kh277_tasks())


def test_group_with_shared_lead_unit_is_inherited():
    tasks = _kh277_tasks()
    expected_chu_tri = "Các Sở, ban, ngành; UBND các xã, phường"
    assert _by_ma(tasks, "12a")["don_vi_chu_tri"] == expected_chu_tri
    assert _by_ma(tasks, "12b")["don_vi_chu_tri"] == expected_chu_tri


def test_children_with_own_values_are_not_overwritten():
    tasks = _kh277_tasks()
    assert _by_ma(tasks, "2a")["thoi_han"] == "30/7/2026"
    assert _by_ma(tasks, "2b")["thoi_han"] == "30/8/2026"


def test_standalone_task_uses_itself_as_its_own_group():
    task = _by_ma(_kh277_tasks(), "8")
    assert task["nhom_nhiem_vu"] == task["ten_nhiem_vu"]
    assert task["so_nhom_nhiem_vu"] == "8"
    assert task["don_vi_chu_tri"] == "Sở Văn hóa và Thể thao"


def test_wrapped_lines_are_rejoined_but_bullets_are_kept_separate():
    task = _by_ma(_kh277_tasks(), "4a")
    lines = task["san_pham"].split("\n")

    # 3 gach dau dong that su, moi gach lien mach khong con bi ngat giua dong.
    assert len(lines) == 3
    assert all(line.startswith("-") for line in lines)
    assert "thời gian giải quyết, 50% thành phần hồ sơ." in lines[-1]


_ADDED_FIELDS = ["nhom_nhiem_vu", "so_nhom_nhiem_vu", "ma_nhiem_vu"]
_DROPPED_FIELDS = ["tt", "chi_tiet"]


def test_cv6582_records_have_no_group_context():
    rows = read_pdf(str(CV6582_PDF))
    tasks = build_tasks(rows)

    assert len(tasks) == len(rows) == 12
    for task in tasks:
        assert all(task[field] is None for field in _ADDED_FIELDS)
        assert all(field not in task for field in _DROPPED_FIELDS)


def test_cv6582_wrapped_unit_names_are_rejoined():
    task = build_tasks(read_pdf(str(CV6582_PDF)))[0]
    # Ten don vi bi PDF wrap chu (vd "Sở KHCN,\nTập đoàn\nViettel") duoc noi lien.
    assert "\n" not in task["don_vi_phoi_hop"]
    assert task["don_vi_phoi_hop"] == "Sở KHCN, Tập đoàn Viettel"


# --------------------------------------------------------------- chọn profile
def _detect(path):
    reader = read_excel if path.suffix == ".xlsx" else read_pdf
    return detect_profile(reader(str(path)), PROFILES_BY_SUFFIX[path.suffix])


def test_profile_is_detected_from_the_code_column_in_use():
    assert _detect(TEST2_XLSX) is DOTTED_CODE
    assert _detect(TEST3_XLSX) is DECIMAL_INDEX
    assert _detect(KH277_PDF) is NUMBER_LETTER


def test_document_without_any_code_column_still_gets_a_profile():
    # CV6582 khong co cot ma phan cap nao -> moi dong di qua nguyen trang.
    assert _detect(CV6582_PDF) is NUMBER_LETTER


# --------------------------------------------------------------- Excel: mã phân cấp
def _test2_tasks():
    return build_tasks(read_excel(str(TEST2_XLSX)), DOTTED_CODE)


def test_test2_drops_label_rows_but_keeps_summary_tasks():
    rows = read_excel(str(TEST2_XLSX))
    tasks = _test2_tasks()
    # 178 dong - 23 dong nhan nhom = 155. Nhan nhom gom: 20 chuong muc cap 1
    # va 3 dong cap sau khong giao viec cho don vi nao.
    assert len(rows) == 178
    assert len(tasks) == 155


def test_test2_level_one_is_always_a_label_even_with_a_lead_unit():
    # N14/N19 co ghi don vi chu tri nhung khong kem san pham dau ra — do la
    # "chuong nay thuoc trach nhiem ai", khong phai mot viec cu the.
    codes = {t["ma_nhiem_vu"] for t in _test2_tasks()}
    assert "KH20_TT_N14" not in codes
    assert "KH20_TT_N19" not in codes
    # Nhung nhiem vu tong o cap sau thi van giu, du cung khong co san pham.
    assert "KH20_TT_N01.1" in codes


def test_test2_level_one_without_children_is_still_a_task():
    # Luat chi ap cho dong CO con; ma 1 doan dung mot minh van la nhiem vu that.
    codes = {t["ma_nhiem_vu"] for t in _test2_tasks()}
    assert {f"TB200_N0{i}" for i in range(1, 7)} <= codes


def test_test2_parent_with_its_own_assignment_stays_a_task():
    # N01.1 vua co dong con, vua co don vi chu tri rieng -> la nhiem vu tong that.
    codes = {t["ma_nhiem_vu"] for t in _test2_tasks()}
    assert "KH20_TT_N01.1" in codes
    assert "KH20_TT_N01.1.1" in codes


def test_test2_parent_without_assignment_is_dropped_as_label():
    codes = {t["ma_nhiem_vu"] for t in _test2_tasks()}
    assert "KH20_TT_N01" not in codes
    assert "KH20_TT_N13" not in codes


def test_test2_group_context_comes_from_the_root_code():
    task = _by_ma(_test2_tasks(), "KH20_TT_N01.1.1")
    assert task["so_nhom_nhiem_vu"] == "KH20_TT_N01"
    assert task["nhom_nhiem_vu"].startswith("Tập trung cao độ")


def test_test2_standalone_code_is_kept_as_its_own_group():
    # TB200_N01 la ma 1 doan nhung khong co dong con -> nhiem vu doc lap, phai giu.
    task = _by_ma(_test2_tasks(), "TB200_N01")
    assert task["so_nhom_nhiem_vu"] == "TB200_N01"
    assert task["don_vi_chu_tri"] == "Sở Tài chính"


def test_test2_missing_middle_level_does_not_lose_its_children():
    # Van ban sot dong N05.1 nhung 5 dong con van phai vao dung nhom goc N05.
    children = [t for t in _test2_tasks() if t["ma_nhiem_vu"].startswith("KH20_TT_N05.1.")]
    assert len(children) == 5
    assert {t["so_nhom_nhiem_vu"] for t in children} == {"KH20_TT_N05"}


# --------------------------------------------------------------- Excel: số thập phân
def _test3_tasks():
    return build_tasks(read_excel(str(TEST3_XLSX)), DECIMAL_INDEX)


def test_test3_keeps_every_row_because_parents_are_real_tasks():
    rows = read_excel(str(TEST3_XLSX))
    assert len(_test3_tasks()) == len(rows) == 375


def test_test3_trailing_zero_means_the_task_itself():
    # "13.0" la nhiem vu so 13, khong phai con thu 0 cua no.
    task = _by_ma(_test3_tasks(), "13")
    assert task["ten_nhiem_vu"] == "Công tác biên chế thường xuyên"


def test_test3_children_belong_to_their_decimal_parent():
    task = _by_ma(_test3_tasks(), "13.5")
    assert task["so_nhom_nhiem_vu"] == "13"
    assert task["nhom_nhiem_vu"] == "Công tác biên chế thường xuyên"


def test_test3_duplicate_codes_are_made_unique():
    # 3 cap ma bi trung do loi danh so o van ban goc -> them hau to de dung
    # duoc lam khoa chinh, thay vi chan ca tai lieu.
    codes = [t["ma_nhiem_vu"] for t in _test3_tasks()]
    assert len(codes) == len(set(codes))
    assert {"122a", "122b", "194a", "194b"} <= set(codes)
