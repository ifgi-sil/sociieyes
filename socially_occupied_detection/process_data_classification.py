# -*- coding: utf-8 -*-
"""
Created on Mon 09 Feb 2021
@author: Violeta

External data processing for classification
"""

import dataprocessing as dp
import pandas as pd
import formation as pform


def classify_orientations():
    """
    From a processed CSV, create K- means classification algorithm

    :param:
    :return:
    """

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

    # Get data from files
    relative = "data/csv/body_orientations_complete_clean.csv"

    data_orientation=dp.get_csv_data(relative)

    print(data_orientation)

    pform.spatemp_stop_kmeans(data_orientation)

    return True