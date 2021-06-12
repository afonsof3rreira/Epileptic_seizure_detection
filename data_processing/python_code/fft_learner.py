# -*- coding: utf-8 -*-
import argparse
import os
import sys
import data_processing.python_code.utilities.fft_training as training
import pandas as pd
import json


def main(preprocessed_data_dir: str, feature_data_dir: str, save_features: bool, saving_weights_dir=None, sf=100,
         ft_window_s=1000, window_overlap=50):
    """Computes spectral weights from previously labelled acquisitions: baseline vs epileptic seizure"""

    """Initialising variables"""
    trainer = training.fft_training(sf=sf, window_size=ft_window_s, overlap=window_overlap)

    """Receiving data and storing it in a list"""

    # trainer.set_acc_data(preprocessed_data_dir, save_features_dir)
    if save_features:
        trainer.set_and_save_acc_features(preprocessed_data_dir, feature_data_dir)
    else:
        trainer.set_acc_features(feature_data_dir)

    # Opening JSON file
    f = open('dataset.json', )

    # returns JSON object as a dictionary
    data_set = json.load(f)

    # Iterating through the json
    # list
    for i in data_set['emp_details']:
        print(i)

    # Closing file
    f.close()

    trainer.spectral_weights_extractor()

    if saving_weights_dir is not None:
        trainer.save_weights_to_csv(saving_weights_dir)


if __name__ == "__main__":
    """The program's entry point."""

    data_dir = os.path.join(os.path.dirname(sys.argv[0]), 'data')

    parser = argparse.ArgumentParser(description='Arduino-based acquisition of acceleration, pulse and EDA signals')

    parser.add_argument(
        '--preprocessed_data_dir',
        type=str,
        default=os.path.normpath(os.path.join(data_dir, 'train', 'preprocessed_data')),
        help='Directory from which to get the preprocessed training data'
    )

    parser.add_argument(
        '--feature_data_dir',
        type=str,
        default=os.path.normpath(os.path.join(data_dir, 'train', 'preprocessed_data_w_features')),
        help='Directory to store preprocessed data including acceleration features'
    )

    parser.add_argument(
        '--save_features',
        type=bool,
        default=False,
        help='Set to True to save data in a .csv file.'
    )

    parser.add_argument(
        '--saving_weights_dir',
        type=str,
        default=os.path.normpath(os.path.join(data_dir, 'trained weights')),
        help='Set to True to save data in a .csv file.'
    )
    args = parser.parse_args()
    main(args.preprocessed_data_dir, args.feature_data_dir, args.save_features, args.saving_weights_dir)
