import serial
import time
import os
import subprocess
import re
import sys
import psutil

def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                print ("%s running" %(processName))
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            print ("%s NOT running"% (processName))
            pass
    print ("%s NOT running"% (processName))
    return False;

def isThisProcessRunning(process_name):
    ps = subprocess.Popen("ps -eaf | grep -w " + process_name + " | grep -v grep", shell=True, stdout=subprocess.PIPE)
    output = ps.stdout.read()
    # print (output)
    ps.stdout.close()
    ps.wait()

    if re.search(process_name, str(output)) is None:
        print("%s process not found" %(process_name))
        return False
    else:
        print("%s process found" % (process_name))
        return True

#base method to initialize the pyserial port
def initializePySerial(port = "/dev/pts/16"):
    ser = serial.Serial(
    port = port,
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
    #for debug purpose
    if ser.isOpen():
        return ser
    else:
        return False
    
def getSerialDump(port = "/dev/pts/16"):
    ser = initializePySerial(port = port)
    if ser:
        time.sleep(1)
        ser.write("\r\n".encode())
        time.sleep(2)
        input_data = ser.read(ser.inWaiting())
        
        print (input_data)
        input_string = str(input_data).rstrip()
        # print (input_string)
        ser.close()             # close port
        return input_string
    else:
        print("port is not open")
        ser.close()             # close port
        return False   

def detectLoginPromptAndLogIn(port = "/dev/pts/16", waitForLoginPromptSeconds = 120):
    
    loginPrompt = False
    loggedInPrompt = False
    print ("waiting for 70 seconds and keep checking for login prompt")
    for i in range(waitForLoginPromptSeconds):
        time.sleep(1)
        serialDump = getSerialDump(port = port)
        print("########################")
        print (serialDump)
        print("########################")
        if serialDump:
            #checking for already loggedin prompt
            logedInPattern = "localhost.*~.*#"
            if re.search(logedInPattern, serialDump):
                print("The console has already been logged. Exitin as True ")
                return True
            
            print ("Checking for login prompt*****")
            if 'localhost login:' in serialDump:
                print("localhost login prompt found")
                loginPrompt = True
                break
            else:
                print("localhost login prompt not found")
        else:
            print("port is not open")
            return False
    if loginPrompt:
        ser = initializePySerial(port = port)
        cmd="root\n"
        ser.write(cmd.encode())
        time.sleep(3)
        cmd = "test0000\n"
        ser.write(cmd.encode())
        
    serialDump = getSerialDump(port = port)
    # ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    # serialDump = ansi_escape.sub('', serialDump)
    print("---------------")
    print (serialDump)
    print("---------------")
    logedInPattern = "localhost.*~.*#"
    
    if re.search(logedInPattern, serialDump):
        print("login success")
        ser.close()             # close port
        return True
    else:
        print("Login not successfull")
        ser.close()             # close port
        return False
    
def getCommandOutputOverSerial(ser = initializePySerial(port = "/dev/pts/16"), cmd = "ip r s\n"):
    if detectLoginPromptAndLogIn(port = "/dev/pts/16"):
        ser.write(cmd.encode())
        time.sleep(2)
        cmd_output_list = []
        while True:
            serial_line = ser.readline()
            serial_line_str = serial_line.decode()
            print(serial_line_str)
            cmd_output_list.append(serial_line_str.rstrip())
            if len(serial_line) == 0:
                break
        
        ser.close()             # close port
        return cmd_output_list
    else:
        print ("DUT serial not loggined. DUT serial Login not attempt unsuccessful. Can't run command...")
        return False

def getDutIp():
    ip_cmd_output_list = getCommandOutputOverSerial(ser = initializePySerial(port = "/dev/pts/16"), cmd = "ip r s\n")        
    print ("*********************")
    if ip_cmd_output_list:
        print(ip_cmd_output_list)
        required_string = ""
        for item in ip_cmd_output_list:
            if "eth" in item:
                required_string = item
                break
        required_string = required_string.rstrip()
        dut_ip = required_string.split(" ")[-1]
        print("dut ip is: ", dut_ip)
        return dut_ip
    else:
        print("Unable to find dut ip. DUT IP check command failed.")
        return False

def getOsVersion():
    os_version_cmd_output_list = getCommandOutputOverSerial(ser = initializePySerial(port = "/dev/pts/16"), cmd = "cat /etc/lsb-release\n")
    print(os_version_cmd_output_list)
    if os_version_cmd_output_list:
        os_version_string = ""
        for item in os_version_cmd_output_list:
            if "CHROMEOS_RELEASE_BUILDER_PATH" in item:
                os_version_string = item
                break
        os_version_string = os_version_string.rstrip()
        os_version = os_version_string.split("=")[-1]
        print("os version is: ", os_version)
        return os_version
    else:
        print("Unable to find os version. Os version command failed.")
        return False
    
if __name__ == "__main__":
    #if minicom or cu process are found, kill them so that pyserial can take control
    kill_minicom_cmd = "pgrep minicom | xargs sshpass -p intel123 sudo kill -9"
    kill_cu_cmd = "pgrep cu | xargs sshpass -p intel123 sudo kill -9"
    if isThisProcessRunning("minicom"):
        os.system(kill_minicom_cmd)
    if isThisProcessRunning("cu"):
        os.system(kill_cu_cmd)
    
    getDutIp()
    getOsVersion()


   
