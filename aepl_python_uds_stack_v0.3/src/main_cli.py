#!/usr/bin/env python3
'''\
Copyright 2024-2025 Accolade Electronics Pvt. Ltd

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
version 2 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

file        main_cli.py
brief       This is the main script file for launching the service tool application

date        12 Nov 2024
author      Accolade Electronics <www.accoladeelectronics.com>

tested on python 3.11.8 on windows 11 x64

# dependencies
PCAN drivers must be installed

# run the script to launch app
launch_app.sh
'''

import app_comm
import app_logic

bit_rate = '250Kbps'
tester_id = '0CDA33F1'   # Utility tester ID
ecu_id = '0CDAF133'      # SAMPARK ECU ID
iso_tp_addressing_mode = '29B_FIXED_NORMAL'


# bit_rate = '250Kbps'
# tester_id = '18FF914C'   # Utility tester ID 18FF914C
# ecu_id = '0CDAF133'      # SAMPARK ECU ID
# iso_tp_addressing_mode = '29B_NORMAL'
#'29B_NORMAL' - Response observed on PCAN 
#'29B_DYNAMIC' - Response observed on PCAN 
#'29B_EXTENDED' - No Response observed on PCAN (Data0-0x33  payload changed)
#'29B_MIXED' - No Response observed on PCAN


# int_tester_id = int(tester_id, 16)
# int_ecu_id = int(ecu_id, 16)

# if app_comm.can_init(bit_rate, int_tester_id, int_ecu_id, iso_tp_addressing_mode) == True:
#     app_comm.test_read_write_did()
# else:
#     print("Error", "Access denied or hardware not connected")


# GUI INTEGRATION #

int_tester_id = int(tester_id, 16)
int_ecu_id = int(ecu_id, 16)

app_logic.create_gui()

