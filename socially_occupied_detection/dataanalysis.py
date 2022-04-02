# -*- coding: utf-8 -*-
"""
Created on Wed Dec 02 2020
@author: Violeta

Data analysis
"""

import pandas as pd
import math
import numpy as np
import display as dp
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import anderson
from statsmodels.graphics.gofplots import qqplot
from matplotlib import pyplot


def base_analysis(data, type):
    """ Statistical analysis of the data to conclude outliers

    :param data: dataframe with trajectory and bodies detected data
    :param type: body orientation to be analyzed to assign color code and titles
    :return:
    """
    # Back: dodgerblue
    # Back diagonal: navy
    # Frontal: seagreen
    # Frontal diagonal: lightseagreen

    choices = {'back': 'dodgerblue', 'backd': 'navy', 'frontal': 'seagreen', 'frontald': 'lightseagreen'}
    titles = {'sider': 'Side Right',
               'backdr': 'Back Diagonal Right',
               'back': 'Back',
               'backdl': 'Back Diagonal Left',
               'sidel': 'Side Left',
               'frontaldl': 'Frontal Diagonal Left',
               'frontal': 'Frontal',
               'frontaldr': 'Frontal Diagonal Right',
               'pairinter':'Pair view intersection',
               'formations': 'Group movement stops'
               }
    shade_color = choices.get(type, 'purple')
    title = titles.get(type, 'Body')

    #dp.data_visualization(data)
    clean_data=trim_outliers(data)
    #clean_data=data

    regression_analysis(clean_data)

    #dp.data_visualization(clean_data, title)

    #everything that has no place due to invalid angle/shoulders not detected
    outliers = (data['re_body_angle']!=1)

    data_outliers = data[outliers]
    data_no_outliers = data[outliers]

    clean_data.to_csv('data/csv/'+type+'_'+clean_data['ID_exp'][0]+'_1856.csv', decimal=',', sep=';', float_format='%.3f')

    #dp.angle_cloud(clean_data, shade_color, title, type=' outliers').show()
    dp.angle_cloud(clean_data, shade_color, title, type=' ').show()

    dp.error_angle_cloud(clean_data, title, type='')
    dp.error_angle_cloud(data_no_outliers, title, type=' (processed)')

    # Histogram
    #histogram(data, shade_color, title)
    
    # Exploratory Analysis
    #correlation(data)
    data['re_body_angle'].describe()
    # Normal Tests
    #normaltest(data, title)
    
    # Threating the outliers
    treat_outliers(data, title, type='')
    treat_outliers(data_no_outliers, title, type=' (processed)')

    return True


def regression_analysis(data):
    """ Statistical description of the data

    :param data: dataframe with trajectory and bodies detected data
    :return: statistics table
    """

    null_values=data.isnull().sum()

    features=['re_body_angle','diff_re_body_angle','shr_x','shr_y','shl_x','shl_y']
    print(data[features].describe())
    return True


def trim_outliers(data):
    """ Remove outliers from range

    :param data: dataframe with trajectory and bodies detected data
    :return: filtered dataframe
    """

    ArrBodyAngle_01pcntile=data.re_body_angle.quantile(0.01)
    ArrBodyAngle_90pcntile = data.re_body_angle.quantile(0.99)

    outliers = data[data.re_body_angle < ArrBodyAngle_01pcntile]
    outliers=data[data.re_body_angle > ArrBodyAngle_90pcntile]

    print('outliers')
    print((outliers.count()))

    data=data[data.re_body_angle < ArrBodyAngle_90pcntile]
    data=data[data.re_body_angle > ArrBodyAngle_01pcntile]

    return data


def correlation(data):
    """Show correlation between variables in the dataframe

    :param data: dataframe with trajectories and bodies detected
    :return: heatmap with relevant variables
    """
    c = data.corr()
    sns.heatmap(c[['origin_x','origin_y','height','re_body_angle','shr_x', 'shr_y', 'shl_x','shl_y']], cmap='BrBG', annot = True)
    plt.show()


def histogram(data, shade_color, title):
    """Show data histogram

    :param data: dataframe with trajectories and bodies detected
    :param shade_color: color code for the body orientation
    :param title: orientation
    :return: display plot
    """
    sns.set()
    sns.set_palette("CMRmap")

    fig, ax = plt.subplots()

    ax=sns.histplot(data['re_body_angle'], kde=True, bins='auto', color=shade_color)

    plt.ylabel('Frequency')
    plt.xlabel('Orientation angle')
    plt.title('Body Orientation: '+title)

    plt.show()

def normaltest(data):
    """ Run normal test for the selected data

    :param data: dataframe with trajectory and body data
    :return: display statistics
    """

    normalized_pledges=data['re_body_angle']
    #
    # # plot both together to compare
    # fig, ax = plt.subplots(1, 2)
    # sns.distplot(x['re_body_angle'], ax=ax[0])
    # ax[0].set_title("Original Data")
    # sns.distplot(normalized_pledges, ax=ax[1])
    # ax[1].set_title("Normalized data")

    k2, p = stats.normaltest(normalized_pledges )
    alpha = 0.05
    print("p = {:g}".format(p))

    print(stats.normaltest(normalized_pledges ))
    print(stats.shapiro(normalized_pledges ))

    if p <= alpha:  # null hypothesis: x comes from a normal distribution
        print("reject H0, not normal.")
    else:
        print("fail to reject H0, normal.")

    result = anderson(data['re_body_angle'])
    print('Statistic: %.3f' % result.statistic)

    for i in range(len(result.critical_values)):
        sl, cv = result.significance_level[i], result.critical_values[i]
        if result.statistic < result.critical_values[i]:
            print('%.3f: %.3f, data looks normal (fail to reject H0)' % (sl, cv))
        else:
            print('%.3f: %.3f, data does not look normal (reject H0)' % (sl, cv))


def treat_outliers(data_kinect, title, type):
    """ Verify which points in the trajectory are outliers

    :param x: dataframe with trajectories and body data
    :param title: plot title
    :param type: type of orientation
    :return: display outliers in a plot and the data related to them
    """

    from numpy import percentile
    data=data_kinect['re_body_angle']
    q25, q75 = percentile(data, 25), percentile(data, 75)
    iqr = q75 - q25
    print('Percentiles: 25th=%.3f, 75th=%.3f, IQR=%.3f' % (q25, q75, iqr))
    # calculate the outlier cutoff
    cut_off = iqr * 1.5
    lower, upper = q25 - cut_off, q75 + cut_off
    # identify outliers
    outliers = [x for x in data if x < lower or x > upper]
    print('Identified outliers: %d' % len(outliers))
    # remove outliers
    outliers_removed = [x for x in data if x >= lower and x <= upper]
    print('Non-outlier observations: %d' % len(outliers_removed))

    filter=data_kinect['re_body_angle']

    count = data_kinect.groupby('re_body_angle').count()
    print(count)
    print('mean=%.3f stdv=%.3f' % (np.mean(filter), np.std(filter)))

    # normalized_pledges = stats.boxcox(data_kinect['re_body_angle'])[0]

    qqplot(filter, line='s', color='mediumseagreen',  markerfacecolor='mediumseagreen')
    plt.title('QQ-Plot '+type+' '+ title)
    pyplot.show()

