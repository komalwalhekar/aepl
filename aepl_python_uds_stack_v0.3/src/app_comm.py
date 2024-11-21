'''
Copyright 2024-2025 Accolade Electronics Pvt. Ltd

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
version 2 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

file        app_comm.py
brief       This is the source file for the UDS stack integration

date        01 Apr 2024
author      Accolade Electronics <www.accoladeelectronics.com>
'''

# For PCAN stack python modules
import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uds_stack'))

########################################### (UDS over CAN: core initialization) ####################################################

import threading                # for file upload thread
import time                     # for sleeping
from PCAN_UDS_2013 import *     # for UDS stack
from ctypes import c_uint16

# A global counter to keep track of the number of failed tests (see display_uds_msg function)
g_nbErr = 0

# import the dlls required for stack
from pathlib import Path

dll_path = Path(__file__).resolve().parent /'uds_stack'
sys.path.insert(0, str(dll_path))
os.add_dll_directory(str(dll_path))

# create uds library object
objPCANUds = PCAN_UDS_2013()

g_pcan_handle = PCANTP_HANDLE_USBBUS1
g_pcan_config = uds_msgconfig()

def test_result_to_string(test):
    return 'Success' if test else 'Fail'

def print_test_status(test):
    return test_result_to_string(objPCANUds.StatusIsOk_2013(test, PUDS_STATUS_OK, False))

def can_init(bit_rate, tester_id, ecu_id, iso_tp_addressing_mode):
    print(f'app_comm  : bit_rate              : {bit_rate}')
    print(f'app_comm  : tester_id             : {tester_id:X}')
    print(f'app_comm  : ecu_id                : {ecu_id:X}')
    print(f'app_comm  : iso_tp_addressing_mode: {iso_tp_addressing_mode}')

    # Print version information
    buff_size = 256
    buffer = create_string_buffer(buff_size)
    status = objPCANUds.GetValue_2013(PCANTP_HANDLE_NONEBUS, PUDS_PARAMETER_API_VERSION, buffer, buff_size)
    print('app_comm  : PCAN-UDS API Version - %s: %s' % (buffer.value, print_test_status(status)))

    # Initialize channel
    if bit_rate == '250Kbps':
        status = objPCANUds.Initialize_2013(g_pcan_handle, PCANTP_BAUDRATE_250K, 0, 0, 0)
    if bit_rate == '500Kbps':
        status = objPCANUds.Initialize_2013(g_pcan_handle, PCANTP_BAUDRATE_500K, 0, 0, 0)
    if bit_rate == '1Mbps':
        status = objPCANUds.Initialize_2013(g_pcan_handle, PCANTP_BAUDRATE_1M, 0, 0, 0)
    print('app_comm  : Initialize channel: %s' % (print_test_status(status)))

    if print_test_status(status) == 'Fail':
        return False

    # Get timeout values
    timeout_request = c_uint32(0)
    status = objPCANUds.GetValue_2013(g_pcan_handle, PUDS_PARAMETER_TIMEOUT_REQUEST, timeout_request,
                                    sizeof(timeout_request))
    print('app_comm  : Get request timeout value (%ums): %s' % (timeout_request.value, print_test_status(status)))
    customTimeOut = c_uint32(timeout_request.value * 2)
    status = objPCANUds.SetValue_2013(g_pcan_handle,
                                    PUDS_PARAMETER_TIMEOUT_REQUEST,
                                    customTimeOut, sizeof(customTimeOut))
    print('app_comm  : Set request timeout value (%ums): %s' % (customTimeOut.value, print_test_status(status)))
    status = objPCANUds.GetValue_2013(g_pcan_handle, PUDS_PARAMETER_TIMEOUT_REQUEST, timeout_request,
                                    sizeof(timeout_request))
    print('app_comm  : Get request timeout value (%ums): %s' % (timeout_request.value, print_test_status(status)))

    timeout_response = c_uint32(0)
    status = objPCANUds.GetValue_2013(g_pcan_handle, PUDS_PARAMETER_TIMEOUT_RESPONSE, timeout_response,
                                    sizeof(timeout_response))
    print('app_comm  : Get response timeout value (%ums): %s' % (timeout_response.value, print_test_status(status)))
    customTimeOut = c_uint32(timeout_response.value * 2)
    status = objPCANUds.SetValue_2013(g_pcan_handle,
                                    PUDS_PARAMETER_TIMEOUT_RESPONSE,
                                    customTimeOut, sizeof(customTimeOut))
    print('app_comm  : Set response timeout value (%ums): %s' % (customTimeOut.value, print_test_status(status)))
    status = objPCANUds.GetValue_2013(g_pcan_handle, PUDS_PARAMETER_TIMEOUT_RESPONSE, timeout_response,
                                    sizeof(timeout_response))
    print('app_comm  : Get response timeout value (%ums): %s' % (timeout_response.value, print_test_status(status)))

    # CAN-TP PRIORITY bits.
    can_tp_prio = c_uint32(0)
    status = objPCANUds.GetValue_2013(g_pcan_handle, PUDS_PARAMETER_J1939_PRIORITY, can_tp_prio,
                                    sizeof(can_tp_prio))
    print('app_comm  : Get default PUDS_PARAMETER_J1939_PRIORITY (%ums): %s' % (can_tp_prio.value, print_test_status(status)))

    # TODO: Priority bits. understand why is it required for "TCU (chetak) and GRAD". other projects may vary
    if tester_id == 0x0CDA33F1:
        can_tp_prio = c_uint32(3)
        status = objPCANUds.SetValue_2013(g_pcan_handle,
                                        PUDS_PARAMETER_J1939_PRIORITY,
                                        can_tp_prio, sizeof(can_tp_prio))
        print('app_comm  : New PUDS_PARAMETER_J1939_PRIORITY (%ums): %s' % (can_tp_prio.value, print_test_status(status)))

    # Add can id filter
    # Dev Note: Write DID fails if filter is not added
    status = objPCANUds.AddCanIdFilter_2013(g_pcan_handle, ecu_id)
    print('app_comm  : Add can id filter (0x%X): %s' % (ecu_id, print_test_status(status)))

    # extract the source and destination ids. ECU is UDS server and Tester is UDS client
    # client_id = tester_id & 0x00000FF
    # server_id = ecu_id & 0x00000FF

    client_id = tester_id & 0x00000FF
    server_id = ecu_id & 0x00000FF

    # Define Network Address Information used for all the tests
    g_pcan_config.can_id = tester_id
    g_pcan_config.can_msgtype = PCANTP_CAN_MSGTYPE_EXTENDED

    # TODO: study which CAN ids requires the EXTENDED protocol, and which the NORMAL
    # The following if/else can be then done based on ID instead of
    # user defined configuration
    nai_protocol = iso_tp_addressing_mode
    if nai_protocol == '29B_EXTENDED':
        g_pcan_config.nai.protocol = PUDS_MSGPROTOCOL_ISO_15765_2_29B_EXTENDED 
    elif nai_protocol == '29B_FIXED_NORMAL':
        g_pcan_config.nai.protocol = PUDS_MSGPROTOCOL_ISO_15765_2_29B_FIXED_NORMAL
    elif nai_protocol == '29B_DYNAMIC':
        g_pcan_config.nai.protocol = PUDS_MSGPROTOCOL_ISO_15765_2_29B_DYNAMIC   
    else:
        g_pcan_config.nai.protocol = PUDS_MSGPROTOCOL_ISO_15765_2_29B_NORMAL

    g_pcan_config.nai.target_type = PCANTP_ISOTP_ADDRESSING_PHYSICAL
    g_pcan_config.type = PUDS_MSGTYPE_USDT
    g_pcan_config.nai.source_addr = client_id
    g_pcan_config.nai.target_addr = server_id

    print(f'app_comm  : PCAN initialized with bit rate {bit_rate}, server id {hex(server_id)}, client id {hex(client_id)}')
    return True

########################################### (UDS over CAN: service tests) ####################################################

g_file_path = ''
g_file_size = 0

# def test_read_write_did():
#     handle = g_pcan_handle
#     config = g_pcan_config

#     if testDiagnosticSessionControl(handle, config) == False:
#         print('Accessing session control fail')
#     elif testSecurityAccess(handle, config) == False:
#         print('Fail Security Access')
    
#     readVinDid = 0xF190 #Harsh Break threshold
#     writeVinDid = 0xF190

#     #not working for DIET (probably not implemented or using different DID)
#     if testReadDataByIdentifier(handle, config, readVinDid) == False:
#         print('app_comm  : read data by id test failed')
    
    # vinNo = 'DIET_2327'
    # vinNo = create_string_buffer(vinNo.encode('utf-8'))

    # if testWriteDataByIdentifier(handle, config, writeVinDid, vinNo, sizeof(vinNo)) == False:
    #     print('VinNo Write DID fail')

def test_read_write_did(handle, config, dids):

    handle = g_pcan_handle
    config = g_pcan_config

        # Accessing session control
    if testDiagnosticSessionControl(handle, config) == False:
        print(f'Accessing session control failed for DID: {hex(did)}')
          # Skip the current DID and proceed with the next one
    
    # Security access check
    if testSecurityAccess(handle, config) == False:
        print(f'Fail Security Access for DID: {hex(did)}')
          # Skip the current DID and proceed with the next one

    # Iterate over the list of DIDs passed to the function
    for did in dids:
        print(f"Testing DID: {hex(did)}")
        
        # Reading data by identifier
        if testReadDataByIdentifier(handle, config, did) == False:
            print(f'app_comm  : read data by id test failed for DID: {hex(did)}')
        
        # # Write test (if required)
        # if testWriteDataByIdentifier(handle, config, did) == False:
        #     print(f'app_comm  : write data by id test failed for DID: {hex(did)}')


   

def testReadDataByIdentifier(channel, config, did):
    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()
    result = False

    print('\n\n*** UDS Service: ReadDataByIdentifier ***')

    # Wrap `did` in a ctypes object (e.g., c_uint16 for 16-bit DID)
    data_identifier = c_uint16(did)

    # Sends a physical ReadDataByIdentifier message
    status = objPCANUds.SvcReadDataByIdentifier_2013(channel, config, request, data_identifier, 1)
    
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcReadDataByIdentifier_2013: %x' % (status.value))
    
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: ReadDataByIdentifier [' + hex(did) + '] :' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    
    return result


def testControlDTCSetting(channel, config, controlParameter):
    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()
    result = False

    # Sends a physical ControlDTCSetting message
    print('\n\nSends a physical ControlDTCSetting message: ')
    dtc_setting_control_option_record = (c_uint8 * 1)(0x00)
    status = objPCANUds.SvcControlDTCSetting_2013(channel, config, request, controlParameter,
                                                  dtc_setting_control_option_record, 0)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcControlDTCSetting_2013: %i' % (status.value))
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: ControlDTCSetting: ' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

def testDiagnosticSessionControl(channel, config):
    request = uds_msg()
    response = uds_msg()
    session_info = uds_sessioninfo()
    confirmation = uds_msg()
    status = objPCANUds.SvcDiagnosticSessionControl_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_DSC_ECUPS)
    print('Execute Diagnostic Session Control service: %s' % (print_test_status(status)))
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    result = False
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: DiagnosticSessionControl: ' + test_result_to_string(result))

    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

def testSecurityAccess(channel, config):
    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()
    value_little_endian = 0xF0A1B2C3
    security_access_data = Reverse32(value_little_endian)
    status = objPCANUds.SvcSecurityAccess_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_SA_RSD_1,
                                               security_access_data, 4)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcSecurityAccess_2013: %i' % (status.value))
    result = False
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)

    if result == True:
        status = objPCANUds.SvcSecurityAccess_2013(channel, config, request,
                                                   objPCANUds.PUDS_SVC_PARAM_SA_SK_2,
                                                   security_access_data, 4)
        if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
            status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
        print(' UDS_SvcSecurityAccess_2013: %i' % (status.value))
        if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
            result = display_uds_msg_validate(confirmation, response, False)
        else:
            result = display_uds_msg_validate(request, None, False)

    print('UDS Service: SecurityAccess: ' + test_result_to_string(result))

    return result

def testLinkControl(channel, config):
    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()
    result = False

    # Sends a physical LinkControl message
    print('\n\nSends a physical LinkControl message (Verify Fixed Baudrate): ')
    status = objPCANUds.SvcLinkControl_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_LC_VBTWFBR,
                                            objPCANUds.PUDS_SVC_PARAM_LC_BAUDRATE_CAN_500K, 0)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcLinkControl_2013: %i' % (status.value))
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: LinkControl: ' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

def testAccessTimingParameter(channel, config):
    request_record = create_string_buffer(b'\xAB\xCD')
    record_size = c_uint32(2)

    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()
    request_record[0] = getCChar(0xAB)
    request_record[1] = getCChar(0xCD)

    # Sends a physical AccessTimingParameter message
    print('\n\nSends a physical AccessTimingParameter message: ')
    status = objPCANUds.SvcAccessTimingParameter_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_ATP_RCATP,
                                                      request_record, record_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcAccessTimingParameter_2013: %d' % (status.value))
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: AccessTimingParameter: ' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

def testWriteDataByIdentifier(channel, config, did, data_record, data_record_size):
    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()

    # Sends a physical WriteDataByIdentifier message
    print('\n\nSends a physical WriteDataByIdentifier message: ')
    status = objPCANUds.SvcWriteDataByIdentifier_2013(channel, config, request, did, data_record, data_record_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcWriteDataByIdentifier_2013: %i' % (status.value))
    result = False
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: WriteDataByIdentifier [' + hex(did) + '] :' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

def testRoutineControlFlashErase(channel, config):
    routine_control_option_record = create_string_buffer(1)
    routine_control_option_record_size = 1

    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()
    result = False

    print('\n\n*** UDS Service: RoutineControl Erasing Flash***')

    # Sends a physical RoutineControl message
    print('\n\nSends a physical RoutineControl message: ')
    for i in range(routine_control_option_record_size):
        routine_control_option_record[i] = 0x0

    status = objPCANUds.SvcRoutineControl_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_RC_STR, 0x2001,
                                               routine_control_option_record, routine_control_option_record_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcRoutineControl_2013 Start: %i' % (status.value))

    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)

    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()

    status = objPCANUds.SvcRoutineControl_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_RC_STPR, 0x2001,
                                               routine_control_option_record, routine_control_option_record_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcRoutineControl_2013 Stop: %i' % (status.value))

    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)

    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()

    status = objPCANUds.SvcRoutineControl_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_RC_RRR, 0x2001,
                                               routine_control_option_record, routine_control_option_record_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcRoutineControl_2013 Result: %i' % (status.value))
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: RoutineControl Erasing Flash: ' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

def testRequestDownload(channel, config):
    memory_address_buffer = create_string_buffer(4)
    memory_size_buffer = create_string_buffer(4)
    memory_address_size = 4
    memory_size_size = 4

    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()

    print('\n\n*** UDS Service: RequestDownload ***')

    # Sends a physical RequestDownload message
    for i in range(memory_address_size):
        memory_address_buffer[i] = 0xFF
        memory_size_buffer[i] = (g_file_size & (0x01 < i)) > i
        print(memory_size_buffer[i])
        print(' ')

    status = objPCANUds.SvcRequestDownload_2013(channel, config, request, 0x0, 0x0, memory_address_buffer,
                                                memory_address_size, memory_size_buffer,
                                                memory_size_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    result = False
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: RequestDownload: ' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

def testTrasferFile(channel, config, file_path, file_size):
    file_transfer_thread = threading.Thread(target=transfer_file, args=(channel, config,  file_path, file_size))
    file_transfer_thread.start()

################################################## TMP START

def readFileInChunk(offset, chunk_size):
    with open(g_file_path, 'rb') as file:
        file.seek(offset)
        readChukData = file.read(chunk_size)
    return readChukData, len(readChukData)

def transfer_file(channel, config, file_path, file_size):
    print(f'transferring file {file_size} {file_path}')
    chunk_size = 254
    sequence = 0
    fileOffset = 0
    index = 0
    status = True
    while index < g_file_size - 1:
        data, read_bytes = readFileInChunk(fileOffset, chunk_size)
        print(f'Offset : {fileOffset}, read_bytes : {read_bytes}, seq : {sequence}')
        fileOffset = read_bytes + fileOffset
        update_progress_bar(file_size, fileOffset)
        index = fileOffset
        status &= testTransferData(channel, config, read_bytes, data, sequence)
        sequence = sequence + 1

def testTransferData(channel, config, size, buffer, sequence):
    record = create_string_buffer(size)
    record_size = size

    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()

    for i in range(record_size):
        record[i] = buffer[i]

    status = objPCANUds.SvcTransferData_2013(channel, config, request, sequence, record, record_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcTransferData_2013: %i' % (status.value))
    result = False
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: TransferData: [' + str(sequence) + '] :' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

################################################## TMP END

def testRequestTransferExit(channel, config):
    record = create_string_buffer(50)
    record_size = 2

    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()

    print('\n\n*** UDS Service: RequestTransferExit ***')

    for i in range(record_size):
        record[i] = 0xFF

    status = objPCANUds.SvcRequestTransferExit_2013(channel, config, request, record, record_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    result = False
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: RequestTransferExit: ' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

def testRoutineControlCrcCheck(channel, config):
    routine_control_option_record = create_string_buffer(2)
    routine_control_option_record_size = 2

    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()
    result = False

    print('\n\n*** UDS Service: RoutineControl Erasing Flash***')

    # Sends a physical RoutineControl message
    print('\n\nSends a physical RoutineControl message: ')
    for i in range(routine_control_option_record_size):
        routine_control_option_record[i] = 0x0

    status = objPCANUds.SvcRoutineControl_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_RC_STR, 0x2002,
                                               routine_control_option_record, routine_control_option_record_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcRoutineControl_2013 Start: %i' % (status.value))

    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)

    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()

    status = objPCANUds.SvcRoutineControl_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_RC_RRR, 0x2002,
                                               routine_control_option_record, routine_control_option_record_size)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcRoutineControl_2013 Result: %i' % (status.value))
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: RoutineControl Erasing Flash: ' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

def testECUReset(channel, config):
    request = uds_msg()
    response = uds_msg()
    confirmation = uds_msg()

    print('\n\n*** UDS Service: ECUReset ***')

    # Sends a physical ECUReset message
    print('\n\nSends a physical ECUReset message: ')
    status = objPCANUds.SvcECUReset_2013(channel, config, request, objPCANUds.PUDS_SVC_PARAM_ER_HR)
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        status = objPCANUds.WaitForService_2013(channel, request, response, confirmation)
    print(' UDS_SvcECUReset_2013: %i' % (status.value))
    if objPCANUds.StatusIsOk_2013(status, PUDS_STATUS_OK, False):
        result = display_uds_msg_validate(confirmation, response, False)
    else:
        result = display_uds_msg_validate(request, None, False)

    print('UDS Service: ECUReset: ' + test_result_to_string(result))

    # Free messages
    status = objPCANUds.MsgFree_2013(request)
    status = objPCANUds.MsgFree_2013(response)
    status = objPCANUds.MsgFree_2013(confirmation)
    return result

########################################### (UDS over CAN: helpers for service tests) ####################################################

def getCChar(c):
    return c if sys.version_info.major >= 3 else chr(c)

def Reverse32(v):
    res = create_string_buffer(4)
    res[3] = getCChar(v & 0x000000FF)
    res[2] = getCChar((v >> 8) & 0x000000FF)
    res[1] = getCChar((v >> 16) & 0x000000FF)
    res[0] = getCChar((v >> 24) & 0x000000FF)
    return res

def display_uds_msg_validate(request, response, no_response_expected):
    '''
    A function that displays UDS Request and Response messages (and count error if no response)

    parameters:
     request: Request message
     response: Received response message
     no_response_expected: if no response is expected, do not increment error counter
    '''
    global g_nbErr
    if request != None and request.msg.msgdata.isotp:
        print('\nUDS request from 0x%04X (to 0x%04X, with extension address 0x%02X) - result: %i - %s' % (
            request.msg.msgdata.isotp.contents.netaddrinfo.source_addr,
            request.msg.msgdata.isotp.contents.netaddrinfo.target_addr,
            request.msg.msgdata.isotp.contents.netaddrinfo.extension_addr,
            request.msg.msgdata.any.contents.netstatus,
            'ERROR !!!' if request.msg.msgdata.any.contents.netstatus != PCANTP_NETSTATUS_OK.value else 'OK !'))
        # display data
        s = '\t-> Length: {x1}, Data= '.format(x1=format(request.msg.msgdata.any.contents.length, 'd'))
        for i in range(request.msg.msgdata.any.contents.length):
            s += '{x1} '.format(x1=format(request.msg.msgdata.any.contents.data[i], '02X'))

        print(s)

    if response != None and response.msg.msgdata.isotp:
        print('\nUDS RESPONSE from 0x%04X (to 0x%04X, with extension address 0x%02X) - result: %i - %s' % (
            response.msg.msgdata.isotp.contents.netaddrinfo.source_addr,
            response.msg.msgdata.isotp.contents.netaddrinfo.target_addr,
            response.msg.msgdata.isotp.contents.netaddrinfo.extension_addr, response.msg.msgdata.any.contents.netstatus,
            ('ERROR !!!' if response.msg.msgdata.any.contents.netstatus != PCANTP_NETSTATUS_OK.value else 'OK !')))
        # display data
        s = '\t-> Length: {x1}, Data= '.format(x1=format(response.msg.msgdata.any.contents.length, 'd'))
        for i in range(response.msg.msgdata.any.contents.length):
            s += '{x1} '.format(x1=format(response.msg.msgdata.any.contents.data[i], '02X'))

        print(s)

        respSID = request.msg.msgdata.any.contents.data[0] + 0x40
        if respSID == response.msg.msgdata.any.contents.data[0]:
            print('Positive Response')
            return True

        elif 0x7F == response.msg.msgdata.any.contents.data[0]:
            print('Negative Response')
            g_nbErr += 1
            return False
        else:
            print('Invalid Response')
            g_nbErr += 1
            return False

    elif not no_response_expected:
        print('\n      ERROR: NO UDS RESPONSE !!\n')
        g_nbErr += 1
        return False
