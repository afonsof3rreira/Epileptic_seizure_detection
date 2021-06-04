import os

import pandas as pd
import datetime


# class fft_training:
#     def __init__(self, training):
#         pass
#
#     def func:
#         pass

class data_recorder:
    def __init__(self, time_reset=True, wifi=False):
        self.sampling_delays = None
        self.raw_data = []
        self.time_reset = time_reset
        self.output_data = []
        if time_reset:
            self.starting_time = None
        self.wifi = wifi

    def add_acquisition(self, raw_acquisition: str):
        self.raw_data.append(raw_acquisition)

    def clean_raw_data(self, save_delays=False, sf=None):
        """each row of the raw data is acquired as b'XXXXXXXX\r\n', where XXXXXXXX
        is the readable data (ASCII) of varying length, thus we need to remove first 2 chars + 5 last chars
        """
        if save_delays ^ bool(sf is not None):
            raise ValueError('In order to save delays, a sampling frequency has to be provided')

        global temp_prev, t_s, sampling_delays

        if save_delays and sf is not None:  # then check for delays
            self.sampling_delays = []
            t_s = 1000 / sf
            temp_prev = -t_s  # time_start: getting the first time measurement to shift time values

        if self.time_reset:
            self.set_starting_time()

        for i in range(len(self.raw_data)):
            temp_current = self.raw_data[i].replace(" ", "")

            if self.wifi:
                temp_current = temp_current.split(',')
                temp_time = temp_current[0][:-3]
            else:
                temp_current = temp_current[2:-5].split(',')
                temp_time = temp_current[0]

            if self.time_reset:
                temp_current[0] = str(int(temp_time) - self.starting_time)

            self.output_data.append(temp_current)

            if save_delays and sf is not None:
                if int(temp_current[0]) - temp_prev != t_s:
                    self.sampling_delays.append([i - 1, i])

                temp_prev = int(temp_current[0])

    def save_data_to_csv(self, output_path: str, df_header: list, filename_extension=None):
        df = pd.DataFrame(self.output_data)  # creating dataframe
        if filename_extension is None:
            time_str = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')  # string with the date of the experiment
        else:
            time_str = filename_extension

        if self.wifi:
            format_str = 'rt_data_wifi_{}.csv'
        else:
            format_str = 'rt_data_usb_{}.csv'

        df.to_csv(os.path.join(output_path, format_str.format(time_str)), header=df_header,
                  sep=",")  # saving csv file

        print('Acquired data saved as ' + os.path.join(output_path, format_str.format(time_str)))

    def print_delays(self):
        if len(self.sampling_delays) != 0:
            print("...delays have occurred while sampling. Check the following lines on the output .csv file:")
            for i in range(len(self.sampling_delays)):
                print("(" + str(i) + ") lines: " + str(self.sampling_delays[i][0]) + " -> " + str(
                    self.sampling_delays[i][1]))
        else:
            print("...no delays were registered while sampling.")

    def set_starting_time(self):
        if self.wifi:
            self.starting_time = int(self.raw_data[0].split(",")[0][:-3])
        else:
            self.starting_time = int(self.raw_data[0].split(", ")[0][2:])


def get_current_time(raw_acquisition: str, wifi=False):
    time_string = raw_acquisition.split(",")[0]
    if wifi:
        return int(time_string[:-3])
    else:
        time_string = raw_acquisition.split(", ")[0]
        return int(time_string[2:])


def getHeaderfromSignals(acquired_signals: list):
    avail_time_series = ['time', 'acc', 'pulse', 'eda']
    series_header = []
    for series_i in acquired_signals:
        if series_i in avail_time_series and series_i != 'acc':
            series_header.append(series_i)
        elif series_i in avail_time_series and series_i == 'acc':
            series_header.append('acc_x')
            series_header.append('acc_y')
            series_header.append('acc_z')

    return series_header
