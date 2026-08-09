"""
Bước 1: Xác định vị trí (số trang) chứa bảng nhiệm vụ trong file PDF.

Ý tưởng: quét từng trang, kết hợp 2 tín hiệu để xác định trang mục tiêu:
- Tín hiệu từ khóa: text trang có chứa các cụm như "Phụ lục", "Đơn vị chủ trì",
  "Đơn vị phối hợp", "Sản phẩm", "Thời hạn".
- Tín hiệu cấu trúc: trang có bảng được pdfplumber.find_tables() nhận diện,
  với số cột >= 4.

Trả về danh sách số trang (0-indexed) được coi là chứa bảng nhiệm vụ, để
extract_tables.py chỉ xử lý đúng các trang này thay vì hard-code số trang.
"""
