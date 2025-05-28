import cv2
import numpy as np
import os


def nothing(x):
    pass


hsv_file = "hsv_values.txt"


def save_hsv_values(lower_bound, upper_bound, filename=hsv_file):
    with open(filename, "w") as file:
        file.write(f"{lower_bound[0]},{lower_bound[1]},{lower_bound[2]}\n")
        file.write(f"{upper_bound[0]},{upper_bound[1]},{upper_bound[2]}\n")
    print(f"HSV values saved to {filename}")


def load_hsv_values(filename=hsv_file):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            lines = file.readlines()
            lower_bound = list(map(int, lines[0].strip().split(',')))
            upper_bound = list(map(int, lines[1].strip().split(',')))
        return lower_bound, upper_bound
    else:
        return [0, 0, 0], [179, 255, 255]


video_path = 'video5.mp4'
cap = cv2.VideoCapture(video_path)
#cap = cv2.VideoCapture(1)

cv2.namedWindow("Trackbars")

lower_hsv, upper_hsv = load_hsv_values()

cv2.createTrackbar("L - H", "Trackbars", lower_hsv[0], 179, nothing)
cv2.createTrackbar("L - S", "Trackbars", lower_hsv[1], 255, nothing)
cv2.createTrackbar("L - V", "Trackbars", lower_hsv[2], 255, nothing)
cv2.createTrackbar("U - H", "Trackbars", upper_hsv[0], 179, nothing)
cv2.createTrackbar("U - S", "Trackbars", upper_hsv[1], 255, nothing)
cv2.createTrackbar("U - V", "Trackbars", upper_hsv[2], 255, nothing)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    l_h = cv2.getTrackbarPos("L - H", "Trackbars")
    l_s = cv2.getTrackbarPos("L - S", "Trackbars")
    l_v = cv2.getTrackbarPos("L - V", "Trackbars")
    u_h = cv2.getTrackbarPos("U - H", "Trackbars")
    u_s = cv2.getTrackbarPos("U - S", "Trackbars")
    u_v = cv2.getTrackbarPos("U - V", "Trackbars")

    lower_bound = np.array([l_h, l_s, l_v])
    upper_bound = np.array([u_h, u_s, u_v])

    mask = cv2.inRange(hsv, lower_bound, upper_bound)

    mask = cv2.GaussianBlur(mask, (11, 11), 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Tìm contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    count = 0
    # Vẽ contours và các hình chữ nhật quanh chúng
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 10000:  # Chỉ xử lý các contours có diện tích lớn hơn 2000
            count += 1
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Vẽ hình chữ nhật màu xanh lên frame

            # Tính toán và hiển thị kích thước nếu cần
            a, b = 5.657, 6.55  # Giả sử kích thước thực tế để tính toán d và l
            d = round(w / a)  # Ví dụ tính toán
            l = round(h / b)  # Ví dụ tính toán
            cv2.putText(frame, f"{d}x{l}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)  # Hiển thị d, l

    result = cv2.bitwise_and(frame, frame, mask=mask)

    frame1 = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    mask1 = cv2.resize(mask, (0, 0), fx=0.5, fy=0.5)
    result1 = cv2.resize(result, (0, 0), fx=0.5, fy=0.5)

    cv2.imshow("Original", frame1)
    cv2.imshow("Mask", mask1)
    cv2.imshow("Result", result1)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        save_hsv_values(lower_bound, upper_bound)
        break

cap.release()
cv2.destroyAllWindows()
