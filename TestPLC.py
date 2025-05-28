import snap7

# Kết nối tới PLC mô phỏng qua NetToPLCSim (địa chỉ IP giả lập)
plc = snap7.client.Client()
plc.connect('192.168.0.1', 0, 1)  # Địa chỉ IP của PLC mô phỏng, rack = 0, slot = 1

# Kiểm tra kết nối
if plc.get_connected():
    print("Kết nối thành công với PLC mô phỏng!")
else:
    print("Không thể kết nối tới PLC mô phỏng.")

number_to_send = 6
number_bytes = number_to_send.to_bytes(2, byteorder='big', signed=True)
plc.db_write(1, 0, number_bytes)

# Ngắt kết nối
plc.disconnect()