'''
Copyright 2024-2025 Accolade Electronics Pvt. Ltd

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
version 2 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

file        app_logic.py
brief       This is the script for handling application logic and background communication

date        22 March 2024
author      Accolade Electronics <www.accoladeelectronics.com>
'''

import app_ui                       # for handling GUI
import app_comm                     # for handling UDS communication and stack
from app_ui import MyApp
import tkinter as tk
from tkinter import filedialog, messagebox


#g_ui_main_window = app_ui.create_gui()

############################################## (APP START) ########################################################

def create_gui():
    # Create the main tkinter window
    root = tk.Tk()
    
    # Initialize the MyApp class with the root window
    app = MyApp(root)
    
    # Start the tkinter event loop
    root.mainloop()
# Run the app
 
def connect_to_can_bus():
    # Parameters to initialize CAN connection
    bit_rate = '250Kbps'
    tester_id = '0CDA33F1'   # Utility tester ID
    ecu_id = '0CDAF133'      # SAMPARK ECU ID
    iso_tp_addressing_mode = '29B_FIXED_NORMAL'

    # Convert tester and ECU IDs from hex string to integer
    int_tester_id = int(tester_id, 16)
    int_ecu_id = int(ecu_id, 16)

    # Call can_init() from app_comm module to initialize CAN
    if app_comm.can_init(bit_rate, int_tester_id, int_ecu_id, iso_tp_addressing_mode):
        # If CAN initialization is successful
        messagebox.showinfo("Success", "Connected to CAN Bus successfully.")
    else:
        # If CAN initialization fails
        messagebox.showerror("Error", "Failed to connect to CAN Bus. Please check the hardware or settings.")

########################################## (GUI EVENT HANDLING) #####################################################

import os
import threading

def browse_file():
    app_ui.append_log(f'attempting to write VIN')
    app_comm.perform_service_tests
    

    file_path = ''
    file_path = app_ui.browse_file_from_disk()
    if file_path:
        app_ui.append_log(f'selected file {file_path}')
        try:
            app_comm.g_file_path = file_path
            app_comm.g_file_size = os.path.getsize(file_path)
            app_ui.set_btn_enabled('UPLOAD_BTN', True)

        except Exception as e:
            print(f'app_logic : {e}')
            return False

def connect_can():
    # Dev Note: Kilobits per second is abbreviated to "Kbps" throughout this project
    # Kilobits per second is shortened to kb/s, Kbps or kbps 
    # (as opposed to KBps, which is Kilobytes per second. Note the capitalization). 
    # The lowercase b is commonly used to denote bits, while the uppercase B is used for bytes.
    bit_rate = app_ui.g_project.get("bit_rate", "500Kbps")
    tester_id = app_ui.g_text_input_tester_id.get()
    ecu_id = app_ui.g_text_input_ecu_id.get()

    if (tester_id == ecu_id) and (tester_id !='' or ecu_id !=''):
        app_ui.show_dialog('Error', 'Tester id cannot not be equal to ECU id')
        return
    if validate_hex_input(tester_id) == False:
        app_ui.show_dialog('Error', 'Tester id is not valid (hex)')
        return
    if validate_hex_input(ecu_id) == False:
        app_ui.show_dialog('Error', 'ECU id is not valid (hex)')
        return

    int_tester_id = int(tester_id, 16)
    int_ecu_id = int(ecu_id, 16)

    if app_comm.can_init(bit_rate, int_tester_id, int_ecu_id) == True:
        app_ui.set_btn_enabled('CONNECT_BTN', False)
        # tmp code: code kept until boot lock button dependency is present 
        app_ui.set_btn_enabled('BOOT_LOCK_BTN', True)
        app_ui.set_btn_enabled('BROWSE_BTN', True)
        # end tmp code
        app_ui.g_text_input_tester_id.config(state='disabled')
        app_ui.g_text_input_ecu_id.config(state='disabled')
    else:
        app_ui.show_dialog("Error", "Access denied or hardware not connected")

def validate_hex_input(value):
    try:
        int(value, 16)  # Try converting input to hexadecimal
        return True     # Input is valid hexadecimal
    except ValueError:
        return False    # Input is not valid hexadecimal

def boot_lock():
    print('app_logic : trying to lock into bootloader...')
    app_ui.append_log('trying to lock into bootloader...')

    handle = app_comm.g_pcan_handle
    config = app_comm.g_pcan_config
    if app_comm.testTesterPresent(handle, config) == False:
        print('app_logic : tester present test failed')
        app_ui.set_btn_enabled('BROWSE_BTN', True)

def upload_file():
    print('app_logic : initiating file upload...')
    app_ui.append_log('initiating file upload...')

    app_ui.set_btn_enabled('BROWSE_BTN', False)

    app_comm.perform_service_tests()

def reset_ecu():
    print('app_logic : resetting ecu...')
    app_ui.append_log('resetting ecu...')

    handle = app_comm.g_pcan_handle
    config = app_comm.g_pcan_config
    threading.Thread(target=app_comm.testECUReset, args=(handle, config)).start()
    # app_comm.testECUReset(handle, config)

# Function to handle application exit
def on_close():
    app_ui.reset_sysout()
    handle = app_comm.g_pcan_handle
    app_comm.objPCANUds.Uninitialize_2013(handle)
  #  g_ui_main_window.destroy()
    print('app_logic : destroyed ui root')
