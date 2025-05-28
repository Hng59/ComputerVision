import cv2
import numpy as np
import serial

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

video_path = 'video3.mp4'
#cap = cv2.VideoCapture(video_path)
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Không thể mở video")
    exit()

image = None

while True:
    ret, frame = cap.read()
    if not ret:
        print("Kết thúc nhận diện")
        break

    height, width, _ = frame.shape

    roi_height = 650
    roi_width = 550
    roi_x = 325
    roi_y = 300

    roi_frame = frame[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]
    start_point = (roi_x, roi_y)
    end_point = (roi_x + roi_width, roi_y + roi_height)
    sensorX = 400

    cv2.rectangle(frame, start_point, end_point, (0,0,255), 2)
    cv2.line(frame, (roi_x + sensorX,roi_y), (roi_x + sensorX,roi_y + roi_height),(255,0,255), 2)

    frame1 = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    cv2.imshow('Video', frame1)

    if ser.in_waiting > 0:
        serial_input = ser.readline().decode('utf-8').strip()
        if serial_input == '1':
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

                area = (x_max - x_min) * (y_max - y_min)
                d = round((x_max - x_min) / a)
                l = round((y_max - y_min) / b)
                d = round_d(d)
                l = round_l(l)
                text = f"D:{d} H:{l}"
                cv2.putText(image, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            elif len(contours) == 1:
                for contour in contours:
                    x, y, w, h = cv2.boundingRect(contour)
                    x += roi_x
                    y += roi_y
                    cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    area = cv2.contourArea(contour)
                    d = round(w / a)
                    l = round(h / b)
                    d = round_d(d)
                    l = round_l(l)
                    text = f"D:{d} H:{l}"
                    cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            print("Phôi vào trường hợp: ")
            if (d == 30) & (l == 50): print(1)
            elif (d == 30) & (l == 60): print(2)
            elif (d == 35) & (l == 50): print(3)
            elif (d == 35) & (l == 60): print(4)
            elif (d == 40) & (l == 50): print(5)
            elif (d == 40) & (l == 60): print(6)
            else: print('Phôi lỗi')


        image1 = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Captured Frame', image1)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Nhấn 'q' để thoát
        break

cap.release()
cv2.destroyAllWindows()
