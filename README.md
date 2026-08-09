# Parsing data from PDF

Công cụ trích xuất bảng phân công nhiệm vụ (nhiệm vụ → đơn vị chủ trì/phối hợp) từ file PDF hành chính.

## Mục tiêu

- **Input:** File PDF chứa bảng phân công nhiệm vụ (vd: Phụ lục kế hoạch triển khai chuyển đổi số).
- **Output:** File CSV/JSON có cấu trúc, mỗi dòng là 1 nhiệm vụ với đầy đủ: mã nhiệm vụ, tên nhiệm vụ, đơn vị chủ trì, đơn vị phối hợp, sản phẩm, thời hạn.

## Cấu trúc thư mục

```
data/raw/         PDF gốc đầu vào
data/output/      Kết quả extract (CSV/JSON)
src/pdf_task_extractor/
    locate_tables.py   Xác định trang/vị trí chứa bảng nhiệm vụ trong PDF
    extract_tables.py  Parse bảng thô từng trang
    normalize.py       Xử lý dòng nhóm/merged cell, chuẩn hóa dữ liệu
    validate.py        Đối chiếu số lượng, kiểm tra dữ liệu thiếu
    pipeline.py         Nối các bước, xuất kết quả cuối
scripts/run_extract.py  CLI entrypoint
tests/                   Unit test cho từng module
notebooks/               Khảo sát nhanh cấu trúc PDF trước khi code vào src/
```

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy thử

```bash
python scripts/run_extract.py --input data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf --output data/output/tasks.csv
```

## Dữ liệu mẫu

File phát triển/test: `data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf` — Kế hoạch triển khai đợt cao điểm 100 ngày chuyển đổi số Thành phố Hà Nội (bảng nhiệm vụ nằm ở phần Phụ lục).
