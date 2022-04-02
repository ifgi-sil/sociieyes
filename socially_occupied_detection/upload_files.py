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
