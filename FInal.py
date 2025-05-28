import cv2
import numpy as np
import serial
import time
from tkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog
from tkinter import messagebox

# Biến toàn cục
arduino = None
cap = None
waiting_for_capture = False
capture_start_time = 0
d_values = []
l_values = []
time_stamps = []
object_count = []
phoi = [0, 0, 0, 0, 0, 0]
phoi_array = ['30x50', '30x60', '35x50', '35x60', '40x50', '40x60']
total_phoi = 0
phoi_pie = [0, 0, 0, 0, 0, 0]
info_array = ['', '', '']
graph_canvas = None

# Hàm làm tròn kích thước
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
    command_map = {
        (30, 50): (b'1', 0),
        (30, 60): (b'2', 1),
        (35, 50): (b'3', 2),
        (35, 60): (b'4', 3),
        (40, 50): (b'5', 4),
        (40, 60): (b'6', 5),
    }
    if (d, l) in command_map and arduino:
        byte_value, index = command_map[(d, l)]
        phoi[index] += 1
        arduino.write(byte_value)
        print(phoi)

# Hàm cập nhật video và vẽ biểu đồ
def update_frame(video_canvas, detection_canvas, info_label, graph_canvas):
    global cap, waiting_for_capture, capture_start_time, d_values, l_values, time_stamps, object_count, total_phoi

    # Đọc khung hình từ webcam
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from webcam.")
        root.after(10, update_frame, video_canvas, detection_canvas, info_label, graph_canvas)
        return

    # Hiển thị video trực tiếp
    frame_resized = cv2.resize(frame, (640, 480))
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    frame_pil = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
    video_canvas.create_image(0, 0, anchor=NW, image=frame_pil)
    video_canvas.image = frame_pil

    # Kiểm tra tín hiệu từ Arduino
    if arduino and arduino.in_waiting > 0:
        data = arduino.readline().decode('utf-8').strip()
        if data == '9':  # Khi nhận tín hiệu '9'
            waiting_for_capture = True
            capture_start_time = time.time()

    # Xử lý nhận diện sau khoảng trễ
    if waiting_for_capture:
        elapsed_time = time.time() - capture_start_time
        if elapsed_time >= 2.3:  # Sau 2.3 giây
            waiting_for_capture = False

            # Chuyển đổi sang HSV và nhận diện
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower_brown = np.array([15, 75, 75])
            upper_brown = np.array([35, 120, 160])
            mask = cv2.inRange(hsv, lower_brown, upper_brown)
            blurred = cv2.GaussianBlur(mask, (11, 11), 0)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            morph = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detected_frame = frame.copy()
            d, l = 0, 0
            count = 0

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 10000:
                    count += 1
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(detected_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    a, b = 5.657, 6.55
                    d = round_d(w / a)
                    l = round_l(h / b)
                    cv2.putText(detected_frame, f"{d}x{l}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    send_result_to_arduino(d, l)
                    total_phoi += 1

            # Hiển thị ảnh nhận diện
            detected_rgb = cv2.cvtColor(detected_frame, cv2.COLOR_BGR2RGB)
            detected_resized = cv2.resize(detected_rgb, (640, 480))
            detected_pil = ImageTk.PhotoImage(image=Image.fromarray(detected_resized))
            detection_canvas.create_image(0, 0, anchor=NW, image=detected_pil)
            detection_canvas.image = detected_pil

            # Thêm dữ liệu vào danh sách và vẽ biểu đồ
            current_time = time.time() - capture_start_time
            time_stamps.append(current_time)
            object_count.append(count)

            # Cập nhật các giá trị d và l (vị trí hoặc kích thước)
            d_values.append(d)
            l_values.append(l)

            # Vẽ lại biểu đồ mới
            draw_graph(graph_canvas)

    # Cập nhật thông số trên info_label
    info_text = f"Cổng kết nối : {info_array[0]}\n"
    info_text += f"Kênh Serial:  {info_array[1]}\n"
    info_text += f"Webcam ID : {info_array[2]}"
    info_label.config(text=info_text)


    # Lặp lại
    root.after(10, update_frame, video_canvas, detection_canvas, info_label, graph_canvas)


# Hàm vẽ biểu đồ
def draw_graph(graph_canvas):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # Biểu đồ cột: vẽ số lượng phôi cho từng loại
    ax1.bar(phoi_array, phoi, color=plt.cm.Paired.colors[:len(phoi)])
    ax1.set_xlabel('Loại phôi')
    ax1.set_ylabel('Số lượng phôi')
    ax1.set_title("Số lượng phôi theo loại")

    # Tính phần trăm của mỗi loại phôi
    if total_phoi > 0:
        phoi_percent = [100 * x / total_phoi for x in phoi]
        wedges, _, autotexts = ax2.pie(
            phoi_percent,
            labels=None,  # Không hiển thị nhãn trực tiếp trên biểu đồ
            autopct='%1.1f%%',
            startangle=90,
            colors=plt.cm.Paired.colors[:len(phoi)]
        )

        ax2.set_title("Phần trăm của các loại phôi")

        # Thêm chú giải (legend) cho biểu đồ tròn
        ax2.legend(wedges, phoi_array, title="Loại phôi", loc="upper right", bbox_to_anchor=(1.2, 1))

    # Xóa biểu đồ cũ (nếu có) trước khi vẽ lại
    for widget in graph_canvas.winfo_children():
        widget.destroy()

    # Hiển thị biểu đồ trong Tkinter
    canvas = FigureCanvasTkAgg(fig, master=graph_canvas)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

# Hàm thoát chương trình
def exit_program():
    root.quit()

# Hàm cài lại giá trị phôi và tổng số phôi
def reset_phoi():
    global phoi, total_phoi
    phoi = [0, 0, 0, 0, 0, 0]
    total_phoi = 0

# Hàm lưu giá trị phôi và tổng số phôi vào file
def save_phoi():
    try:
        # Mở cửa sổ chọn đường dẫn và tên tệp để lưu
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not file_path:  # Kiểm tra nếu người dùng không chọn tệp
            return

        # Ghi dữ liệu vào tệp với mã hóa UTF-8
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("Tổng số phôi: {}\n".format(total_phoi))
            for i in range(len(phoi)):
                file.write("{}: {}\n".format(phoi_array[i], phoi[i]))

        # Thông báo khi lưu thành công
        messagebox.showinfo("Thành công", f"Dữ liệu phôi đã được lưu vào {file_path}")
    except Exception as e:
        # Thông báo khi có lỗi
        messagebox.showerror("Lỗi", f"Lỗi khi lưu dữ liệu: {e}")

# Hàm tải giá trị phôi và tổng số phôi từ file
def load_phoi():
    try:
        # Mở cửa sổ chọn tệp để tải
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not file_path:  # Kiểm tra nếu người dùng không chọn tệp
            return

        # Đọc dữ liệu từ tệp
        with open(file_path, "r") as file:
            lines = file.readlines()
            total_phoi = int(lines[0].split(":")[1].strip())
            for i in range(1, len(phoi_array) + 1):
                phoi[i - 1] = int(lines[i].split(":")[1].strip())

        # Thông báo khi tải thành công
        messagebox.showinfo("Thành công", f"Dữ liệu phôi đã được tải từ {file_path}")
    except Exception as e:
        # Thông báo khi có lỗi
        messagebox.showerror("Lỗi", f"Lỗi khi tải dữ liệu: {e}")

# Hàm ngắt kết nối và quay lại cửa sổ kết nối
def disconnect():
    global arduino, cap
    if arduino:
        arduino.close()
    if cap:
        cap.release()
    open_connection_window()

# Giao diện chính
def setup_main_window():
    global cap

    root.state("zoomed")
    video_canvas = Canvas(root, width=640, height=480, bg="black")
    video_canvas.grid(row=0, column=0, padx=60, pady=10)
    detection_canvas = Canvas(root, width=640, height=480, bg="gray")
    detection_canvas.grid(row=1, column=0, padx=60, pady=10)
    info_label = Label(root, text=None, font=("Arial", 14))
    info_label.grid(row=1, column=1, padx=10, pady=10)

    # Thêm khung vẽ biểu đồ
    graph_canvas = Canvas(root, width=960, height=480, bg="gray")
    graph_canvas.grid(row=0, column=1, padx=60, pady=10, columnspan=2, sticky=N+S+E+W)

    # Tạo Frame để chứa các nút
    button_frame = Frame(root)
    button_frame.grid(row=1, column=2, padx=10, pady=10)

    # Thêm các nút vào Frame
    exit_button = Button(button_frame, text="Thoát", command=exit_program)
    exit_button.pack(side=LEFT, padx=5)

    reset_button = Button(button_frame, text="Cài lại", command=reset_phoi)
    reset_button.pack(side=LEFT, padx=5)

    save_button = Button(button_frame, text="Lưu", command=save_phoi)
    save_button.pack(side=LEFT, padx=5)

    load_button = Button(button_frame, text="Tải", command=load_phoi)
    load_button.pack(side=LEFT, padx=5)

    disconnect_button = Button(button_frame, text="Ngắt kết nối", command=disconnect)
    disconnect_button.pack(side=LEFT, padx=5)

    update_frame(video_canvas, detection_canvas, info_label, graph_canvas)

# Cửa sổ kết nối
def open_connection_window():
    connection_window = Toplevel(root)
    connection_window.title("Kết nối thiết bị")

    Label(connection_window, text="Cổng COM:").grid(row=0, column=0, padx=5, pady=5)
    com_entry = Entry(connection_window)
    com_entry.grid(row=0, column=1, padx=5, pady=5)

    Label(connection_window, text="Tốc độ Serial:").grid(row=1, column=0, padx=5, pady=5)
    baud_entry = Entry(connection_window)
    baud_entry.insert(0, "115200")
    baud_entry.grid(row=1, column=1, padx=5, pady=5)

    Label(connection_window, text="Webcam ID:").grid(row=2, column=0, padx=5, pady=5)
    webcam_entry = Entry(connection_window)
    webcam_entry.grid(row=2, column=1, padx=5, pady=5)

    def connect_devices():
        global arduino, cap
        try:
            com_port = f"COM{com_entry.get()}"
            baud_rate = int(baud_entry.get())
            webcam_id = int(webcam_entry.get())

            info_array[0] = com_port
            info_array[1] = str(baud_rate)
            info_array[2] = str(webcam_id)

            arduino = serial.Serial(port=com_port, baudrate=baud_rate, timeout=1)
            time.sleep(2)
            cap = cv2.VideoCapture(webcam_id)
            if not cap.isOpened():
                raise ValueError("Không mở được webcam")
            connection_window.destroy()
            setup_main_window()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Kết nối thất bại: {e}")

    Button(connection_window, text="Kết nối", command=connect_devices).grid(row=3, column=0, columnspan=2, pady=10)

# Chương trình chính
root = Tk()
root.title("Hệ thống nhận diện và phân loại")
open_connection_window()
root.mainloop()
