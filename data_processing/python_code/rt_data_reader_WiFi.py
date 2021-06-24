import argparse
import collections
import datetime
import itertools
import os
import sys
import time
import timeit
import pandas as pd
import serial
import platform
import numpy as np
import threading
import json
import data_processing.python_code.utilities.data_acquisition as acq
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


def main(save_data: bool, detect_seizure: bool, result_dir: str, serial_baud_r: int, recording_time: float,
         acquired_signals: list,
         serial_port=None, sf=100, ft_window_s=1, window_overlap=50):
    """Reads the acceleration, pulse and EDA signals acquired from the Firebase. This script is not fully functional."""

    global arduino, first_ft_window, read_line_str, window_overlap_frac, mag_list, abs_fft_list, times_fft, target_ref, node_name, root_ref, abs_fft_vm_list, abs_fft_sma_list, vm_weights, sma_weights, detection_window_it, scr_vm_sum, scr_sma_sum, detection_window, VM_thrs, SMA_thrs, curr_len
    default, port = check_default_port(serial_port)  # the Port name as a string

    # Initializing firebase credentials and URL
    cred = credentials.Certificate("WiFi_database//key.json")
    url_firebase = {'databaseURL': 'https://esp32wifitest-4f0ee-default-rtdb.europe-west1.firebasedatabase.app/'}
    firebase_admin.initialize_app(cred, url_firebase)

    try:
        root_ref = db.reference("/")
        print('Successfully connected to ' + url_firebase['databaseURL'] + ' at ' + str(serial_baud_r) + ' BAUD.')

    except:
        print('Failed to connect to ' + url_firebase['databaseURL'] + ' at ' + str(serial_baud_r) +
              'BAUD.')

    print("...accessing data base nodes")


    # Opening JSON file

    json_path = 'WiFi_database/avail_nodes.json'
    f = open(json_path, )

    # returns JSON object as
    # a dictionary
    stored_data = json.load(f)
    found_new_node = False

    print("...searching for node update")

    while not found_new_node:
        data = root_ref.get(shallow=True)
        for key, val in data.items():
            if key not in stored_data:
                print(key)
                node_name = key
                found_new_node = True
                print('found new node!')

    with open(json_path, 'w') as file:
        json.dump(data, file)
    f.close()

    """Initialising variables"""

    data_ac = acq.data_recorder(wifi=True)
    raw_data = []

    target_ref = db.reference("/" + node_name)

    # target_ref = db.reference("/" + "2021-06-23_00:41:03")

    """Receiving data and storing it in a list"""

    print("transmission started...")
    print(" ")

    # reading the first line and saving the starting time

    first_line_ref = target_ref.order_by_key().limit_to_last(1).get()
    print(type(first_line_ref))
    print(first_line_ref)
    print(1)

    # last_JSON

    # Data_dict = list(first_line_ref.items())[0][1]
    # Data_str = list(Data_dict.items())[0][1]
    # Data = np.array(list(map(lambda x: x.split(","), Data_str))).astype(np.float)

    print(type(first_line_ref))
    print(first_line_ref)
    print(2)
    if type(first_line_ref) is list:
        Data_dict = first_line_ref[1]

    if type(first_line_ref) is collections.OrderedDict:
        Data_dict = list(first_line_ref.items())[0][1]

    print(3)
    print(type(Data_dict))
    print(Data_dict)

    first_read_line = Data_dict['Data']

    time_i_str = first_read_line[0].split(",")[0]
    time_i = int(float(time_i_str))

    print(time_i)
    time_curr = time_i

    interval_mark = 1

    if detect_seizure:
        # commented for manual threshold input ---------------

        # threshold_param_file = "experiment_a.csv"
        # path_to_thresholds = os.path.join(os.path.dirname(sys.argv[0]), "classification_results", threshold_param_file)
        path_to_spectral_weights = os.path.join(os.path.dirname(sys.argv[0]), "data", "results", "2021-06-12-22-50-19",
                                                "a", "spectral_weights_a.csv")

        df_spectral_weights = pd.read_csv(path_to_spectral_weights, index_col=[0])
        vm_weights = np.transpose(df_spectral_weights['VM weights'].to_numpy())
        sma_weights = np.transpose(df_spectral_weights['SMA weights'].to_numpy())

        # commented for manual threshold input ---------------

        VM_thrs = 1.7065725297694536  # max_params.iloc[0]['VM thrs.'] ,
        SMA_thrs = 1.6968069180073173  # max_params.iloc[0]['SMA thrs.']

        print(VM_thrs)

        first_ft_window = True
        read_line_str = collections.deque([first_read_line])
        window_overlap_frac = 100 // window_overlap
        mag_list = []
        abs_fft_vm_list = []
        abs_fft_sma_list = []
        times_fft = []
        detection_window = 5  # seconds
        detection_window_it = 0
        scr_vm_sum = 0
        scr_sma_sum = 0
        scr_vm = 0
        scr_sma = 0

    # recording data until the recording_time stopping criterion is met
    len_data = len(target_ref.get(shallow=True))
    curr_len = len_data

    while time_curr - time_i < recording_time * 1000 * 60:

        # delaying the loop until new data chunk arrives
        while curr_len != len_data:
            curr_len = len(target_ref.get(shallow=True))

        first_line_ref = target_ref.order_by_key().limit_to_last(1).get()

        len_data = curr_len # updating new nr of data chunks

        if type(first_line_ref) is list:
            Data_dict = first_line_ref[1]

        if type(first_line_ref) is collections.OrderedDict:
            Data_dict = list(first_line_ref.items())[0][1]

        read_line_str = Data_dict['Data']    # read_line_key[1]['Data']  # time, acc_x, acc_y, acc_z, pulse, eda

        time_curr_str = read_line_str[0].split(",")[0]
        time_curr = int(float(time_curr_str))

        # if ((time_curr - time_i) * 0.001) % 10 == 0:
        #     print("{}x10 seconds were recorded".format(interval_mark))
        #     interval_mark += 1

        # TODO: detection algorithm (every 1 second)
        if detect_seizure:

            # TODO: until here, we have (sf * ft_window_s) + 1 points = ft_window_s seconds.
            abs_ft_vm_arr, abs_ft_sma_arr = detection_algorithm(read_line_str)
            times_fft.append(time_curr - time_i)
            abs_fft_vm_list.append(abs_ft_vm_arr)
            abs_fft_sma_list.append(abs_ft_sma_arr)

            vm_num = np.squeeze(np.multiply(abs_ft_vm_arr, vm_weights))
            sma_num = np.squeeze(np.multiply(abs_ft_sma_arr, sma_weights))

            scr_vm = np.divide(np.sum(vm_num, axis=0), np.sum(np.squeeze(abs_ft_vm_arr), axis=0))
            scr_sma = np.divide(np.sum(sma_num, axis=0), np.sum(np.squeeze(abs_ft_sma_arr), axis=0))

            detection_window_it += 1
            scr_vm_sum += scr_vm
            scr_sma_sum += scr_sma

        if detection_window_it == 5:

            scr_vm_avg = scr_vm_sum / (detection_window_it)
            scr_sma_avg = scr_sma_sum / (detection_window_it)

            print(scr_vm_avg, scr_sma_avg)

            if scr_vm_avg > VM_thrs and scr_sma_avg > SMA_thrs:
                db.reference("/").child("s").set({"s": "s"})
                # print('...SEIZURE DETECTED!!!!!!')

            else:
                pass
                # print('...normal')

            scr_vm_sum = 0
            scr_sma_sum = 0
            scr_vm_avg = 0
            scr_sma_avg = 0

            detection_window_it = 0

    print("...transmission finished")

    if save_data:
        print("checking on acquired data...")
        data_ac.clean_raw_data(save_delays=True, sf=sf)
        data_ac.print_delays()

        # generate result directory if it does not exist
        os.makedirs(result_dir, exist_ok=True)

        print("saving acquired data...")
        data_ac.save_data_to_csv(result_dir, df_header=acq.getHeaderfromSignals(acquired_signals))

        t = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')  # string with the date of the experiment

        # data_fft, header_fft = write_2(times_fft, mag_list, abs_fft_list)
        # df_fft = pd.DataFrame(data_fft)
        #
        #
        # df_fft.to_csv(os.path.join(result_dir, 'rt_data_fft_windows_{}.csv'.format(t)), header=header_fft,
        #               sep=",")  # saving csv file
        # print('FFT data saved as ' + os.path.join(result_dir, 'rt_data_fft_windows_{}.csv'.format(t)))


def detection_algorithm(data_chunk: list, magnitude=True):
    # implement an algorithm based on the following article https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5375767/ [1]
    # check this one too https://odr.chalmers.se/bitstream/20.500.12380/145997/1/145997.pdf

    # TODO: compute the FFT weights based on a series of seizure vs baseline datasets [1]
    vm_arr, sma_arr = getArrayfromStringList(data_chunk)

    abs_ft_vm_arr = np.abs(np.fft.rfft(vm_arr))
    abs_ft_sma_arr = np.abs(np.fft.rfft(sma_arr))

    return abs_ft_vm_arr, abs_ft_sma_arr


def write_2(times_fft_l, mag_l, abs_fft_l):
    newl = []
    # time_start: getting the first time measurement to shift time values

    for i in range(len(times_fft_l)):

        temp_l = str(times_fft_l[i])
        mag_arr = np.squeeze(mag_l[i])
        abs_fft_arr = np.squeeze(abs_fft_l[i])

        for j in range(np.size(mag_arr) - 1):  # check dimensions to print 3 values
            temp_l = temp_l + "," + str(mag_arr[j])

        temp_l = temp_l + "," + str(mag_arr[-1])

        for j in range(np.size(abs_fft_arr) - 1):
            temp_l = temp_l + "," + str(abs_fft_arr[j])

        temp_l = temp_l + "," + str(abs_fft_arr[-1])

        temp_l = temp_l.replace(" ", "")
        temp_l = temp_l.split(',')
        newl.append(temp_l)

    header = []

    size_mag = np.size(np.squeeze(mag_l[0]))
    size_abs_fft = np.size(np.squeeze(abs_fft_l[0]))

    header.append('time')
    for i in range(size_mag):
        header.append('mag at point {}'.format(str(i)))
    for i in range(size_abs_fft):
        header.append('fft bin {}'.format(str(i)))

    return newl, header


def getArrayfromStringList(data_lines: list):

    data_arr_vm = np.zeros((1, len(data_lines)))  # [mag_acc_t1, mag_acc_t2, ..., mag_acc_tn]
    data_arr_sma = np.zeros((1, len(data_lines)))
    for i in range(len(data_lines)):
        temp = data_lines[i].replace(" ", "")
        temp = temp.split(',')
        data_arr_vm[0, i] = np.linalg.norm(np.array([float(temp[1]), float(temp[2]), float(temp[3])]))
        data_arr_sma[0, i] = (abs(float(temp[1])) + abs(float(temp[2])) + abs(float(temp[3]))) / 3

    return data_arr_vm, data_arr_sma


def check_default_port(port_name):
    port_str = port_name
    default = False
    if platform.system() == 'Windows' and port_name is None:  # for windows OS
        port_str = 'COM3'  # change to default
        default = True
    elif platform.system() == 'Darwin' and port_name is None:  # for MAC OS
        port_str = '/dev/ttyUSB0'  # change to default
        default = True
    elif platform.system() == 'Linux' and port_name is None:  # for GNU/Linux OS
        port_str = '/dev/ttyUSB0'  # change to default
        default = True

    return default, port_str


def listener(event):
    print(event.event_type)  # can be 'put' or 'patch'
    print(event.path)  # relative to the reference, it seems
    print(event.data)  # new data at /reference/event.path. None if deleted


if __name__ == "__main__":
    """The program's entry point."""

    script_dir = os.path.dirname(sys.argv[0])

    parser = argparse.ArgumentParser(description='Arduino-based acquisition of acceleration, pulse and EDA signals')

    parser.add_argument(
        '--save_data',
        type=bool,
        default=False,
        help='Set to True to save data in a .csv file.'
    )

    parser.add_argument(
        '--detect_seizure',
        type=bool,
        default=True,
        help='Set to True to enable real-time seizure detection'
    )

    parser.add_argument(
        '--result_dir',
        type=str,
        default=os.path.normpath(os.path.join(script_dir, 'data')),
        help='Directory for results (useless if save_data = False).'
    )

    parser.add_argument(
        '--serial_baud_r',
        type=int,
        default=115200,
        help='Baud rate used in the ESP32.'
    )

    parser.add_argument(
        '--recording_time',
        type=float,
        default=45,
        help='Time in minutes or fraction of minutes the data acquisition will take.'
    )

    parser.add_argument(
        '--acquired_signals',
        type=list,
        default=['time', 'acc', 'pulse', 'eda'],
        help='A list of the names of the signals needed to be acquired. Edit it if you do not have some sensors.'
    )

    parser.add_argument(
        '--serial_port',
        type=str,
        default='COM6',
        help='Name of the serial port, depending on the OS and computer itself.'
    )

    args = parser.parse_args()
    main(args.save_data, args.detect_seizure, args.result_dir, args.serial_baud_r, args.recording_time,
         args.acquired_signals,
         args.serial_port)
