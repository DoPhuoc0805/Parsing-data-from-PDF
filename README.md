# Parsing data from PDF

Công cụ trích xuất bảng phân công nhiệm vụ (nhiệm vụ → đơn vị chủ trì/phối hợp) từ file PDF hành chính.

## Mục tiêu

- **Input:** File PDF chứa bảng phân công nhiệm vụ (vd: Phụ lục kế hoạch triển khai chuyển đổi số).
- **Output:** File CSV hoặc JSON, mỗi dòng/phần tử là 1 nhiệm vụ với: mã nhiệm vụ, tên nhiệm vụ, đơn vị chủ trì, đơn vị phối hợp, sản phẩm (nếu có), thời hạn, tên nhóm nhiệm vụ.

## Trạng thái hiện tại

| Module | Vai trò | Trạng thái |
|---|---|---|
| `src/pdf_task_extractor/locate_tables.py` | Bước 1: xác định trang/vị trí bảng nhiệm vụ trong PDF, ánh xạ cột theo tên trường chuẩn | ✅ Xong |
| `src/pdf_task_extractor/extract_tables.py` | Bước 2: trích xuất dữ liệu thô, gộp bảng bị ngắt qua nhiều trang (kể cả dòng bị PDF cắt ngang do rơi đúng ranh giới trang) | ✅ Xong |
| `src/pdf_task_extractor/normalize.py` | Bước 3: loại dòng nhóm cha, kế thừa cột dùng chung xuống dòng con, ghép mã nhiệm vụ | ✅ Xong |
| `src/pdf_task_extractor/pipeline.py` | Nối Bước 1→2→3, xuất kết quả ra CSV/JSON | ✅ Xong |
| `scripts/run_extract.py` | CLI chính thức (`--input`/`--output`), gọi `pipeline.py` | ✅ Xong |
| `src/pdf_task_extractor/validate.py` | Kiểm tra chất lượng dữ liệu sau normalize | ⏳ Mới có docstring, chưa code |

## Cấu trúc thư mục

```
data/raw/         PDF gốc đầu vào (2 file mẫu: kh-cao-diem-100-ngay-c-s-tp-hn.pdf, CV 6582.pdf)
data/output/      Kết quả xuất ra (CSV/JSON, không commit vào git)
src/pdf_task_extractor/
    locate_tables.py   Bước 1
    extract_tables.py  Bước 2
    normalize.py       Bước 3 (+ export_records dùng chung cho CSV/JSON)
    pipeline.py        Nối Bước 1-2-3, xuất kết quả
    validate.py        (chưa code)
tests/                 Unit test cho 4 module đã xong (25 test)
scripts/run_extract.py CLI chính thức
notebooks/exploration.ipynb
```

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy thử

Cách dùng chính thức — gọi qua CLI `scripts/run_extract.py`:

```bash
python scripts/run_extract.py --input "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf" --output "data/output/kh277_normalized.csv"
python scripts/run_extract.py --input "data/raw/CV 6582.pdf" --output "data/output/cv6582_normalized.json"
```

**Định dạng output được chọn tự động theo đuôi file** truyền vào `--output` — không cần thêm flag nào khác:

- Đuôi `.csv` → xuất CSV bằng `pandas`.
- Đuôi `.json` → xuất JSON (dùng `json.dump` chuẩn, không cần cài thêm thư viện).

Nên ưu tiên dùng JSON khi cần xử lý tiếp bằng code (giữ đúng kiểu dữ liệu, `None` hiện thành `null` thay vì `NaN` gây khó đọc khi mở CSV bằng Excel/Jupyter) — dùng CSV khi cần mở trực tiếp bằng Excel để xem/lọc bằng tay.

Muốn xem kết quả trung gian từng bước riêng lẻ (in ra màn hình, không lưu file) để debug:

```bash
python -m src.pdf_task_extractor.locate_tables "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
python -m src.pdf_task_extractor.extract_tables "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
python -m src.pdf_task_extractor.normalize "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf" "data/output/kh277_normalized.csv"
```

Lệnh `normalize` ở trên vẫn xuất được file đầy đủ như `run_extract.py` (dùng khi chỉ muốn chạy riêng Bước 3 để debug) — nhưng khuyến khích dùng `scripts/run_extract.py` làm điểm vào chính thức.

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

Cột `tt`, `chi_tiet` chỉ dùng nội bộ trong quá trình xử lý, không xuất hiện trong CSV/JSON cuối cùng.

## Dữ liệu mẫu

- `data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf` — Kế hoạch triển khai đợt cao điểm 100 ngày chuyển đổi số Thành phố Hà Nội (bảng nhiệm vụ ở Phụ lục, 7 cột, header 2 dòng).
- `data/raw/CV 6582.pdf` — Công văn Sở Y tế Hà Nội về di trú Hồ sơ sức khỏe điện tử (bảng "Kế hoạch sơ bộ di trú dữ liệu", 5 cột, header 1 dòng) — dùng để kiểm tra pipeline tổng quát hóa được với cấu trúc bảng khác KH277.
