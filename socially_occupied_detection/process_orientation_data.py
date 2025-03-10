# MIT License
#
# Copyright (c) 2020-2024 Violeta Ana Luz Sosa León
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# -*- coding: utf-8 -*-
"""
Created on Fri Jul 03 2020
@author: Violeta

Skeleton data processing for spatial reconstruction
"""

import display as d
import dataprocessing as dp
import coordinates as coor
import formation as fm
import pandas as pd
import dataanalysis as da


def process_data_orientation(type):
    desired_width = 640
    pd.set_option('display.width', desired_width)
    pd.set_option('display.max_columns', None)


    # Get data from files
    relative = "data/kinect/"
    data_controlpoints = dp.get_control_points('data/control/','cpoints_may21_exp_uni_2.json')

    # Process JSON and create data structures
    data_kinect = dp.merge_data(relative)

    # Unique coordinate from origin
    coor.getTrajectory_OriginCoordinates(data_kinect)

    # Recalculate body angle
    dp.re_body_angle(data_kinect, type)

    # Data Analysis
    dp.add_shoulder(data_kinect)
    
    # Remove samples with no complete shoulder orientations
    data_kinect = data_kinect[(data_kinect['re_body_angle'] != 1)]

    # Detecting Formations
    #d.display_body_shoulder(data_kinect).show()
    #fm.eval_formation(data_kinect, data_controlpoints, stop_time=1.0, stop_distance=0.10)
    #d.test_ani()

    #Save the data
    #data_kinect.to_csv('data/csv/'+type+'_preanalysis_meeting_with.csv', decimal=',', sep=';', float_format='%.3f')
    da.base_analysis(data_kinect,type)



    display = False
    if display:
        #d.display_2d_global(data_kinect).show()
        #d.display_2d_origin_global(data_kinect, data_controlpoints,'ID_exp').show()
        d.display_2d_origin_global(data_kinect, data_controlpoints,'ID_subject').show()
        #d.display_body_direction(data_kinect, data_controlpoints).show()
        #d.display_aniTrajectory_simple(data_kinect,data_controlpoints).show()
        #d.display_control_points(data_controlpoints)
    pass

