import cv2
import numpy as np
import time

# Đường dẫn tới file video
video_path = 'video2.mp4'

# Mở video bằng OpenCV
cap = cv2.VideoCapture(video_path)

# Kiểm tra nếu không mở được video
if not cap.isOpened():
    print("Không thể mở video")
    exit()

# Đọc từng khung hình từ video
while True:
    ret, frame = cap.read()  # ret = True nếu đọc thành công, frame = khung hình

    # Nếu không đọc được khung hình (kết thúc video)
    if not ret:
        print("Đã hết video hoặc không thể đọc khung hình")
        break

    # Lấy kích thước khung hình
    height, width, _ = frame.shape

    # Xác định vùng ROI ở giữa khung hình
    roi_height = height // 2
    roi_width = width // 2
    roi_x = (width - roi_width) // 2
    roi_y = (height - roi_height) // 2

    # Cắt vùng ROI
    roi_frame = frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]

    roi_frame_blurred = cv2.GaussianBlur(roi_frame, (5, 5), 0)

    hsv_frame = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
    lower_mask = np.array([10, 100, 10])
    upper_mask = np.array([20, 255, 200])
    mask = cv2.inRange(hsv_frame, lower_mask, upper_mask)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    d = None
    l = None

    if len(contours) == 1:
        for contour in contours:
            # Tính toán bounding rectangle cho contour
            x, y, w, h = cv2.boundingRect(contour)

            x += roi_x
            y += roi_y

            # Vẽ hình chữ nhật vuông góc
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Vẽ hình chữ nhật màu xanh

            # Ghi chú chiều rộng và chiều cao
            d = round(w / 5.866)
            l = round(h / 5.888)
            text = f"D:{d} H:{l}"
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    elif len(contours) > 1:
        all_x, all_y, all_w, all_h = [], [], [], []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            x += roi_x
            y += roi_y

            all_x.append(x)
            all_y.append(y)
            all_w.append(x + w)
            all_h.append(y + h)

            x_min, y_min = min(all_x), min(all_y)
            x_max, y_max = max(all_w), max(all_h)


            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

            area = (x_max - x_min) * (y_max - y_min)
            d = round((x_max - x_min) / 5.866)
            l = round((y_max - y_min) / 5.888)
            text = f"D:{d} H:{l}"
            cv2.putText(frame, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # Hiển thị khung hình
    cv2.imshow('Video', frame)

    if (d == 30) & (l == 50): print(1)
    if (d == 30) & (l == 60): print(2)
    if (d == 35) & (l == 50): print(3)
    if (d == 35) & (l == 60): print(4)
    if (d == 40) & (l == 50): print(5)
    if (d == 40) & (l == 60): print(6)

    # Nhấn phím 'q' để thoát
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

# Giải phóng tài nguyên sau khi kết thúc
cap.release()
cv2.destroyAllWindows()