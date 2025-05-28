import cv2
import numpy as np
import serial
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

def round_d(x):
    if x < 35:
        x1 = abs(x - 30)
        x2 = abs(x - 35)
        if x1 < x2: return(30)
        elif x1 >= x2: return(35)
    if x >= 35:
        x1 = abs(x - 35)
        x2 = abs(x - 40)
        if x1 < x2: return(35)
        elif x1 >= x2: return(40)

def round_l(y):
    y1 = abs(y - 50)
    y2 = abs(y - 60)
    if y1 < y2: return(50)
    elif y1 >= y2: return(60)

ser = serial.Serial('COM11', 115200)

video_path = 'video5.mp4'
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Không thể mở video")
    exit()

image = None
paused = False
detected_image = None
d = None
l = None
case_text = ""

def update_frame():
    global image, paused, detected_image, d, l, case_text
    if not paused:
        ret, frame = cap.read()
        if not ret:
            print("Kết thúc nhận diện")
            return

        height, width, _ = frame.shape
        roi_height = 650
        roi_width = 550
        roi_x = 325
        roi_y = 300

        roi_frame = frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]
        start_point = (roi_x, roi_y)
        end_point = (roi_x + roi_width, roi_y + roi_height)
        sensorX = 400

        cv2.rectangle(frame, start_point, end_point, (0, 0, 255), 2)
        cv2.line(frame, (roi_x + sensorX, roi_y), (roi_x + sensorX, roi_y + roi_height), (255, 0, 255), 2)

        if ser.in_waiting > 0:
            serial_input = ser.readline().decode('utf-8').strip()
            if serial_input == '9':
                image = frame.copy()
                ser.write(b'0')
                hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

                hsv_frame = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
                lower_mask = np.array([10, 100, 10])
                upper_mask = np.array([20, 255, 200])
                mask = cv2.inRange(hsv_frame, lower_mask, upper_mask)
                mask = cv2.GaussianBlur(mask, (9, 9), 0)

                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                d = None
                l = None
                a = 9
                b = 9.6

                if len(contours) > 1:
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

                    cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

                    d = round((x_max - x_min) / a)
                    l = round((y_max - y_min) / b)
                    d = round_d(d)
                    l = round_l(l)

                elif len(contours) == 1:
                    for contour in contours:
                        x, y, w, h = cv2.boundingRect(contour)
                        x += roi_x
                        y += roi_y
                        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        d = round(w / a)
                        l = round(h / b)
                        d = round_d(d)
                        l = round_l(l)

                # Xác định trường hợp phôi
                char_to_send = None
                if (d == 30) & (l == 50):
                    case_text = "Trường hợp phôi: 1"
                    ser.write(b'1')
                elif (d == 30) & (l == 60):
                    case_text = "Trường hợp phôi: 2"
                    ser.write(b'2')
                elif (d == 35) & (l == 50):
                    case_text = "Trường hợp phôi: 3"
                    ser.write(b'3')
                elif (d == 35) & (l == 60):
                    case_text = "Trường hợp phôi: 4"
                    ser.write(b'4')
                elif (d == 40) & (l == 50):
                    case_text = "Trường hợp phôi: 5"
                    ser.write(b'5')
                elif (d == 40) & (l == 60):
                    case_text = "Trường hợp phôi: 6"
                    ser.write(b'6')
                else: case_text = "Phôi lỗi"

                # Cập nhật ảnh nhận diện
                detected_image = image.copy()

        # Cập nhật hình ảnh video lên giao diện
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        lbl_video.imgtk = imgtk
        lbl_video.configure(image=imgtk)

        # Cập nhật ảnh nhận diện lên giao diện
        if detected_image is not None:
            detected_image_rgb = cv2.cvtColor(detected_image, cv2.COLOR_BGR2RGB)
            detected_image_rgb = cv2.resize(detected_image_rgb, (0, 0), fx=0.5, fy=0.5)  # Resize nhỏ còn 50%
            img_detected = Image.fromarray(detected_image_rgb)
            imgtk_detected = ImageTk.PhotoImage(image=img_detected)
            lbl_detected.imgtk = imgtk_detected
            lbl_detected.configure(image=imgtk_detected)

        # Hiển thị bán kính d và chiều cao l
        lbl_dimensions.config(text=f"Bán kính (d): {d}, Chiều cao (l): {l}")
        lbl_case.config(text=case_text)

    root.after(10, update_frame)

def pause_video():
    global paused
    paused = not paused
    btn_pause.config(text="Resume" if paused else "Pause")

def quit_program():
    cap.release()
    root.quit()

# Thiết lập giao diện Tkinter
root = tk.Tk()
root.title("Video Processing with OpenCV")
root.geometry("1200x800")

# Tự động phóng to cửa sổ khi chạy
root.state('zoomed')

# Bố cục lưới cho giao diện
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# Label hiển thị video ở bên phải
lbl_video = tk.Label(root, borderwidth=2, relief="solid")
lbl_video.grid(row=0, column=2, rowspan=3, padx=10, pady=10)


# Label hiển thị hình ảnh nhận diện ở góc trên bên trái
lbl_detected = tk.Label(root, borderwidth=2, relief="solid")
lbl_detected.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

# Label hiển thị thông số d và l với viền
lbl_dimensions = tk.Label(root, text="Bán kính (d): N/A, Chiều cao (l): N/A", font=("Arial", 12), borderwidth=2, relief="solid")
lbl_dimensions.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="nw")

# Label hiển thị trường hợp phôi với viền
lbl_case = tk.Label(root, text="Trường hợp phôi: N/A", font=("Arial", 12), borderwidth=2, relief="solid")
lbl_case.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nw")

# Nút tạm dừng/tiếp tục và thoát chương trình
btn_pause = ttk.Button(root, text="Pause", command=pause_video)
btn_pause.grid(row=3, column=0, padx=10, pady=10, sticky="w")

btn_quit = ttk.Button(root, text="Quit", command=quit_program)
btn_quit.grid(row=3, column=1, padx=10, pady=10, sticky="e")

update_frame()
root.mainloop()
