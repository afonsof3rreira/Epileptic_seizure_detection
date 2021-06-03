# -*- coding: utf-8 -*-
import argparse
import os
import sys
import data_processing.python_code.utilities.fft_training as training
import pandas as pd


def main(save_data: bool, data_dir: list, save_dir: str, sf=100, ft_window_s=1, window_overlap=50):
    """Computes spectral weights from previously labelled acquisitions: baseline vs epileptic seizure"""

    """Initialising variables"""
    trainer = training.fft_training(sf, window_size=(ft_window_s * 1000), overlap=window_overlap)

    """Receiving data and storing it in a list"""
    trainer.set_acc_data(data_dir)

    trainer.spectral_weights_extractor()

    if save_data:
        trainer.save_weights_to_csv(save_dir)


if __name__ == "__main__":
    """The program's entry point."""

    data_dir = os.path.join(os.path.dirname(sys.argv[0]), 'data')

    parser = argparse.ArgumentParser(description='Arduino-based acquisition of acceleration, pulse and EDA signals')

    parser.add_argument(
        '--save_data',
        type=bool,
        default=True,
        help='Set to True to save data in a .csv file.'
    )

    parser.add_argument(
        '--training_data_dir',
        type=list,
        default=[os.path.normpath(os.path.join(data_dir, 'train', 'normal')),
                 os.path.normpath(os.path.join(data_dir, 'train', 'seizure'))],
        help='Directory from which to get training data'
    )

    parser.add_argument(
        '--save_dir',
        type=str,
        default=os.path.normpath(os.path.join(data_dir, 'trained weights')),
        help='Directory to store trained spectral weights'
    )

    args = parser.parse_args()
    main(args.save_data, args.training_data_dir, args.save_dir)
