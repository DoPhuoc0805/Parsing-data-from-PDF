# Parsing data from PDF

Công cụ trích xuất bảng phân công nhiệm vụ (nhiệm vụ → đơn vị chủ trì/phối hợp) từ file PDF hành chính, xuất ra CSV hoặc JSON.

## Mục tiêu

- **Input:** File PDF chứa bảng phân công nhiệm vụ (vd: Phụ lục kế hoạch triển khai chuyển đổi số).
- **Output:** File CSV hoặc JSON, mỗi dòng/phần tử là 1 nhiệm vụ với: mã nhiệm vụ, tên nhiệm vụ, đơn vị chủ trì, đơn vị phối hợp, sản phẩm (nếu có), thời hạn, tên nhóm nhiệm vụ.

## Cách hoạt động

Pipeline gồm 3 bước, nối lại qua `pipeline.py`:

1. **`locate_tables.py`** — quét từng trang PDF, xác định bảng nào là bảng phân công nhiệm vụ (dựa vào header khớp các trường chuẩn như "Đơn vị chủ trì"/"Đơn vị thực hiện", "Đơn vị phối hợp" — không hard-code theo 1 mẫu cột cố định), xử lý được cả bảng bị ngắt qua nhiều trang.
2. **`extract_tables.py`** — trích xuất dữ liệu thô từ các bảng đã xác định, gộp lại các dòng bị PDF cắt ngang do rơi đúng ranh giới trang (1 câu bị tách thành 2 dòng rác).
3. **`normalize.py`** — loại bỏ dòng nhóm cha (tiêu đề nhóm không phải nhiệm vụ cụ thể), kế thừa các cột dùng chung (đơn vị chủ trì/phối hợp, sản phẩm, thời hạn) xuống từng dòng con, ghép mã nhiệm vụ (vd "1a", "12b"), nối lại các dòng bị PDF wrap chữ giữa dòng trong khi vẫn giữ nguyên gạch đầu dòng thật.

Toàn bộ pipeline đã được kiểm chứng chạy đúng trên 2 file PDF có cấu trúc bảng khác nhau hoàn toàn (7 cột/header 2 dòng và 5 cột/header 1 dòng) — không cần code riêng cho từng loại file.

## Cấu trúc thư mục

```
data/raw/         PDF gốc đầu vào (2 file mẫu: kh-cao-diem-100-ngay-c-s-tp-hn.pdf, CV 6582.pdf)
data/output/      Kết quả xuất ra (CSV/JSON, không commit vào git)
src/pdf_task_extractor/
    locate_tables.py   Bước 1
    extract_tables.py  Bước 2
    normalize.py       Bước 3 (+ export_records dùng chung cho CSV/JSON)
    pipeline.py        Nối Bước 1-2-3, xuất kết quả
scripts/
    run_extract.py     CLI chính thức
tests/                 25 unit test cho 4 module
notebooks/exploration.ipynb
```

## Cài đặt

```bash
pip install -r requirements.txt
```

## Sử dụng

```bash
python scripts/run_extract.py --input "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf" --output "data/output/kh277_normalized.csv"
python scripts/run_extract.py --input "data/raw/CV 6582.pdf" --output "data/output/cv6582_normalized.json"
```

**Định dạng output được chọn tự động theo đuôi file** truyền vào `--output` — không cần thêm flag nào khác:

- Đuôi `.csv` → xuất CSV bằng `pandas`.
- Đuôi `.json` → xuất JSON (dùng `json.dump` chuẩn, không cần cài thêm thư viện).

Nên ưu tiên dùng JSON khi cần xử lý tiếp bằng code (giữ đúng kiểu dữ liệu, `None` hiện thành `null` thay vì `NaN` gây khó đọc khi mở CSV bằng Excel/Jupyter) — dùng CSV khi cần mở trực tiếp bằng Excel để xem/lọc bằng tay.

### Debug từng bước riêng lẻ

Mỗi module đều chạy độc lập được, in kết quả trung gian ra màn hình để kiểm tra:

```bash
python -m src.pdf_task_extractor.locate_tables "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
python -m src.pdf_task_extractor.extract_tables "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
python -m src.pdf_task_extractor.normalize "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf" "data/output/kh277_normalized.csv"
```

Lệnh `normalize` ở trên cũng xuất được file đầy đủ như `run_extract.py` — dùng khi chỉ muốn chạy riêng Bước 3 để debug, nhưng nên dùng `scripts/run_extract.py` cho công việc thực tế.

## Chạy test

```bash
python -m pytest tests/ -v
```

## Schema output

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
- `data/raw/CV 6582.pdf` — Công văn Sở Y tế Hà Nội về di trú Hồ sơ sức khỏe điện tử (bảng "Kế hoạch sơ bộ di trú dữ liệu", 5 cột, header 1 dòng).

## Giới hạn đã biết

- Chỉ nhận diện được bảng có header chứa đủ 2 trường "đơn vị chủ trì" và "đơn vị phối hợp" (hoặc từ đồng nghĩa của chúng). File PDF không có cấu trúc phân công dạng bảng tương tự sẽ không trích xuất được gì.
- Việc gộp dòng bị ngắt trang và nối dòng bị wrap chữ dựa trên các quy tắc suy ra từ 2 file mẫu hiện có; với file PDF có cách trình bày khác biệt lớn, nên kiểm tra lại kết quả trước khi dùng.
