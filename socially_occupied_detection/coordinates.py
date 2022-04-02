# -*- coding: utf-8 -*-
"""
Created on Wed Jul 08 2020
@author: Violeta

Skeleton data processing for spatial reconstruction

Transform coordinates to real world with artificial origin
"""

import numpy as np


def getOrigin(data_kinect, kinect_id):
    """
    Get Origin coordinates (X,Y): Kinect coordinates referenced to the origin
    :param data_kinect:
    :return: tuple coordinates
    """
    origin_coordinates=data_kinect[['Kx','Ky']]
    return origin_coordinates


def getRotation(data_kinect, kinect_id):
    """
    Get rotation of the current Kinect from the origin of coordinates in grads from 0 to 360°. It can be negative
    :param data_kinect:
    :return: float orientation angle
    """
    origin_rotation=data_kinect[['rotation']]
    return origin_rotation


def calculateCoordinates(row):
    """ Calculate coordinates from depth camera coordinate system to real world coordinates
    :param row: row from data frame
    :return: set of coordinates x, y 
    """
    local_x=row['x']
    local_y=row['y']
    origin_x=row['Kx']
    origin_y=row['Ky']
    #Origin rotation angle
    tetha=np.radians(row['rotation'])

    translation_matrix=np.array([[np.cos(tetha),-np.sin(tetha),origin_x],
                        [np.sin(tetha),np.cos(tetha),origin_y],
                        [0.0,0.0,1.0]])

    vector_local=np.array([[local_x],[local_y],[1]])
    new_coordinates=translation_matrix.dot(vector_local)

    return new_coordinates[0][0], new_coordinates[1][0]


def transformCoordinates(x,y,origin_x, origin_y,rotation):
    """ Transform coordinates from joints to real world coordinates
    :param x: to transform
    :param y: to transform
    :param origin_x: correct
    :param origin_y: correct
    :param rotation: angle of rotation
    :return:
    """
    local_x=x
    local_y=y
    origin_x=origin_x
    origin_y=origin_y
    #Origin rotation angle
    tetha=np.radians(rotation)

    translation_matrix=np.array([[np.cos(tetha),-np.sin(tetha),origin_x],
                        [np.sin(tetha),np.cos(tetha),origin_y],
                        [0.0,0.0,1.0]])

    vector_local=np.array([[local_x],[local_y],[1]])
    new_coordinates=translation_matrix.dot(vector_local)

    return [new_coordinates[0][0], new_coordinates[1][0]]


def calculate_bodyrotation(row):
    """ Calculate the difference between the depth camera calculated angle vs the depth camera position
    :param row: data row from dataframe
    :return: angle difference between depth camera angle and camera position angle
    """

    angle_body_origin=row['rotation']-row['re_body_angle']

    return angle_body_origin

def getTrajectory_OriginCoordinates(data_kinect):
    """ Get real world coordinates
    :param data_kinect: dataframe with joints and trajectory
    :return: dataframe with columns for origin coordinates calculated
    """

    data_kinect[['origin_x','origin_y']]=data_kinect.apply(calculateCoordinates,axis=1, result_type='expand')
    #data_kinect['origin_bangle']=data_kinect.apply(calculate_bodyrotation,axis=1, result_type='expand')

    return data_kinect


