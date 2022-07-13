#!/usr/bin/env python
import pyudev
import os
import sys
import time
import argparse
# import glob
from datetime import datetime
import logging
import logging.handlers
import subprocess
import serial


debug_log_folder = os.getcwd() + "/debug_log"
if not os.path.exists(debug_log_folder):
    os.makedirs(debug_log_folder)

log_file_name = debug_log_folder + "/" + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') +"debug.log"

logging.basicConfig(filename= log_file_name, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("paramiko").setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stdout)
dlogger = logging.getLogger(__name__)
dlogger.addHandler(handler)



def find_cros_sdk_home(name, path):
    path_list = []
    for dirpath, dirname, filename in os.walk(path):
        if name in filename:
            path_list.append(os.path.join(dirpath, name))
    
    cros_sdk_search_path = False
    for path in path_list:
        if "chromite/bin" in path:
            cros_sdk_search_path = path
    
    if cros_sdk_search_path:
        cros_sdk_path = cros_sdk_search_path.split("/chromite")[0]
        return cros_sdk_path
    else:
        return cros_sdk_search_path


def get_removable():
    context = pyudev.Context()
    removable = [device for device in context.list_devices(subsystem='block', DEVTYPE='disk') if device.attributes.asstring('removable') == "1"]
    # print (removable)
    flashing_device = False
    for device in removable:
        # print (device.device_node)
        if device.get('ID_BUS') == "usb":
            flashing_device = device.device_node
            
        # if "usb" in device:
        #     partitions = [device.device_node for device in context.list_devices(subsystem='block', DEVTYPE='partition', parent=device)]
        #     print("All removable partitions: {}".format(", ".join(partitions)))
        #     print("Mounted removable partitions:")
    return flashing_device

#experimental recursion to install and recheck sshpass, but passing password is a must.
def is_sshpass(tries = 1):
    """Check whether `sshpass` is on PATH."""

    from distutils.spawn import find_executable
    print(find_executable("sshpass"))
    if find_executable("sshpass") is None:
        os.system("sudo -k apt-get install sshpass -y")
        tries = tries + 1
        if tries < 2:
            return is_sshpass(tries = 2)
        elif find_executable("sshpass") is not None:
            dlogger.info("sshpass is installed successfully.")
            return True
        else:
            dlogger.info("sshpass couldn't be installed. Exiting. Try installing sshpass manually and then rerun the script")
            return False
    else:
        dlogger.info("sshpass is installed. Returning True")
        return True

def servod_process(cros_sdk_path, password = "intel123"):  
    script_working_directory = os.getcwd()
    # os.system("pgrep servod | xargs sudo kill -9")
    p = subprocess.Popen('pgrep servod', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval = p.wait()
    out, err = p.communicate()

    if out:
        servod_pid = int(out.strip())
        dlogger.info('servod Process found.')
        return True

    dlogger.info('starting a fresh servod...')

    os.chdir(cros_sdk_path)	
    dlogger.info (os.getcwd())
    
    servod_cmd = 'sshpass -p' + " " + password + " cros_sdk" + ' ' + 'sudo ' + 'servod ' + '--board=brya ' + '&'
    os.system(servod_cmd)
    time.sleep(15)
    
    output = subprocess.Popen(['pgrep', 'servod'], stdout=subprocess.PIPE).communicate()[0]
    if output:
        dlogger.info("Servod started successfully")
        return True
    else:
        dlogger.info("Servod couldn't be started successfully. Exiting test.")
        return False
    

def hostSeesUSB(cros_sdk_path, password = "intel123"):  
    if servod_process(cros_sdk_path, password = password):
        os.chdir(cros_sdk_path)	
        dlogger.info (os.getcwd())
        prtctl4_pwren_off_cmd = 'sshpass -p' + " " + password + " cros_sdk" + ' ' + 'dut-control prtctl4_pwren:off'
        dut_control_servo_sees_usb_cmd = 'sshpass -p' + " " + password + " cros_sdk" + ' ' + 'dut-control usb_mux_sel1:servo_sees_usbkey'
        prtctl4_pwren_on_cmd = 'sshpass -p' + " " + password + " cros_sdk" + ' ' + 'dut-control prtctl4_pwren:on'
        
        os.system(prtctl4_pwren_off_cmd)
        os.system(dut_control_servo_sees_usb_cmd)
        time.sleep(2)
        os.system(prtctl4_pwren_on_cmd)
        time.sleep(3)
        if get_removable():
            dlogger.info('removable device found in host. hostSeesUSB successful.')
            return True
        else:
            dlogger.info('removable device not found in host. hostSeesUSB failed.')
            return False    
    else:
        dlogger.info('Unable to start servod. hostSeesUSB failed.')
        return False

def dutSeesUSB(cros_sdk_path, password = "intel123"):  
    if servod_process(cros_sdk_path, password = password):
        os.chdir(cros_sdk_path)	
        dlogger.info (os.getcwd())
        prtctl4_pwren_off_cmd = 'sshpass -p' + " " + password + " cros_sdk" + ' ' + 'dut-control prtctl4_pwren:off'
        dut_control_dut_sees_usb_cmd = 'sshpass -p' + " " + password + " cros_sdk" + ' ' + 'dut-control usb_mux_sel1:dut_sees_usbkey'
        prtctl4_pwren_on_cmd = 'sshpass -p' + " " + password + " cros_sdk" + ' ' + 'dut-control prtctl4_pwren:on'
        
        os.system(prtctl4_pwren_off_cmd)
        os.system(dut_control_dut_sees_usb_cmd)
        time.sleep(2)
        os.system(prtctl4_pwren_on_cmd)
        time.sleep(2)
        if not get_removable():
            dlogger.info('removable device found in dut. dutSeesUSB successful.')
            return True
        else:
            dlogger.info('removable device not found in dut. dutSeesUSB failed.')
            return False    
    else:
        dlogger.info('Unable to start servod. dutSeesUSB failed')
        return False    
    

def get_cpu_uart(cros_sdk_path, password = "intel123"):
    cpu_uart = False
    os.chdir(cros_sdk_path)
    print(os.getcwd())
    cpu_uart_cmd = "sshpass -p" + " " + password  + " " + "cros_sdk dut-control cpu_uart_pty"
    cpu_uart_byte_data = subprocess.check_output(cpu_uart_cmd, shell=True)
    dlogger.info(cpu_uart_byte_data)
    cpu_uart_str_data = cpu_uart_byte_data.decode('utf-8')
    cpu_uart = cpu_uart_str_data.split(":")[1]
    cpu_uart = cpu_uart.rstrip()
    return(cpu_uart)   

def pyserial_function(cpu_uart):
    pass
    
    
    
def is_tool(name):
    """Check whether `name` is on PATH."""
    from distutils.spawn import find_executable
    return find_executable(name) is not None
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', dest='ip_address', help='provide remote system ip')
    parser.add_argument('--password', dest='password', default = "intel123", help='Provide host password if otherthan intel123!')

    args = parser.parse_args()

    #taking care of argparse
    if not args.ip_address:
        ip_address = False
    
    password = args.password
        
    #change directory to cros_sdk directory
    #detect OS file
    #cros flash to the DUT IP if DUT IP is provided in command line argument
    #If failed or DUT IP not provided follow below steps
    #Check removable device detected, cros flash the OS to removable.
    #Boot DUT to recovery using DUT control
    #Switch removable to be seen by DUT
    #using pyserial keep checking for localhost for 180 seconds and localhost is found: login using root and test0000 and chromeos_install -y by detecting block device
    
    if not is_tool("sshpass"):
        dlogger.info ("sshpass is not installed. Please install sshpass with sudo apt-get install sshpass")
        dlogger.info ("Exiting test!")
        sys.exit()
    
    cros_sdk_path = find_cros_sdk_home("cros_sdk", "/")
    if cros_sdk_path:
        if servod_process(cros_sdk_path, password = password):
            removable_device = get_removable()
            cpu_uart = get_cpu_uart(cros_sdk_path, password = password)
             
            print (get_removable())
            print(get_cpu_uart(cros_sdk_path, password = password))
            pyserial_function(cpu_uart)
            hostSeesUSB(cros_sdk_path)
            dutSeesUSB(cros_sdk_path)
        else:
            dlogger.info("servod couldn't start successfully")
    else:
        dlogger.info("cros_sdk path not found in the host machine.")
  
