import os
import sys

import pandas as pd
import numpy as np


def crop_csv_data(folder_dir: str, saving_dir: str, cropping_vals: list):

    # searching, cropping and adding acceleration data as numpy arrays to the raw_data list
    j = 0
    for filename in os.listdir(folder_dir):
        if filename.endswith(".csv"):
            print(filename)

            cropping_i = cropping_vals[j][0]
            cropping_f = cropping_vals[j][1]

            cropping_list = np.arange(cropping_i, cropping_f+1)
            print(cropping_list.tolist())
            full_dir = os.path.join(folder_dir, filename)
            df = pd.read_csv(full_dir, index_col=[0])
            df = df.drop(cropping_list.tolist(), axis=0)
            saved_name = "cropped_" + filename
            df.to_csv(os.path.join(saving_dir, saved_name), sep=",")  # saving csv file
            j += 1



folder_data_dir = os.path.join(os.path.dirname(sys.argv[0]), 'data', 'data/train', 'raw_data')
saving_data_dir = os.path.join(os.path.dirname(sys.argv[0]), 'data', 'data/train')


folder_dir_list = os.path.normpath(os.path.join(folder_data_dir, 'seizure'))
saving_dir_list = os.path.normpath(os.path.join(saving_data_dir, 'seizure'))

cropping_vals = [[5690, 9000], [3573, 9000], [4135, 9000], [6803, 9000], [8981, 9000], [6639, 9000], [6905, 9000], [0, 1365], [8981, 9000], [7695, 9000]]

crop_csv_data(folder_dir_list, saving_dir_list, cropping_vals)
