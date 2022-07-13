import serial
import time
import os
ser = serial.Serial(
port = "/dev/pts/16",
baudrate = 115200,
bytesize = serial.EIGHTBITS, 
parity = serial.PARITY_NONE,
stopbits = serial.STOPBITS_ONE, 
timeout = 2,
xonxoff = False,
rtscts = False,
dsrdtr = False,
writeTimeout = 2
)
kill_minicom_cmd = "pgrep minicom | xargs sshpass -p intel123 sudo kill -9"
kill_cu_cmd = "pgrep cu | xargs sshpass -p intel123 sudo kill -9"
os.system(kill_minicom_cmd)
os.system(kill_cu_cmd)

print(ser.isOpen())
cmd="root\n"
ser.write(cmd.encode())
time.sleep(3)
cmd = "test0000\n"
ser.write(cmd.encode())
time.sleep(2)
cmd = "ip r s\n"
ser.write(cmd.encode())
time.sleep(2)
# msg=ser.read(50000)
# msg = ser.read_until(expected="TX", size=None)
cmd_output_list = []
while True:
    serial_line = ser.readline()
    serial_line_str = serial_line.decode()
    print(serial_line_str)
    cmd_output_list.append(serial_line_str.rstrip())
    if len(serial_line) == 0:
      break

print ("*********************")
print(cmd_output_list)
required_string = ""
for item in cmd_output_list:
    if "eth" in item:
        required_string = item
        break
required_string = required_string.rstrip()
dut_ip = required_string.split(" ")[-1]
print(dut_ip)
ser.close()             # close port