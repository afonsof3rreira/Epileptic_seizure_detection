import datetime
import os
import sys

import numpy as np
import pandas as pd
import random
import json
import data_processing.python_code.utilities.fft_training as training
import data_processing.python_code.experiment_detail_writer as writer

sf = 100
ft_window_s = 1000
window_overlap = 50

# Opening JSON file
f = open('dataset.json', )
data_set = json.load(f)

f.close()

# Opening JSON file
f = open('combos.json', )
combo_set = json.load(f)
f.close()

data_dir = os.path.join(os.path.dirname(sys.argv[0]), 'data')
data_path = os.path.normpath(os.path.join(data_dir, 'train', 'preprocessed_data_w_features'))

results_dir = os.path.join(os.path.dirname(sys.argv[0]), 'data', 'results')

trainer = training.fft_training(sf=sf, window_size=ft_window_s, overlap=window_overlap)
trainer.set_acc_features(os.path.normpath(os.path.join(data_dir, 'train', 'preprocessed_data_w_features')))

t = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

os.makedirs(results_dir, exist_ok=True)
os.makedirs(os.path.join(results_dir, t), exist_ok=True)


for i in range(len(combo_set)):
    experiment_name = '-'.join([str(num[0]) for num in combo_set[i]])
    saving_dir = os.path.join(results_dir, t, experiment_name)
    os.makedirs(saving_dir, exist_ok=True)

    training_data, testing_data = trainer.select_data_partition(data_set, combo_set[i], 0.5)
    writer.experiment_writer(saving_dir, training_data, testing_data, 'info_{}'.format(experiment_name), experiment_name)

    spectral_weights = trainer.spectral_weights_extractor_v2(training_data)
    training.save_weights_to_csv_v2(spectral_weights, saving_dir, filename=experiment_name)
    tested_data = trainer.seizure_detection(10, testing_data, spectral_weights)
    training.save_detected_signals(tested_data, saving_dir)



