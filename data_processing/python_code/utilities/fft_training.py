import datetime
import os
import pandas as pd
import numpy as np


class fft_training:
    def __init__(self, sf: int, window_size: float, overlap=50.0):
        """Initializes a new instance of the fft training class.

        Args:
            sf (int) sampling frequency in Hertz.
            window_size (int): the window size in milliseconds for feature extraction.
            overlap (float): the window overlap as a percentage of the window size between consecutive extractions.
        """
        self.sf = sf
        self.window_size = int((window_size * sf) / 1000)  # keeps the integer part (floor)
        assert 0 <= overlap < 100
        self.stride = int(np.ceil((100 / (100 - overlap)) * self.window_size))

        self.raw_data = {}
        self.feature_data = {}

        self.spectral_weights = None

    def set_acc_data(self, folder_dirs: list, columns=None):
        if columns is None:
            columns = ["time", "acc_x", "acc_y", "acc_z"]

        # searching, cropping and adding acceleration data as numpy arrays to the raw_data list
        for folder_dir in folder_dirs:
            sub_raw_data = []  # list containing numpy arrays of a class of time-series

            for filename in os.listdir(folder_dir):
                if filename.endswith(".csv"):

                    full_dir = os.path.join(folder_dir, filename)
                    df = pd.read_csv(full_dir, usecols=columns)

                    vm_vals, sma_vals = [], []
                    for index, row in df.iterrows():

                        mag_arr = np.array([row["acc_x"], row["acc_y"], row["acc_z"]])

                        vm_vals.append(np.linalg.norm(mag_arr))
                        sma_vals.append((abs(mag_arr[0]) + abs(mag_arr[1]) + abs(mag_arr[2])) / 3)

                    # Using DataFrame.insert() to add a column
                    df.insert(4, "VM", vm_vals, True)
                    df.insert(5, "SMA", sma_vals, True)

                    sub_raw_data.append(df.to_numpy())

            # each key is given by the folder name containing files of each type of time series
            self.raw_data.update({os.path.basename(folder_dir): sub_raw_data})
            # self.raw_data[os.path.basename(folder_dir)] = sub_raw_data

    def spectral_weights_extractor(self):

        print('Computing spectral weights...')

        fft_data = []
        found_order = []

        for data_type, data_list in self.raw_data.items():

            found_order.append(data_type)

            # If n is even, the length of the transformed axis is (n / 2) + 1.
            # If n is odd, the length is (n + 1) / 2. (fft.rfft function)
            if self.window_size % 2 == 0:
                fft_size = (self.window_size // 2) + 1
            else:
                fft_size = (self.window_size // 2) + 2

            fft_concat_tot_vm = np.zeros((1, fft_size))
            fft_concat_tot_sma = np.zeros((1, fft_size))

            for data_arr in data_list:
                fft_concat_vm = np.zeros(fft_size)
                fft_concat_sma = np.zeros(fft_size)

                sample_size = data_arr.shape[0]

                n_windows = int(np.floor((sample_size - self.window_size) / self.stride))

                # iterating through every window's initial index
                ind_initial = 0
                for i in range(n_windows):
                    # ["time", "acc_x", "acc_y", "acc_z", "VM", SMA"] = [0, 1, 2, 3, 4, 5]
                    # temp_window = data_arr[ind_initial:ind_initial + self.window_size, :]
                    # temp_feature_window = np.zeros((self.window_size, 2))

                    ft_window_vm = np.abs(
                        np.fft.rfft(data_arr[int(ind_initial):ind_initial + self.window_size, 4]))
                    ft_window_sma = np.abs(
                        np.fft.rfft(data_arr[ind_initial:ind_initial + self.window_size, 5]))

                    # summing the magnitudes along each frequency
                    fft_concat_vm = np.sum([fft_concat_vm, ft_window_vm], axis=0)
                    fft_concat_sma = np.sum([fft_concat_sma, ft_window_sma], axis=0)

                    ind_initial += self.stride

                # normalizing every frequency bin
                fft_concat_vm = np.divide(fft_concat_vm, np.sum([fft_concat_vm], axis=1))
                fft_concat_sma = np.divide(fft_concat_sma, np.sum([fft_concat_sma], axis=1))

                fft_concat_tot_vm = np.sum([fft_concat_tot_vm, fft_concat_vm])
                fft_concat_tot_sma = np.sum([fft_concat_tot_sma, fft_concat_sma])

            fft_concat_tot_vm = np.squeeze(np.divide(fft_concat_tot_vm, len(data_list)))
            fft_concat_tot_sma = np.squeeze(np.divide(fft_concat_tot_sma, len(data_list)))

            fft_data.append([fft_concat_tot_vm, fft_concat_tot_sma])

        ind_num = 0
        ind_denom = 1

        if found_order[0] == "normal" and found_order[1] == "seizure":
            ind_num = 1
            ind_denom = 0

        self.spectral_weights = np.transpose(
            np.squeeze(np.array([[np.divide(fft_data[ind_num][0], fft_data[ind_denom][0])],
                                 [np.divide(fft_data[ind_num][1], fft_data[ind_denom][1])]])))

    def save_weights_to_csv(self, output_path: str, df_header=None, filename=None):
        if df_header is None:
            df_header = ["VM weights", "SMA weights"]

        df = pd.DataFrame(self.spectral_weights)  # creating dataframe
        if filename is None:
            name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')  # string with the date of the experiment
        else:
            name = filename
        df.to_csv(os.path.join(output_path, 'spectral_weights_{}.csv'.format(name)), header=df_header,
                  sep=",")  # saving csv file
        print('Trained data saved as ' + os.path.join(output_path, 'spectral_weights_{}.csv'.format(name)))


def get_header_info(folder_dir: str, filename: str):
    return list(pd.read_csv(os.path.join(folder_dir, filename)).columns.values)
