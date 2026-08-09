"""
Bước 2: Trích xuất bảng thô (raw rows) từ các trang đã xác định ở locate_tables.py.

Dùng pdfplumber.Page.find_tables() / extract_table() cho từng trang mục tiêu.
Gộp các bảng của nhiều trang liên tiếp thành một danh sách rows duy nhất,
loại bỏ dòng header bị lặp lại ở đầu mỗi trang khi bảng bị ngắt qua trang.

Output của bước này là dữ liệu "thô" (list các dict/row theo đúng cột gốc
trong PDF), chưa xử lý dòng nhóm cha hay merged cell — việc đó thuộc về
normalize.py.
"""
