# Python-Bakhi

Chương trình quản lý kết quả học tập sinh viên cho Bài A1 môn COMP1804. Giao diện Streamlit cho phép nhập hồ sơ, tính điểm, xem kết quả và lưu dữ liệu JSON. FastAPI cung cấp API cho cùng các chức năng lưu trữ.

## Đối chiếu yêu cầu Phần A

| Yêu cầu | Chức năng đã có |
|---|---|
| Mã số và họ tên sinh viên | Nhập hồ sơ, kiểm tra trường bắt buộc và MSSV trùng |
| Danh sách môn và điểm thành phần | Nhập 1–15 môn trên giao diện, điểm từ 0 đến 10 |
| Điểm tổng kết mỗi môn | Điểm thành phần 1 × 0.4 + điểm thành phần 2 × 0.6 |
| GPA | Trung bình cộng điểm tổng kết các môn trên thang 10 |
| Lưu dữ liệu có cấu trúc | Danh sách sinh viên trong tệp JSON UTF-8 |
| Mở lại và xem kết quả | Đọc JSON, xem bảng điểm, tìm kiếm, sắp xếp và thống kê |

Điểm môn làm tròn 1 chữ số thập phân. GPA lấy trung bình các điểm môn đã làm tròn rồi làm tròn 2 chữ số, dùng `round()` của Python. Đề bài được cung cấp chưa quy định cách quy đổi GPA hoặc trọng số tín chỉ, nên đây là quy ước nhóm cần ghi trong báo cáo và xác nhận khi giảng viên yêu cầu.

## Các tệp chính

| Tệp | Nội dung |
|---|---|
| `app.py` | Giao diện nhập, xem trước, xác nhận lưu, xem kết quả |
| `data.py` | Kiểm tra, chuẩn hóa, đọc và ghi JSON |
| `tinh_diem.py` | Tính điểm môn và GPA |
| `analytics.py` | Tìm kiếm, sắp xếp và thống kê |
| `api.py` | API đọc, thêm, xóa sinh viên và thống kê |
| `ketqua.json` | Dữ liệu mặc định |
| `demo/ketqua_demo.json` | 4 hồ sơ mẫu dùng cho buổi trình bày |
| `demo/sinh_vien_moi.json` | Thông tin sinh viên thứ 5 để nhập trực tiếp trên giao diện |
| `tests/test_core.py` | Kiểm thử dữ liệu, công thức, đọc ghi JSON và thống kê |
| `tests/test_app.py` | Kiểm thử tương tác trên giao diện Streamlit bằng AppTest |
| `tests/test_api.py` | Kiểm thử các endpoint FastAPI |

JSON dùng khóa `diem_thanh_phan_1` và `diem_thanh_phan_2` theo code hiện tại. Hai tệp mẫu trong `demo` dùng đúng cấu trúc này. Khi mở tệp, chương trình kiểm tra hồ sơ, chuẩn hóa và tính lại điểm tổng kết/GPA từ điểm thành phần.

## Cài đặt và chạy

Mở PowerShell trong thư mục `Python-Bakhi`, dùng Python 3.10 trở lên.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt httpx
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Giao diện tự mở tại địa chỉ được Streamlit in ra, thường là `http://localhost:8501`. Mặc định dữ liệu được lưu trong `ketqua.json` cạnh `data.py`.

Nếu chạy thêm FastAPI, mở terminal thứ hai tại cùng thư mục.

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Khi API ở cổng 8000 đang hoạt động, giao diện tự chuyển sang dùng API. Có thể xem tài liệu API tại `http://127.0.0.1:8000/docs`.

## Chuẩn bị dữ liệu demo

Các MSSV và điểm dưới đây là dữ liệu giả lập. Tệp mẫu chứa 4 thành viên, mỗi người có 3 môn.

| MSSV | Họ tên | Python | Cơ sở dữ liệu | Xử lý dữ liệu | GPA |
|---|---|---:|---:|---:|---:|
| DEMO001 | Long | 8.2 | 8.6 | 7.0 | 7.93 |
| DEMO002 | Sang | 8.6 | 9.0 | 9.2 | 8.93 |
| DEMO003 | Khoa | 5.6 | 6.6 | 7.6 | 6.60 |
| DEMO004 | Trọng | 6.6 | 8.1 | 8.0 | 7.57 |

GPA trung bình nhóm là **7.76**, cao nhất là Sang **8.93**, thấp nhất là Khoa **6.60**.

Trước buổi demo, tạo một bản dữ liệu để chạy thử, rồi chọn tệp này bằng biến môi trường `BAKHI_DATA_FILE`.

```powershell
Copy-Item -LiteralPath .\demo\ketqua_demo.json -Destination .\demo\ketqua_chay_thu.json
$env:BAKHI_DATA_FILE = (Resolve-Path .\demo\ketqua_chay_thu.json).Path
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Đường dẫn tương đối trong `BAKHI_DATA_FILE` được tính từ thư mục chứa `data.py`. Biến môi trường phải được đặt trước khi khởi động ứng dụng. Nếu dùng cả FastAPI và Streamlit cho demo, đặt **cùng giá trị `BAKHI_DATA_FILE` trong cả hai terminal**, rồi khởi động hai tiến trình. Giao diện gọi API đang hoạt động tại cổng 8000.

### Kịch bản trình bày

1. Mở **Danh sách, Tìm & Sắp xếp**, kiểm tra đủ 4 hồ sơ, tìm `Trọng`, rồi sắp GPA từ cao đến thấp. Thứ tự là Sang, Long, Trọng, Khoa.
2. Mở **Thống kê kết quả nhóm**, đối chiếu GPA trung bình 7.76, cao nhất 8.93 và thấp nhất 6.60.
3. Mở **Nhập sinh viên & Tính điểm**. Nhập MSSV `DEMO005`, họ tên `Sinh viên Demo`, số môn `2` theo `demo/sinh_vien_moi.json`.
4. Môn `Lập trình Python` nhập điểm `7` và `9`. Môn `Cơ sở dữ liệu` nhập `6.5` và `7.3`.
5. Bấm **Kiểm tra & Xem trước kết quả**. Kết quả phải là **8.2**, **7.0** và GPA **7.60**. Kiểm tra xong, bấm **Xác nhận & Lưu hồ sơ**.
6. Mở **Lưu / Tải dữ liệu JSON**, bấm **Đọc lại dữ liệu**, kiểm tra JSON đã có `DEMO005` cùng điểm tổng kết và GPA.
7. Dừng ứng dụng bằng `Ctrl+C`, chạy lại lệnh Streamlit trong cùng terminal, tìm `DEMO005` và mở bảng điểm. Hồ sơ vẫn có GPA **7.60** sau khi mở lại. Nếu dùng API, khởi động lại API với cùng đường dẫn demo để kiểm tra việc nạp lại từ tệp.
8. Nhập lại MSSV `DEMO005`, chương trình phải báo trùng. Thử bỏ trống họ tên hoặc nhập hai môn cùng tên, chương trình phải báo lỗi trước khi lưu. Các ô nhập số giới hạn điểm trong khoảng 0–10.

## Kiểm thử tự động và kết quả kiểm tra

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Các kiểm thử sử dụng JSON trong thư mục tạm, bao gồm nhập, xác nhận lưu trên giao diện và thêm/xóa qua API. Cần có `streamlit`, `fastapi` và `httpx` để chạy đủ các nhóm kiểm thử. Khi thiếu thư viện tương ứng, `unittest` sẽ ghi `skipped` cho nhóm giao diện/API.

Kết quả chạy ngày **25/11/2026** là **41/41 ca đạt**, gồm 22 ca dữ liệu/tính điểm, 7 ca giao diện và 12 ca API. Đã chạy thêm API bằng tiến trình Uvicorn thật, nhập `DEMO005`, kiểm tra JSON, dừng và khởi động lại API, rồi đọc lại đúng điểm **8.2**, **7.0** và GPA **7.60**. Hai tệp demo đã được đối chiếu với các phép tính trong chương trình.

Kiểm thử giao diện dùng AppTest và mô phỏng việc chạy lại fragment khi xác nhận trong hộp thoại Streamlit. Phiên bản Streamlit đã chạy có cảnh báo tham số `use_container_width` sẽ được thay bằng `width`; các ca kiểm thử vẫn hoàn tất.

Trong quá trình kiểm tra, đã sửa các lỗi đọc hồ sơ thiếu điểm tổng kết/GPA, hiển thị điểm tính cũ, tiếp tục nhập sau khi JSON lỗi, trùng MSSV khác hoa/thường và nhận điểm Boolean qua API. Luồng thêm sinh viên đọc lại dữ liệu mới nhất trước khi ghi. API khóa thao tác thêm/xóa trong cùng tiến trình, tệp được thay bằng bản ghi tạm sau khi ghi thành công.

Phần source code đáp ứng các chức năng Phần A được cung cấp. Khi chuẩn bị nộp, nhóm cần hoàn thiện báo cáo ngắn và phần trình bày theo yêu cầu môn học.
