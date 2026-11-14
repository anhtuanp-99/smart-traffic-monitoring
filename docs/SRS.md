# ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)

**Dự án:** Hệ thống giám sát và gợi ý đèn giao thông thông minh (YOLOv8 + ByteTrack)
**Phiên bản:** 1.0  |  **Ngày:** 10/11/2026  |  **Tác giả:** Tuấn

**Quy ước trạng thái:** `Đã làm` = đã có trong code · `Kế hoạch` = chưa làm (giai đoạn sau).
**Quy ước ưu tiên:** Cao = chức năng cốt lõi · Thấp = tiện ích, có thể bỏ mà hệ thống vẫn hoạt động.

---

## 1. Giới thiệu

### 1.1. Mục đích
Tài liệu mô tả yêu cầu của hệ thống giám sát lưu lượng giao thông bằng camera: nhận diện xe, đếm xe theo cung đường, quy đổi sang đơn vị xe máy (PCU) và **gợi ý** điều chỉnh thời gian đèn xanh. Tài liệu dùng làm cơ sở cho thiết kế, lập trình, kiểm thử và viết báo cáo.

### 1.2. Phạm vi
Hệ thống gồm hai phân hệ:

| Phân hệ | Nội dung | Trạng thái |
|---|---|---|
| **A. Giám sát và phân tích (desktop)** | Đọc 2 camera, nhận diện, bám vết, đếm xe, tính PCU, so sánh lưu lượng, gợi ý thời gian xanh, đèn giao thông mô phỏng, xuất báo cáo JSON | Đã làm |
| **B. Tài khoản, thống kê và quản trị (trong ứng dụng desktop)** | Đăng nhập, tạo Admin lần đầu, phân quyền Admin/User, lưu thống kê vào CSDL, thống kê và biểu đồ theo giờ, lịch sử gợi ý, quản lý tài khoản | Đã làm |

**Ngoài phạm vi:** điều khiển đèn tín hiệu thật, nhận diện biển số, xử lý vi phạm giao thông.

### 1.3. Định nghĩa và từ viết tắt

| Thuật ngữ | Ý nghĩa |
|---|---|
| Cung đường | Một hướng tiếp cận ngã tư, mỗi cung đường có một camera (cung đường 1 và 2, vuông góc nhau) |
| Xe đi ra xa | Xe di chuyển ra xa camera (tâm xe dịch lên trên khung hình), tham gia xếp hàng chờ đèn đỏ |
| Xe đi về camera | Xe di chuyển về phía camera, thuộc chiều ngược lại, không tính vào lưu lượng |
| Vạch đếm | Vạch ngang ảo, xe đi ra xa cắt qua vạch thì được đếm |
| PCU | Đơn vị quy đổi xe (1 xe máy = 1 đơn vị) |
| Mốc | Khoảng thời gian chốt số liệu (mặc định 60 giây) |
| Cửa sổ | Số mốc gần nhất dùng để so sánh (mặc định 3 mốc = 3 phút) |
| YOLO / ByteTrack | Mô hình nhận diện đối tượng / thuật toán bám vết đa đối tượng |
| LLM | Mô hình ngôn ngữ lớn, dùng để diễn giải gợi ý (kế hoạch) |

### 1.4. Tài liệu liên quan
`README.md`, `traffic_monitor/config.py` (toàn bộ tham số), bộ sơ đồ UML và sơ đồ high-level trong thư mục `docs/`.

### 1.5. Bố cục tài liệu
Mục 2 mô tả tổng quan, mục 3 là yêu cầu chức năng, mục 4 là giao diện ngoài, mục 5 là yêu cầu phi chức năng, mục 6 là quy tắc nghiệp vụ và công thức, mục 7 là dữ liệu, mục 8 là giả định và hạn chế, mục 9 là vấn đề còn mở.

---

## 2. Mô tả tổng quan

### 2.1. Bối cảnh sản phẩm
Hệ thống mô phỏng một **ngã tư có đèn tín hiệu** bằng **2 camera quay từ phía sau** trên 2 cung đường vuông góc nhau. Camera bao trọn đoạn đường từ chỗ xe ló vào khung hình đến vạch dừng đèn đỏ. Thực tế ngã tư có 4 nhánh, nhưng chỉ có 2 camera nên nhánh đối diện được **giả định có lưu lượng tương đương và cùng pha đèn**.

### 2.2. Chức năng chính
1. Nhận diện và bám vết 4 loại xe: ô tô, xe máy, xe buýt, xe tải.
2. Đếm xe đi ra xa khi cắt vạch, phân biệt hướng đi bằng quỹ đạo màu xanh/đỏ.
3. Quy đổi PCU, gom mốc 60 giây, tính lưu lượng trung bình 3 phút.
4. So sánh lưu lượng 2 cung đường và gợi ý thời gian đèn xanh.
5. Mô phỏng 2 đèn giao thông ngược pha có đếm ngược giây.
6. Xuất báo cáo JSON, lưu thống kê vào CSDL SQLite và hiển thị thống kê, biểu đồ theo giờ trong tab Thống kê.

### 2.3. Đối tượng sử dụng

| Đối tượng | Mô tả | Phân hệ |
|---|---|---|
| Người vận hành | Chạy chương trình, theo dõi video, số liệu và gợi ý (là User hoặc Admin đã đăng nhập) | A |
| User | Đăng nhập để dùng tab Giám sát và Thống kê | B |
| Admin | Có quyền User, tạo tài khoản Admin lần đầu và quản lý User (tab Quản trị) | B |
| Camera / Video | Nguồn hình ảnh: webcam, camera điện thoại (IP), file video | A |
| LLM API | Dịch vụ diễn giải gợi ý bằng ngôn ngữ tự nhiên (kế hoạch) | B |

### 2.4. Môi trường vận hành

| Hạng mục | Yêu cầu |
|---|---|
| Hệ điều hành | Windows 10/11 |
| Phần cứng | Laptop có GPU NVIDIA (đã dùng RTX 3050), hoặc chạy CPU với tốc độ thấp hơn |
| Ngôn ngữ | Python 3.10 trở lên |
| Thư viện phân hệ A | ultralytics, opencv-python, numpy, customtkinter, pillow |
| Thư viện phân hệ B | `sqlite3` và `hashlib` (có sẵn trong Python), matplotlib (biểu đồ) |
| Công cụ theo dõi CSDL | DBeaver (kết nối trực tiếp file SQLite) |
| Mô hình | `weights/best.pt` (YOLOv8n, huấn luyện trên Colab, 4 lớp) |

### 2.5. Ràng buộc
- Tất cả tham số (ngưỡng, hệ số, thời gian đèn...) đặt trong `config.py`, không viết cứng trong code.
- Mỗi camera dùng một instance YOLO riêng vì tracker lưu trạng thái theo instance.
- Gợi ý chỉ mang tính tư vấn, hệ thống không tự thay đổi đèn.

### 2.6. Giả định và phụ thuộc
- Camera đặt cố định, quay từ phía sau theo hướng xe đi tới vạch dừng.
- Điện thoại và laptop cùng mạng Wi-Fi khi dùng camera IP.
- Hệ số PCU và thời gian đèn là giá trị khởi đầu, cần hiệu chỉnh theo thực tế.

---

## 3. Yêu cầu chức năng

### 3.1. Phân hệ A: Giám sát và phân tích (desktop)

**Nguồn video và điều khiển**

| Mã | Yêu cầu | Ưu tiên | Trạng thái |
|---|---|---|---|
| FR-01 | Mỗi cung đường nhận nguồn video là webcam (số thứ tự), URL luồng (http/rtsp) hoặc file video. | Thấp | Đã làm |
| FR-02 | Bật/tắt giám sát độc lập cho từng camera. | Cao | Đã làm |
| FR-03 | Video file phát đúng tốc độ gốc; khi xử lý không kịp thì bỏ bớt khung hình; tự phát lại khi hết video (có thể tắt trong cấu hình). | Cao | Đã làm |
| FR-04 | Hiển thị lỗi trên giao diện khi không mở được nguồn video hoặc thiếu file `best.pt`; lỗi của một camera không làm dừng camera còn lại. | Cao | Đã làm |

**Nhận diện, bám vết và đếm**

| Mã | Yêu cầu | Ưu tiên | Trạng thái |
|---|---|---|---|
| FR-05 | Nhận diện 4 loại xe (car, motorbike, bus, truck) với ngưỡng tự tin tối thiểu 0.35. | Cao | Đã làm |
| FR-06 | Gán ID cho từng xe bằng ByteTrack và lưu quỹ đạo tâm xe (tối đa 30 điểm gần nhất). | Cao | Đã làm |
| FR-07 | Xác định hướng đi theo độ dời tổng của tâm xe trong 15 điểm gần nhất: **ra xa**, **về camera** hoặc **chưa xác định**. Độ dời nhỏ hơn 1.5% chiều cao khung hình thì giữ hướng cũ (xe dừng chờ đèn đỏ). | Cao | Đã làm |
| FR-08 | Vẽ quỹ đạo tâm xe: xanh = đi ra xa, đỏ = đi về camera, xám = chưa xác định. | Cao | Đã làm |
| FR-09 | Chỉ đếm xe đi ra xa khi tâm xe cắt vạch; mỗi ID đếm đúng một lần; xe đi về camera không được đếm. | Cao | Đã làm |
| FR-10 | Vị trí vạch đếm theo thang 0–100 (0 = mép dưới khung hình, nơi xe ló vào; 100 = mép trên), mặc định 40; có thể chỉnh bằng thanh trượt khi đang chạy. | Thấp | Đã làm |

**Thống kê và gợi ý**

| Mã | Yêu cầu | Ưu tiên | Trạng thái |
|---|---|---|---|
| FR-11 | Thống kê tích lũy theo từng loại xe và tổng PCU của mỗi cung đường. | Cao | Đã làm |
| FR-12 | Quy đổi từng xe sang PCU theo hệ số cấu hình (mục 6.1). | Cao | Đã làm |
| FR-13 | Gom số liệu theo mốc 60 giây; lưu lượng so sánh là PCU/phút trung bình của 3 mốc gần nhất. Chưa đủ 3 mốc thì chưa gợi ý. | Cao | Đã làm |
| FR-14 | So sánh lưu lượng 2 cung đường; chỉ gợi ý khi **chênh lệch ≥ 30%** và **tổng ≥ 10 PCU/phút** (mục 6.2). | Cao | Đã làm |
| FR-15 | Khi kích hoạt, đề xuất chia lại thời gian xanh giữa 2 cung đường, giữ nguyên tổng và chu kỳ, giới hạn 20–45 giây (mục 6.3). Kết quả chỉ hiển thị, không tự áp dụng. | Cao | Đã làm |
| FR-16 | Hiển thị trạng thái chờ khi chưa đủ điều kiện: "cần chạy cả 2 camera" hoặc "đang thu thập dữ liệu k/3 mốc". | Cao | Đã làm |

**Đèn giao thông mô phỏng**

| Mã | Yêu cầu | Ưu tiên | Trạng thái |
|---|---|---|---|
| FR-17 | Mô phỏng 2 đèn ngược pha theo chu kỳ mặc định 100 giây (mục 6.4); không bao giờ cả hai cung cùng xanh. | Cao | Đã làm |
| FR-18 | Hiển thị màu hiện tại và số giây còn lại cho từng cung; với đèn đỏ là thời gian còn lại đến khi chuyển xanh. | Cao | Đã làm |

**Giao diện và báo cáo**

| Mã | Yêu cầu | Ưu tiên | Trạng thái |
|---|---|---|---|
| FR-19 | Giao diện chia 2 cột (mỗi cung đường): ô địa chỉ camera, menu chọn video mẫu, nút Start/Stop, khung video, thanh trượt vạch đếm, đèn mô phỏng, số xe theo loại, PCU/phút; khung video tự giãn theo kích thước cửa sổ. | Cao | Đã làm |
| FR-20 | Thanh phía dưới hiển thị lưu lượng 2 cung, chênh lệch, gợi ý và so sánh thời gian xanh mặc định với đề xuất. | Cao | Đã làm |
| FR-21 | Xuất báo cáo JSON vào `logs/<ngày>/` mỗi 60 giây khi có camera đang chạy và khi đóng chương trình. | Cao | Đã làm |
| FR-22 | Lưu log theo thư mục từng ngày, mỗi lần xuất một file (ví dụ `logs/2026-11-10/traffic_log_14-32-05.json`). | Thấp | Đã làm |

### 3.2. Phân hệ B: Tài khoản, thống kê và quản trị (trong ứng dụng desktop)

Phân hệ B nằm chung trong ứng dụng desktop: chạy `main.py` → đăng nhập → cửa sổ chính có các tab **Giám sát**, **Thống kê** và (chỉ Admin) **Quản trị**.

| Mã | Yêu cầu | Ưu tiên | Trạng thái |
|---|---|---|---|
| FR-23 | Lần chạy đầu (CSDL chưa có tài khoản nào) hiển thị màn hình tạo tài khoản Admin; sau đó User không tự đăng ký, do Admin tạo. | Cao | Đã làm |
| FR-24 | Đăng nhập bằng tên đăng nhập và mật khẩu; mật khẩu băm PBKDF2-HMAC-SHA256 có salt; tài khoản bị khóa không đăng nhập được; có đăng xuất (dừng camera và lưu báo cáo trước khi thoát). | Cao | Đã làm |
| FR-25 | Phân quyền: Admin và User dùng tab Giám sát và Thống kê; chỉ Admin có tab Quản trị. | Cao | Đã làm |
| FR-26 | Mỗi mốc 60 giây, ghi vào `traffic_stats` số xe **tăng thêm** của từng cung đường và từng loại xe (mỗi mốc 8 dòng); PCU tính khi truy vấn từ `vehicle_types.pcu_weight` (mục 7.2). | Cao | Đã làm |
| FR-27 | Tab Thống kê hiển thị số xe theo loại, theo cung đường và tổng PCU, có lọc theo ngày. | Cao | Đã làm |
| FR-28 | Biểu đồ PCU theo giờ của 2 cung đường. | Cao | Đã làm |
| FR-29 | Lưu lịch sử gợi ý đèn (khi gợi ý được kích hoạt) vào `signal_suggestions` và hiển thị trong tab Thống kê. | Trung bình | Đã làm |
| FR-30 | Admin thêm, khóa/mở khóa, xóa tài khoản User; không được khóa hoặc xóa chính mình. | Thấp | Đã làm |
| FR-31 | Ghi báo cáo JSON (FR-21) và CSDL (FR-26) theo cùng chu kỳ 60 giây; lỗi ghi CSDL không làm dừng giám sát, JSON vẫn được lưu; ghi CSDL bật/tắt bằng cấu hình `DB_WRITE_STATS`. | Trung bình | Đã làm |
| FR-32 | Diễn giải gợi ý bằng LLM; khi LLM lỗi dùng câu mẫu. Số giây vẫn do công thức (FR-15) tính. | Thấp | Kế hoạch |

---

## 4. Yêu cầu giao diện ngoài

### 4.1. Giao diện người dùng
- **Desktop (customtkinter):** màn hình đăng nhập (hoặc tạo Admin lần đầu); cửa sổ chính có 3 tab: **Giám sát** (hai cột cung đường), **Thống kê** (thẻ số liệu, biểu đồ matplotlib, lịch sử gợi ý), **Quản trị** (chỉ Admin).
- Chữ tiếng Việt, giao diện sáng (đổi sang tối bằng `APPEARANCE_MODE`), mở toàn màn hình; khung video tự giãn theo kích thước cửa sổ. Chữ trên khung video (OpenCV) dùng tiếng Việt không dấu.

### 4.2. Giao diện phần cứng
Webcam, camera điện thoại (ứng dụng IP Webcam/DroidCam), GPU NVIDIA hỗ trợ CUDA (khuyến nghị).

### 4.3. Giao diện phần mềm

| Thành phần | Mô tả |
|---|---|
| `weights/best.pt` | Trọng số YOLOv8 với 4 lớp: car, motorbike, bus, truck |
| OpenCV VideoCapture | Đọc webcam, luồng http/rtsp và file video |
| LLM API (kế hoạch) | Nhận số liệu và kết quả đề xuất, trả lời diễn giải; khóa API lưu trong `.env` |

### 4.4. Giao diện dữ liệu
Báo cáo JSON (mục 7.1) lưu trong `logs/<yyyy-mm-dd>/`, mã hóa UTF-8.

---

## 5. Yêu cầu phi chức năng

| Mã | Nhóm | Yêu cầu |
|---|---|---|
| NFR-01 | Hiệu năng | Xử lý đồng thời 2 camera trên GPU RTX 3050; giao diện cập nhật khoảng 30 ms/lần; mục tiêu mỗi camera đạt khoảng 15 FPS trở lên *(chưa đo, cần kiểm chứng)*. |
| NFR-02 | Độ chính xác | Số xe đếm sai lệch không quá 10% so với đếm tay trên 3 video mẫu *(mục tiêu, cần kiểm chứng)*. |
| NFR-03 | Độ tin cậy | Lỗi một camera không làm dừng camera kia; đóng chương trình luôn lưu báo cáo cuối; không đếm trùng một xe. |
| NFR-04 | Khả năng cấu hình | Mọi tham số nằm trong `config.py`; vị trí vạch đếm chỉnh được lúc chạy. |
| NFR-05 | Khả năng bảo trì | Mã tách module (nhận diện, gom số liệu, gợi ý, đèn mô phỏng, CSDL, tài khoản, giao diện); logic gợi ý, gom mốc, đèn, CSDL và đăng nhập có kiểm thử đơn vị (22 test). |
| NFR-06 | Bảo mật | Mật khẩu băm PBKDF2-HMAC-SHA256 có salt, không lưu dạng gốc; chỉ Admin được thêm/khóa/xóa tài khoản; khóa API của LLM (nếu dùng) chỉ đặt trong `.env`, không đưa lên Git. |
| NFR-07 | Tương thích | Windows 10/11, Python 3.10 trở lên; chạy được trên CPU (chậm hơn). |
| NFR-08 | Khả năng sử dụng | Giao diện tiếng Việt; trạng thái, lỗi và lý do chưa gợi ý hiển thị rõ ràng. |
| NFR-09 | Toàn vẹn dữ liệu | CSDL có khóa chính, khóa ngoại (bật `PRAGMA foreign_keys`), ràng buộc duy nhất và `CHECK` (mục 7.2); không ghi trùng một mốc thống kê. |

---

## 6. Quy tắc nghiệp vụ và công thức

### 6.1. Quy đổi PCU (giá trị khởi đầu, cần đối chiếu tài liệu giao thông và dẫn nguồn trong báo cáo)

| Loại xe | Hệ số PCU |
|---|---|
| Xe máy (motorbike) | 1.0 |
| Ô tô (car) | 3.0 |
| Xe tải (truck) | 5.0 |
| Xe buýt (bus) | 6.0 |

### 6.2. Điều kiện kích hoạt gợi ý
Gọi `P1`, `P2` là lưu lượng trung bình (PCU/phút) của 3 mốc gần nhất của cung 1 và cung 2.

- Chênh lệch = `P_nhiều / P_ít − 1`.
- Gợi ý khi **chênh lệch ≥ 30%** (`IMBALANCE_TRIGGER_PCT`) **và** `P1 + P2 ≥ 10` (`MIN_TOTAL_PCU_PER_MIN`).
- Ngược lại giữ bộ đèn mặc định.

### 6.3. Chia thời gian đèn xanh
- `G_total = GREEN_DEFAULT_1 + GREEN_DEFAULT_2` (mặc định 70 giây).
- `xanh_nhiều = clamp(G_total × P_nhiều / (P1 + P2), MIN_GREEN, MAX_GREEN)` với `MIN_GREEN = 20`, `MAX_GREEN = 45`.
- `xanh_ít = G_total − xanh_nhiều`. Chu kỳ giữ nguyên.
- Ví dụ: `P1 = 60`, `P2 = 30` → công thức ra 46.7 giây, bị chặn ở 45 → cung 1 xanh 45 giây, cung 2 xanh 25 giây.

### 6.4. Chu kỳ đèn mô phỏng mặc định (100 giây)

| Giai đoạn | Cung 1 | Cung 2 | Thời gian |
|---|---|---|---|
| 1 | Xanh | Đỏ | 35 giây |
| 2 | Vàng | Đỏ | 3 giây |
| 3 | Đỏ | Đỏ (đỏ chung) | 2 giây |
| 4 | Đỏ | Xanh | 35 giây |
| 5 | Đỏ | Vàng | 3 giây |
| 6 | Đỏ | Đỏ (đỏ chung) | 2 giây |
| 7 | Đỏ | Đỏ (pha phụ: rẽ, người đi bộ, nhánh khác) | 20 giây |

Mỗi cung: xanh 35 giây, vàng 3 giây, đỏ 62 giây. Giá trị nên được thay bằng số bấm giờ tại một nút giao thật.

### 6.5. Quy tắc đếm
- Chỉ xe có hướng **đi ra xa** mới được đếm.
- Vạch đếm đo lưu lượng đi qua vạch, không đo hàng đợi. Nên đặt vạch xa đuôi hàng xe chờ đèn đỏ để tránh đếm thiếu.

---

## 7. Dữ liệu

### 7.1. Báo cáo JSON (đã làm)

```json
{
  "timestamp": "2026-11-10T14:32:05",
  "location": "Nut giao thong Da Nang - Mo phong 2 camera",
  "interval_seconds": 60,
  "window": { "bucket_seconds": 60, "buckets": 3 },
  "routes": {
    "route_1": {
      "state": "running",
      "total_vehicles": 42,
      "breakdown": { "car": 8, "motorbike": 30, "bus": 1, "truck": 3 },
      "pcu_total": 77.0,
      "window_pcu_per_min": 60.0,
      "window_buckets_ready": 3,
      "active_vehicles_moving_away": 9
    },
    "route_2": { "...": "cấu trúc tương tự route_1" }
  },
  "signal_default": {
    "green_seconds": { "route_1": 35, "route_2": 35 },
    "yellow_seconds": 3,
    "all_red_seconds": 2,
    "extra_red_seconds": 20,
    "cycle_seconds": 100
  },
  "advice": {
    "ready": true,
    "triggered": true,
    "heavier_route": 1,
    "imbalance_pct": 100.0,
    "pcu_route_1": 60.0,
    "pcu_route_2": 30.0,
    "green_1": 45,
    "green_2": 25,
    "message": "Cung 1 đông hơn 100% → đề xuất tăng đèn xanh Cung 1 lên 45s, Cung 2 còn 25s."
  }
}
```

### 7.2. Cơ sở dữ liệu (SQLite)

Cơ sở dữ liệu gồm 5 bảng, có khóa chính (PK), khóa ngoại (FK) và ràng buộc toàn vẹn. Sơ đồ ERD: `07_erd`.

| Bảng | Khóa chính | Khóa ngoại | Các cột còn lại |
|---|---|---|---|
| `users` | `user_id` | không | `username` (duy nhất), `password_hash`, `role` (chỉ nhận `admin` hoặc `user`), `is_active`, `created_at` |
| `routes` | `route_id` | không | `name` (duy nhất); có 2 dòng: Cung đường 1 và Cung đường 2 |
| `vehicle_types` | `type_id` | không | `name` (duy nhất: car, motorbike, bus, truck), `pcu_weight` |
| `traffic_stats` | `stat_id` | `route_id` → `routes`, `type_id` → `vehicle_types` | `recorded_at`, `quantity` (số xe **tăng thêm** trong mỗi mốc 60 giây, không phải số tích lũy) |
| `signal_suggestions` | `suggestion_id` | `heavier_route_id` → `routes` (có thể rỗng khi không có gợi ý) | `recorded_at`, `imbalance_pct`, `green_1`, `green_2`, `content`, `source` (llm/rule) |

**Quan hệ**
- `routes` 1–N `traffic_stats`: một cung đường có nhiều bản ghi thống kê.
- `vehicle_types` 1–N `traffic_stats`: một loại xe xuất hiện trong nhiều bản ghi thống kê.
- `routes` 1–N `signal_suggestions`: một cung đường có thể là cung đông hơn trong nhiều gợi ý.
- `users` đứng riêng, chỉ phục vụ đăng nhập và phân quyền.

**Ràng buộc**
- `traffic_stats` có khóa duy nhất `(route_id, type_id, recorded_at)` để không ghi trùng một mốc; `quantity ≥ 0`.
- Hệ số `pcu_weight` được khởi tạo từ `config.py` khi tạo CSDL. PCU không lưu sẵn mà tính khi truy vấn: tổng của `quantity × pcu_weight`.
- Mỗi mốc ghi 8 dòng vào `traffic_stats` (2 cung đường × 4 loại xe).

**Công nghệ và lưu ý (SQLite)**
- CSDL quan hệ lưu trong một file `data/traffic.db` (không đưa lên Git), tự tạo khi chạy `main.py`.
- Bật `PRAGMA foreign_keys = ON` ở mỗi kết nối vì SQLite mặc định không kiểm tra khóa ngoại; bật chế độ WAL để DBeaver đọc trong khi ứng dụng ghi.
- Các luồng camera không ghi trực tiếp mà đưa dữ liệu vào hàng đợi, một luồng ghi riêng ghi vào SQLite.
- Có thể kết nối DBeaver vào file này để xem bảng, dữ liệu và sơ đồ ER.

---

## 8. Giả định và hạn chế

1. Nhánh đối diện được giả định có lưu lượng tương đương và cùng pha đèn vì chỉ có 2 camera.
2. Vạch đếm đo lưu lượng qua vạch, có thể thấp hơn nhu cầu thật khi hàng xe chờ kéo dài tới sát vạch.
3. Hệ số PCU và thời gian đèn là giá trị khởi đầu, chưa hiệu chỉnh bằng số liệu thực tế.
4. Độ chính xác nhận diện phụ thuộc chất lượng mô hình `best.pt`, góc quay và ánh sáng.
5. Video mô phỏng được phát lặp nên số liệu tích lũy không phản ánh lưu lượng thật theo thời gian.
6. Gợi ý không tự điều khiển đèn; đèn mô phỏng chạy theo bộ giây mặc định.
7. Đăng nhập chỉ bảo vệ ở mức ứng dụng; file CSDL nằm trên máy nên ai có file vẫn mở được bằng công cụ khác (ví dụ DBeaver).
8. CSDL chỉ ghi khi hết trọn một mốc 60 giây; phiên giám sát ngắn hơn một mốc không để lại dữ liệu trong CSDL.

---

## 9. Vấn đề còn mở

| STT | Vấn đề | Ghi chú |
|---|---|---|
| 1 | Hiệu chỉnh hệ số PCU và ngưỡng 30% / 10 PCU/phút | Cần chạy thử trên 3 video và đối chiếu tài liệu |
| 2 | Chọn dịch vụ LLM cho phân hệ B | Chưa chọn |
| 3 | Kiểm chứng NFR-01 và NFR-02 | Cần đo FPS và so sánh với đếm tay |
| 4 | Chạy thử giao diện đăng nhập, Thống kê, Quản trị trên máy thật | Logic CSDL và đăng nhập đã có kiểm thử; giao diện mới được chạy thử bằng bản giả, chưa chạy với customtkinter thật |

---

## Phụ lục A. Truy vết yêu cầu và sơ đồ

| Nhóm yêu cầu | Sơ đồ liên quan |
|---|---|
| FR-01 đến FR-22 (phân hệ A) | Use case 1, Activity 1 và 2, Sequence 1, Class 1, State 1 và 2, High-level |
| FR-23 đến FR-32 (phân hệ B) | Use case 2, Sequence 2, Class 2, ERD (`07_erd`), High-level |

## Phụ lục B. Tham số cấu hình chính (`config.py`)

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `CONFIDENCE_THRESHOLD` | 0.35 | Ngưỡng tự tin nhận diện |
| `DEFAULT_COUNT_LINE_PCT` | 40 | Vị trí vạch đếm (0–100, 0 = mép dưới) |
| `DIRECTION_WINDOW` | 15 | Số điểm quỹ đạo dùng để xác định hướng |
| `DIRECTION_MIN_MOVE_RATIO` | 0.015 | Độ dời tối thiểu (tỉ lệ chiều cao khung) |
| `PCU_WEIGHTS` | 1 / 3 / 5 / 6 | Hệ số xe máy / ô tô / xe tải / xe buýt |
| `BUCKET_SECONDS` | 60 | Độ dài một mốc |
| `WINDOW_BUCKETS` | 3 | Số mốc trong cửa sổ so sánh |
| `IMBALANCE_TRIGGER_PCT` | 30 | Ngưỡng chênh lệch kích hoạt gợi ý |
| `MIN_TOTAL_PCU_PER_MIN` | 10 | Tổng lưu lượng tối thiểu để gợi ý |
| `GREEN_DEFAULT_1/2` | 35 / 35 | Thời gian xanh mặc định |
| `YELLOW`, `ALL_RED`, `EXTRA_RED` | 3, 2, 20 | Vàng, đỏ chung, pha phụ |
| `MIN_GREEN`, `MAX_GREEN` | 20, 45 | Giới hạn xanh khi gợi ý |
| `LOOP_VIDEO_FILES` | True | Tự phát lại video file |
| `DB_WRITE_STATS` | True | Ghi thống kê mỗi mốc vào CSDL |
| `APPEARANCE_MODE` | light | Giao diện sáng / tối / theo hệ thống |
| `START_MAXIMIZED` | True | Mở cửa sổ chính toàn màn hình |
| `DB_PATH` | `data/traffic.db` | Đường dẫn file SQLite |
| `MIN_PASSWORD_LENGTH` | 6 | Độ dài mật khẩu tối thiểu |
| `PBKDF2_ITERATIONS` | 200000 | Số vòng băm mật khẩu |