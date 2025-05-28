import cv2
import numpy as np
import serial
import time
from tkinter import *
from PIL import Image, ImageTk

def round_d(x):
    if x < 35:
        x1 = abs(x - 30)
        x2 = abs(x - 35)
        if x1 < x2:
            return 30
        else:
            return 35
    if x >= 35:
        x1 = abs(x - 35)
        x2 = abs(x - 40)
        if x1 < x2:
            return 35
        else:
            return 40

def round_l(y):
    y1 = abs(y - 50)
    y2 = abs(y - 60)
    if y1 < y2:
        return 50
    else:
        return 60

def send_result_to_arduino(d, l):
    if (d, l) == (30, 50):
        arduino.write(b'1')
    elif (d, l) == (30, 60):
        arduino.write(b'2')
    elif (d, l) == (35, 50):
        arduino.write(b'3')
    elif (d, l) == (35, 60):
        arduino.write(b'4')
    elif (d, l) == (40, 50):
        arduino.write(b'5')
    elif (d, l) == (40, 60):
        arduino.write(b'6')

# Thiết lập Serial giao tiếp với Arduino
arduino = serial.Serial(port='COM11', baudrate=115200, timeout=1)
time.sleep(2)  # Chờ Arduino khởi động

# Mở webcam
cap = cv2.VideoCapture(1)

# Tạo cửa sổ giao diện Tkinter
root = Tk()
root.title("Object Detection Interface")
root.state('zoomed')  # Tự động phóng to cửa sổ

# Định nghĩa kích thước cố định cho khung hiển thị
canvas_width, canvas_height = 640, 480

# Tạo khung hiển thị video
video_canvas = Canvas(root, width=canvas_width, height=canvas_height, bg="black")
video_canvas.grid(row=0, column=0, padx=10, pady=10)

# Tạo khung hiển thị ảnh nhận diện
detection_canvas = Canvas(root, width=int(canvas_width * 1.5), height=int(canvas_height * 1.5), bg="gray")
detection_canvas.grid(row=0, column=1, padx=10, pady=10)

# Hiển thị thông số kích thước
info_label = Label(root, text="d = 0, l = 0", font=("Arial", 14))
info_label.grid(row=1, column=0, sticky="w", padx=10, pady=10)

# Biến kiểm soát trạng thái chụp ảnh
waiting_for_capture = False
capture_start_time = 0

def update_frame():
    global waiting_for_capture, capture_start_time

    # Đọc khung hình từ webcam
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from webcam.")
        root.after(10, update_frame)
        return

    # Hiển thị video trực tiếp
    frame_resized = cv2.resize(frame, (canvas_width, canvas_height))
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    frame_pil = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
    video_canvas.create_image(0, 0, anchor=NW, image=frame_pil)
    video_canvas.image = frame_pil

    # Kiểm tra tín hiệu từ Arduino
    if arduino.in_waiting > 0:
        data = arduino.readline().decode('utf-8').strip()
        if data == '9':  # Khi nhận tín hiệu '9'
            print("Received signal '9' from Arduino. Preparing to capture...")
            waiting_for_capture = True
            capture_start_time = time.time()

    # Delay không chặn khi nhận tín hiệu
    if waiting_for_capture:
        elapsed_time = time.time() - capture_start_time
        if elapsed_time >= 2.3:  # Sau 1 giây chụp ảnh
            waiting_for_capture = False
            print("Capturing image after delay...")

            # Chuyển đổi khung hình sang HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Định nghĩa khoảng màu nâu
            lower_brown = np.array([16, 73, 50])
            upper_brown = np.array([33, 142, 191])

            # Tạo mask và xử lý nhiễu
            mask = cv2.inRange(hsv, lower_brown, upper_brown)
            blurred = cv2.GaussianBlur(mask, (9, 9), 0)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            morph = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

            # Tìm contour
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detected_frame = frame.copy()
            d, l = 0, 0

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 2000:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(detected_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    a, b = 6.15, 6.9
                    d = round_d(w / a)
                    l = round_l(h / b)
                    cv2.putText(detected_frame, f"{d}x{l}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                    send_result_to_arduino(d, l)

            # Resize ảnh nhận diện
            height, width = detected_frame.shape[:2]
            resized_frame = cv2.resize(detected_frame, (int(width * 1.5), int(height * 1.5)))

            # Hiển thị ảnh nhận diện
            detected_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            detected_pil = ImageTk.PhotoImage(image=Image.fromarray(detected_rgb))
            detection_canvas.create_image(0, 0, anchor=NW, image=detected_pil)
            detection_canvas.image = detected_pil

            # Cập nhật thông số d và l
            info_label.config(text=f"d = {d}, l = {l}")

    # Lặp lại hàm cập nhật
    root.after(10, update_frame)

# Bắt đầu cập nhật khung hình
update_frame()

# Chạy giao diện
root.mainloop()

# Giải phóng tài nguyên sau khi thoát
cap.release()
arduino.close()
