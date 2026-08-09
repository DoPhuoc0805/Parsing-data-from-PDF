"""
Bước 3-4: Xử lý dòng nhóm cha / merged cell và chuẩn hóa dữ liệu.

- Nhận diện dòng tiêu đề nhóm (cột "Chi tiết" và "Đơn vị chủ trì" trống)
  và forward-fill ngữ cảnh nhóm (tên nhiệm vụ nhóm, đơn vị phối hợp/thời hạn
  chung nếu có) xuống các dòng con (a, b, c...).
- Ghép mã nhiệm vụ đầy đủ từ cột TT + Chi tiết (vd "3" + "b" -> "3.b").
- Tách cột "Đơn vị phối hợp" thành list (split theo dấu ";" hoặc xuống dòng).
- Parse "Thời hạn" thành ngày cụ thể khi có định dạng dd/mm/yyyy, giữ nguyên
  dạng text khi là điều kiện (vd "100 ngày kể từ ngày ban hành Kế hoạch").

Output: danh sách nhiệm vụ đã chuẩn hóa, mỗi phần tử tương ứng 1 dòng trong
kết quả cuối cùng.
"""
