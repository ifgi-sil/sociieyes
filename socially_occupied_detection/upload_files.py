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


import pandas as pd
import display
import dataprocessing as dp
import formation as fm



def upload_csv():
    # formation_AW_040521_1856_frontal_sides
    # formation_AW_040521_1856_inside
    # formation_AW_040521_1856_frontal
    file_name='stops_1856_3'

    relative = "data/kinect/"
    control_points = dp.get_control_points('data/control/','cpoints_may21_exp_uni_2.json')

    # Get data from files
    relative = "data/csv/"
    shared_stops = pd.read_csv(relative +file_name+".csv") 
    shared_stops.reset_index(drop=True)

    avg_subjects=(shared_stops.iloc[:,:].groupby(['shared_stop','ID_subject']).mean())
    display.display_body_direction_stops_fov(shared_stops.iloc[:,:], control_points,avg_subjects).show()

    return True
