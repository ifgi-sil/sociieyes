# -*- coding: utf-8 -*-
"""
Created on Wed Jul 08 2020
@author: Violeta

Skeleton data processing for spatial reconstruction
"""

import json
import os
import pandas as pd
import datetime as dt
import math
import coordinates as coor

from os import listdir
from os.path import isfile, join


def get_file(relative_path, file, type):
    """
    Get Json file, check if exists, separate info header from main Json structure
    :param type:
    :param relative_path:
    :param file:
    :return: data processed
    """
    json_path = relative_path + file

    switcher = {
        0: lambda: get_trackingdata(f),
        1: lambda: get_json_data(f)
    }

    if os.path.exists(json_path):
        with open(json_path) as f:
            data = switcher.get(type)
            return data()
    else:
        print("Path not valid")


def get_trackingdata(f):
    """ Extract from JSON File description and actual data
    :param f: file path
    :return: processed JSON file
    """
    general = f.read().split(']', 1)

    data_tracking = {
        "description": general[0],
        "data": json.loads(general[1])['bodies_data']
    }
    return data_tracking


def get_json_data(f):
    """ Get json file
    :param f: file path
    :return: data processed
    """
    general = f.read()
    json_data = json.loads(general)

    return json_data


def get_csv_data(f):
    """ Get csv file
    :param f: File path
    :return: data processed
    """

    csv_data = pd.read_csv(f,sep=";")

    return csv_data


def set_data(json_data):
    """
    Create data structure to save Json data: description of file + measurements
    :param json_data: data extracted from the JSON File
    :return: dataframe with trajectory and bodies detected data
    """
    global merged
    exp = (json_data['description'])
    values = ((exp[1:].replace('"', "")).split(","))
    keys = ('ID_exp', 'description', 'Kheight', 'Kx', 'Ky', 'Kz', 'tilx', 'tily', 'tilz', 'rotation')

    base = {k: v for k, v in zip(keys, values)}

    data = json_data['data']

    # is_happy = list()
    # is_wearing_glasses = list()
    # is_mouth_open = list()
    # is_mouth_moved = list()
    # left_arm_length = list()
    # right_arm_length = list()
    # shoulders_length = list()
    # left_leg_length = list()
    # right_leg_length = list()
    # body_angle = list()

    x = list()
    y = list()
    height = list()
    time = list()
    joints = list()
    ids = list()
    pitch = list()
    yaw = list()
    roll = list()
    body_length = list()
    posture = list()

    for key in data:
        for value in data[key]:
            #is_happy.append(value['is_happy'])
            #is_wearing_glasses.append(value['is_wearing_glasses'])
            #is_mouth_open.append(value['is_mouth_open'])
            # is_mouth_moved.append(value['is_mouth_moved'])
            # left_arm_length.append(value['left_arm_length'])
            # right_arm_length.append(value['right_arm_length'])
            # shoulders_length.append(value['shoulders_length'])
            # left_leg_length.append(value['left_leg_length'])
            # right_leg_length.append(value['right_leg_length'])
            # body_length.append(value['body_length'])
            # body_angle.append(value['body_angle'])

            ids.append(key[7:])
            x.append(value['x'])
            y.append(value['y'])
            height.append(value['height'])
            time.append(value['time'])
            pitch.append(value['pitch'])
            yaw.append(value['yaw'])
            roll.append(value['roll'])
            posture.append(value['posture'])
            joints.append(value['joints_data'])
            body_length.append(value['body_length'])
            merged = {
                'ID_subject': ids,
                'x': y,
                'y': x,
                'height': height,
                'time': time,
                'joints': joints,
                #'is_happy': is_happy,
                #'is_wearing_glasses': is_wearing_glasses,
                #'is_mouth_open': is_mouth_open,
                #'is_mouth_moved': is_mouth_moved,
                'pitch': pitch,
                'yaw': yaw,
                'roll': roll,
                #'left_arm_length': left_arm_length,
                #'right_arm_length': right_arm_length,
                #'shoulders_length': shoulders_length,
                #'left_leg_length': left_leg_length,
                #'right_leg_length': right_leg_length,
                'body_length': body_length,
                #'body_angle': body_angle,
                'posture': posture
            }

    dtMerged = pd.DataFrame.from_dict(merged)

    count = 0

    for item in base:
        dtMerged.insert(count, item, base[item], True)
        count += 1

    # dtMerged.insert(0, 'track_id', range(0, len(dtMerged)))
    dtMerged.insert(1, 'date_exp', base['ID_exp'][-6:], True)
    dtMerged.insert(len(dtMerged.keys()), 're_body_angle', 0, True)
    dtMerged[["x", "y", "Kx", "Ky", "rotation"]] = dtMerged[
        ["x", "y", "Kx", "Ky", "rotation"]].apply(pd.to_numeric)
    dtMerged.reset_index(drop=True)

    dtMerged['date_exp'] = dtMerged.apply(format_date, axis=1)

    return dtMerged


def processing_file(file, relative_path):
    """
    Get file and set data structure,
    :param file: name with extension of the Json file
    :param relative_path: folder containing the files
    :return: data frame with data from Json file
    """
    j_data = get_file(relative_path, file, 0)
    data_json = set_data(j_data)

    return data_json


def merge_data(relative):
    """
    Merge the data from Json files in a single data frame

    :param relative: path
    :return: data frame with all Json files data from the provided directory
    """
    files = [f for f in listdir(relative) if isfile(join(relative, f))]
    complete_dataset = [processing_file(file, relative) for file in files]
    final_data = pd.concat(complete_dataset, ignore_index=True)
    return final_data


def get_control_points(relative_path, file):
    """ Process real world coordinates for the control points 
    :param relative_path: folder containing the files
    :param file: file name
    :return: dataframe with control points' real world coordinates
    """
    raw_data = get_file(relative_path, file, 1)
    control_points = pd.DataFrame.from_dict(raw_data)

    return control_points


def format_date(data):
    """ Process timestamps from the depth camera to be processed by python
    :param data: dataframe with trajectory and bodies data
    :return:
    """
    t = data['time']
    date_time = (data['date_exp'] + ' ' + t[:15])
    date_full = dt.datetime.strptime(date_time, '%d%m%y %H:%M:%S.%f')

    return date_full

def format_date_alone(data):
    """Extract only date from timestamps
    :param data: dataframe with trajectory and bodies data
    :return:
    """
    t = data['time']
    date_time = (data['date_exp'])
    date_full = dt.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S.%f')

    return date_full

def lenghtPoints(x, y):
    """
    Distance between two points in the Kinect space
    :param x: point x
    :param y: point y
    :return: distance
    """
    return math.sqrt(math.pow(x[0] - y[0], 2) + math.pow(x[1] - y[1], 2) + math.pow(x[2] - y[2], 2))


def re_body_angle(data_kinect, type):
    """Calculate real body angle towards the camera

    :param data_kinect: dataframe with trajectory and body data
    :return: dataframe with the body angle calculated per row
    """
    data_kinect['re_body_angle'] = data_kinect.apply(body_angle_calc, axis=1, result_type='expand')

    correction=analyze_face(data_kinect)

    if correction > 0.8:
        data_kinect['re_body_angle'] = data_kinect.apply(correct_orientation, axis=1, result_type='expand')

    #Calcular la diferencia del angulo calculado con el angulo predeterminado
    data_kinect['diff_re_body_angle'] = data_kinect.apply(diff_body_angle_calc,axis=1, result_type='expand',args=(type,))

    return data_kinect


def body_angle_calc(row):
    """ Calculate the body orientation from joints
    :param row: row from dataframe with trajectory and bodies data
    :return: calculated body angle
    """
    angle = 0

    if 'ShoulderLeft' in row['joints'].keys() and 'ShoulderRight' in row['joints'].keys():

        shl_o = coor.transformCoordinates(-row['joints']['ShoulderLeft'][0], row['joints']['ShoulderLeft'][2], row['Kx'],
                                          row['Ky'], row['rotation'])
        shr_o = coor.transformCoordinates(-row['joints']['ShoulderRight'][0], row['joints']['ShoulderRight'][2],
                                          row['Kx'], row['Ky'], row['rotation'])

        x_new = (shr_o[0] - shl_o[0])
        y_new = (shr_o[1] - shl_o[1])

        angle = (round((math.atan(y_new/x_new)) * (180 / math.pi),2))

        if shr_o[0] < shl_o[0]:
            angle = angle -90
        elif shr_o[0] > shl_o[0]:
            angle = angle+90

    else:
        angle=1


    return round(angle,2)


def analyze_face(data_kinect):
    """ Percentage of face detected in the trajectory
    :param data_kinect:  dataframe with trajectory and body data
    :return: percentage of face detected
    """

    total_face=data_kinect[(data_kinect.yaw ==0)].count()
    total_data= len(data_kinect)
    change_percentage =float(total_face[0])/total_data

    return round(change_percentage,4)


def correct_orientation(row):
    """ Assess the orientation value according to the detection of the face

    :param row: row from dataframe with trajectory and bodies data
    :return: corrected angle
    """
    angle= row['re_body_angle']

    #For both sideright and side left, analyze extremes less/greater than zero
    # if row['re_body_angle'] < 0 and row['origin_x'] < 0:
    #     if row['yaw'] == 0 or row['pitch'] == 0 or row['roll'] == 0:
    #         angle=angle+180

    if row['re_body_angle'] < 0 :
        if row['yaw'] == 0 or row['pitch'] == 0 or row['roll'] == 0:
            angle=angle+180

    return angle


def diff_body_angle_calc(row,type_orientation):

    """
    Calculate the absolute difference between the device angle calculations and the new method
    :param row: data for the timestamp and position
    :param type_orientation: type of orientation analyzed
    :return: difference in absolute value
    """
    choices = {'sider':0,
               'sidel': -180,

               'backdr': 45,
               'back': 90,
               'backdl': 135,

               'frontaldl': -135,
               'frontal': -90,
               'frontaldr': -45
               }

    if type_orientation!='None':
        correct_angle = choices.get(type_orientation, 0)
        diff=round(correct_angle-row['re_body_angle'],2)
        return abs(diff)
    else:
        return None


def add_shoulder(data_kinect):
    """
    Process shoulder data

    :param data_kinect: dataframe with joints data per experiment
    :return: dataframe with joint information for shoulder analysis processed
    """

    data_kinect[['shr_x','shr_y','shl_x','shl_y','sp_x','sp_y']]=data_kinect.apply(process_shoulder_segments, axis=1, result_type='expand')

    return data_kinect


def process_shoulder_segments(row):
    """
    Review if joint exists, extract the information about joints and returns the resulting data
    :param row: joint data
    :return: list of segments for shoulders to spine
    """

    segments=[]

    if 'ShoulderLeft' in row['joints'].keys() and 'ShoulderRight' in row['joints'].keys() and 'SpineShoulder' in row['joints'].keys():

        shl_o = coor.transformCoordinates(-row['joints']['ShoulderLeft'][0], row['joints']['ShoulderLeft'][2], row['Kx'],
                                          row['Ky'], row['rotation'])
        shr_o = coor.transformCoordinates(-row['joints']['ShoulderRight'][0], row['joints']['ShoulderRight'][2],
                                          row['Kx'],
                                          row['Ky'], row['rotation'])

        if 'SpineShoulder' in row['joints'].keys():
            sh_sp= coor.transformCoordinates(-row['joints']['SpineShoulder'][0], row['joints']['SpineShoulder'][2],
                                          row['Kx'],
                                          row['Ky'], row['rotation'])


        segments.append([(shr_o[0], shr_o[1]), (shl_o[0], shl_o[1])])

        return shr_o[0], shr_o[1], shl_o[0], shl_o[1],sh_sp[0],sh_sp[1]
    else:
        segments.append([(0, 0), (0,0)])
        return 0, 0, 0, 0,0,0
