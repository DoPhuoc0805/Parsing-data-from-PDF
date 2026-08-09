# Parsing data from PDF

Công cụ trích xuất bảng phân công nhiệm vụ (nhiệm vụ → đơn vị chủ trì/phối hợp) từ file PDF hành chính.

## Mục tiêu

- **Input:** File PDF chứa bảng phân công nhiệm vụ (vd: Phụ lục kế hoạch triển khai chuyển đổi số).
- **Output:** File CSV, mỗi dòng là 1 nhiệm vụ với: mã nhiệm vụ, tên nhiệm vụ, đơn vị chủ trì, đơn vị phối hợp, sản phẩm (nếu có), thời hạn, tên nhóm nhiệm vụ.

## Trạng thái hiện tại

Pipeline gồm 3 bước, cả 3 đã code xong và có test:

| Module | Vai trò | Trạng thái |
|---|---|---|
| `src/pdf_task_extractor/locate_tables.py` | Xác định trang/vị trí bảng nhiệm vụ trong PDF, ánh xạ cột theo tên trường chuẩn | ✅ Xong |
| `src/pdf_task_extractor/extract_tables.py` | Trích xuất dữ liệu thô, gộp bảng bị ngắt qua nhiều trang (kể cả dòng bị PDF cắt ngang do rơi đúng ranh giới trang) | ✅ Xong |
| `src/pdf_task_extractor/normalize.py` | Loại dòng nhóm cha, kế thừa cột dùng chung xuống dòng con, ghép mã nhiệm vụ, **xuất CSV** | ✅ Xong |

Các file sau **mới chỉ có docstring, chưa có code** — chưa dùng được:

- `src/pdf_task_extractor/pipeline.py`
- `src/pdf_task_extractor/validate.py`
- `scripts/run_extract.py`

Hiện tại `normalize.py` đang tạm đảm nhiệm luôn việc "chạy toàn bộ pipeline + xuất file", nên vẫn dùng được đầy đủ chức năng qua lệnh ở mục Chạy thử bên dưới.

## Cấu trúc thư mục

```
data/raw/         PDF gốc đầu vào (2 file mẫu: kh-cao-diem-100-ngay-c-s-tp-hn.pdf, CV 6582.pdf)
data/output/      Kết quả xuất ra (CSV, không commit vào git)
src/pdf_task_extractor/
    locate_tables.py   Bước 1
    extract_tables.py  Bước 2
    normalize.py       Bước 3 (+ CLI xuất CSV)
    validate.py        (chưa code)
    pipeline.py        (chưa code)
tests/                 Unit test cho 3 module đã xong (21 test)
scripts/run_extract.py (chưa code)
notebooks/exploration.ipynb
```

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy thử

Chạy toàn bộ 3 bước và xuất CSV kết quả cuối cùng:

```bash
python -m src.pdf_task_extractor.normalize "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf" "data/output/kh277_normalized.csv"
python -m src.pdf_task_extractor.normalize "data/raw/CV 6582.pdf" "data/output/cv6582_normalized.csv"
```

Tham số 1: file PDF input. Tham số 2 (tùy chọn): đường dẫn CSV output, mặc định `data/output/normalized.csv`.

Muốn xem kết quả trung gian từng bước (in ra màn hình, không lưu file) để debug:

```bash
python -m src.pdf_task_extractor.locate_tables "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
python -m src.pdf_task_extractor.extract_tables "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
```

## Chạy test

```bash
python -m pytest tests/ -v
```

## Schema output (sau Bước 3)

| Field | Ý nghĩa |
|---|---|
| `ma_nhiem_vu` | Mã nhiệm vụ, vd "1a", "12b" (số nhóm + chữ cái con); nhiệm vụ độc lập thì là số riêng của nó, vd "8" |
| `ten_nhiem_vu` | Tên/nội dung nhiệm vụ |
| `don_vi_chu_tri` | Đơn vị chủ trì |
| `don_vi_phoi_hop` | Đơn vị phối hợp |
| `san_pham` | Sản phẩm đầu ra (nếu file gốc có cột này) |
| `thoi_han` | Thời hạn hoặc số ngày dự kiến |
| `nhom_nhiem_vu` | Tên nhóm nhiệm vụ lớn mà dòng này thuộc về (nhiệm vụ độc lập thì bằng chính `ten_nhiem_vu` của nó) |
| `nhom_so_thu_tu` | Số hiệu nhóm dạng số thuần, tiện sort/filter |

Cột `tt`, `chi_tiet` chỉ dùng nội bộ trong quá trình xử lý, không xuất hiện trong CSV cuối cùng.

## Dữ liệu mẫu

- `data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf` — Kế hoạch triển khai đợt cao điểm 100 ngày chuyển đổi số Thành phố Hà Nội (bảng nhiệm vụ ở Phụ lục, 7 cột, header 2 dòng).
- `data/raw/CV 6582.pdf` — Công văn Sở Y tế Hà Nội về di trú Hồ sơ sức khỏe điện tử (bảng "Kế hoạch sơ bộ di trú dữ liệu", 5 cột, header 1 dòng) — dùng để kiểm tra pipeline tổng quát hóa được với cấu trúc bảng khác KH277.
