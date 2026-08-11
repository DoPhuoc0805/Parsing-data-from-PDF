# Parsing data from PDF

Công cụ trích xuất bảng phân công nhiệm vụ (nhiệm vụ → đơn vị chủ trì/phối hợp) từ văn bản hành chính, xuất ra CSV/JSON theo 3 tầng dữ liệu.

## Mục tiêu

- **Input:** File chứa bảng phân công nhiệm vụ (vd: Phụ lục kế hoạch triển khai chuyển đổi số). Hỗ trợ **PDF có lớp text** và **Excel** (`.xlsx`, `.xlsm`) — tự nhận dạng theo đuôi file, không cần khai báo gì thêm.
- **Output:** Danh sách nhiệm vụ với mã nhiệm vụ, tên nhiệm vụ, đơn vị chủ trì, đơn vị phối hợp, sản phẩm, thời hạn, nhóm nhiệm vụ.

## Tầng dữ liệu

| Tầng | Nội dung | Định dạng |
|---|---|---|
| `data/raw/` | File gốc | nguyên bản |
| `data/bronze/` | Dòng bảng đọc được, **chưa diễn giải** | JSON |
| `data/silver/` | Bảng phẳng, 1 dòng = 1 nhiệm vụ | CSV + JSON |
| `data/gold/` | Gộp theo nhóm nhiệm vụ | JSON |

Mọi tầng dùng chung tên file gốc, để truy vết 1 văn bản xuyên suốt các tầng chỉ bằng tên.

Tầng bronze tồn tại để **tách bạch lỗi "đọc sai" với lỗi "suy luận sai"** — khi kết quả lệch, mở bronze ra là biết ngay vấn đề nằm ở bước đọc file hay bước xử lý phân cấp. Đồng thời cho phép chạy lại phần xử lý mà không cần đọc lại PDF (xem `--from-bronze`).

## Cách hoạt động

| Module | Vai trò |
|---|---|
| `fields.py` | Ánh xạ tiêu đề cột về trường chuẩn — dùng chung cho mọi nguồn |
| `pdf_tables.py` | Dò bảng nhiệm vụ trong PDF, xử lý bảng ngắt qua nhiều trang |
| `read_pdf.py` | PDF → dòng thô (bronze), gộp dòng bị ngắt trang |
| `read_excel.py` | Excel → dòng thô (bronze), điền ô gộp |
| `hierarchy.py` | Mô hình đường dẫn phân cấp — dùng chung cho mọi loại văn bản |
| `profiles.py` | Cấu hình cách đọc mã phân cấp cho từng kiểu mã hóa |
| `tasks.py` | Dòng thô → nhiệm vụ chuẩn (silver): loại nhãn nhóm, kế thừa cột dùng chung |
| `views.py` | Gộp nhóm (gold) và ghi file |
| `pipeline.py` | Nối các tầng, tự chọn cách đọc và profile |

Việc nhận diện bảng dựa vào header khớp các trường chuẩn (vd "Đơn vị chủ trì"/"Đơn vị thực hiện"/"Chủ trì") — không hard-code theo 1 mẫu cột cố định.

### Cách xác định nhiệm vụ cha/con

Mỗi dòng được quy về một **đường dẫn phân cấp**, rồi mọi kết luận đều suy ra từ đó: mã nhiệm vụ là đường dẫn nối lại, cha là đường dẫn bỏ đoạn cuối, và **"có phải nhóm cha hay không" được suy ra từ chính dữ liệu** — dòng nào có dòng con nằm dưới thì là cha. Không có luật cứng viết riêng cho từng loại văn bản.

Thêm một loại văn bản mới chỉ cần thêm một mục cấu hình trong `profiles.py`:

| Profile | Kiểu mã | Ví dụ |
|---|---|---|
| `number_letter` | Cấp 1 là số, cấp 2 là chữ cái (mã tương đối) | PDF: `12` → `b)` |
| `dotted_code` | Mã có tiền tố, phân cấp bằng dấu chấm | `KH20_TT_N01.1.1` |
| `decimal_index` | Số thập phân, đuôi `.0` là chính nó | `13.0` → `13.5` |

Profile được chọn tự động bằng cách thử đọc: kiểu mã sai gần như không đọc nổi dòng nào.

Đã kiểm chứng trên 4 văn bản có cấu trúc khác nhau hoàn toàn — 2 PDF (7 cột/header 2 dòng và 5 cột/header 1 dòng) và 2 Excel (mã phân cấp có tiền tố, và số thập phân).

## Cài đặt

```bash
pip install -r requirements.txt
```

## Sử dụng

```bash
python scripts/run_extract.py --input "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
python scripts/run_extract.py --input "data/raw/test_2.xlsx"
```

Một lệnh ghi ra cả 3 tầng. Các cờ khác:

| Cờ | Ý nghĩa |
|---|---|
| `--data-dir` | Thư mục gốc chứa các tầng (mặc định `data`) |
| `--from-bronze` | Chạy lại từ bronze đã có, không đọc lại file nguồn — dùng khi debug bước xử lý |

### Debug từng module riêng lẻ

```bash
python -m src.task_extractor.pdf_tables "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
python -m src.task_extractor.read_pdf "data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf"
```

## Chạy test

```bash
python -m pytest tests/ -v
```

## Schema output

### Tầng silver (bảng phẳng)

| Field | Ý nghĩa |
|---|---|
| `ma_nhiem_vu` | Mã nhiệm vụ, vd "1a", "12b" (số nhóm + chữ cái con); nhiệm vụ độc lập thì là số riêng của nó, vd "8" |
| `ten_nhiem_vu` | Tên/nội dung nhiệm vụ |
| `don_vi_chu_tri` | Đơn vị chủ trì |
| `don_vi_phoi_hop` | Đơn vị phối hợp |
| `san_pham` | Sản phẩm đầu ra (nếu file gốc có cột này) |
| `thoi_han` | Thời hạn hoặc số ngày dự kiến |
| `nhom_nhiem_vu` | Tên nhóm nhiệm vụ lớn mà dòng này thuộc về (nhiệm vụ độc lập thì bằng chính `ten_nhiem_vu` của nó) |
| `so_nhom_nhiem_vu` | Số hiệu nhóm dạng số thuần, tiện sort/filter |

Cột `tt`, `chi_tiet` chỉ tồn tại ở tầng bronze, không xuất hiện ở silver/gold.

### Tầng gold (gộp theo nhóm)

Mảng các nhóm, mỗi nhóm gồm tên nhóm, số hiệu nhóm, và mảng `data` chứa các nhiệm vụ con (đã bỏ 2 field `nhom_nhiem_vu`/`so_nhom_nhiem_vu` khỏi từng nhiệm vụ vì đã có ở cấp nhóm). Nhiệm vụ độc lập trở thành 1 nhóm chỉ có 1 phần tử:

```json
[
  {
    "nhom_nhiem_vu": "Làm sạch, di trú, tích hợp, chuẩn hóa nhóm dữ liệu thiết yếu...",
    "so_nhom_nhiem_vu": "1",
    "data": [
      {
        "ma_nhiem_vu": "1a",
        "ten_nhiem_vu": "...",
        "don_vi_chu_tri": "Sở Tài chính",
        "don_vi_phoi_hop": "Sở Khoa học và Công nghệ",
        "san_pham": "...",
        "thoi_han": "30/8/2026"
      }
    ]
  }
]
```

## Dữ liệu mẫu

- `data/raw/kh-cao-diem-100-ngay-c-s-tp-hn.pdf` — Kế hoạch đợt cao điểm 100 ngày chuyển đổi số TP Hà Nội (bảng nhiệm vụ ở Phụ lục, 7 cột, header 2 dòng).
- `data/raw/CV 6582.pdf` — Công văn Sở Y tế Hà Nội về di trú Hồ sơ sức khỏe điện tử (5 cột, header 1 dòng).

## Cảnh báo chất lượng dữ liệu

Khi chạy, công cụ tự kiểm tra tính toàn vẹn của cây nhiệm vụ và in cảnh báo ra màn hình:

- **Mã trùng lặp** — do lỗi đánh số ở văn bản gốc. Được tự thêm hậu tố `a`/`b` để dùng làm khóa chính, không chặn cả tài liệu.
- **Cấp cha bị thiếu** — mã tham chiếu một cấp không có dòng nào trong văn bản (vd có `N05` và `N05.1.1` nhưng thiếu `N05.1`). Con trỏ cha được trỏ lên tổ tiên gần nhất còn tồn tại.

Cả hai đều là lỗi biên tập ở văn bản nguồn, rất khó phát hiện bằng mắt trên file hàng trăm dòng — có thể gửi ngược lại cho người soạn văn bản để sửa.

## Giới hạn đã biết

- Chỉ đọc được **PDF có lớp text**. PDF scan (ảnh) không trích xuất được gì nếu chưa có OCR.
- Chỉ nhận diện được bảng có header chứa đủ 2 trường "đơn vị chủ trì" và "đơn vị phối hợp" (hoặc từ đồng nghĩa).
- Với Excel, chỉ đọc **sheet đầu tiên** của file.
- Việc gộp dòng bị ngắt trang và nối dòng bị wrap chữ dựa trên quy tắc suy ra từ các file mẫu hiện có; với văn bản trình bày khác biệt lớn, nên kiểm tra lại kết quả trước khi dùng.
