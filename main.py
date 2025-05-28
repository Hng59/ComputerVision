import cv2
import numpy as np
#import snap7

#plc = snap7.client.Client()
#plc.connect('192.168.0.1', 0, 1)

path = r'E:\XLA\T1\35x60.JPG'

image = cv2.imread(path)
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

height, width, _ = image.shape

roi_height = height // 1
roi_width = width // 1
roi_x = (width - roi_width) // 1
roi_y = (height - roi_height) // 1

roi_frame = image[roi_y:roi_y + roi_height, roi_x:roi_x + roi_width]

hsv_frame = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
lower_mask = np.array([10, 100, 10])
upper_mask = np.array([20, 255, 200])
mask = cv2.inRange(hsv_frame, lower_mask, upper_mask)


contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

d = None
l = None

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
    d = round((x_max - x_min) / 4.8333)
    l = round((y_max - y_min) / 4.7666)
    text = f"D:{d} H:{l}"
    cv2.putText(image, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

elif len(contours) == 1:
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        x += roi_x
        y += roi_y
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        area = cv2.contourArea(contour)
        d = round(w/4.8333)
        l = round(h/4.7666)
        text = f"D:{d} H:{l}"
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

if (d == 30) & (l == 50): print(1)
if (d == 30) & (l == 60): print(2)
if (d == 35) & (l == 50): print(3)
if (d == 35) & (l == 60): print(4)
if (d == 40) & (l == 50): print(5)
if (d == 40) & (l == 60): print(6)

cv2.imshow('Phoi', image)
#cv2.imshow('PhoiM', mask)

cv2.waitKey(0)
cv2.destroyWindow()