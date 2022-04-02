# -*- coding: utf-8 -*-
"""
Created on Sun Sep 20 2020
@author: Violeta

Skeleton data processing for spatial reconstruction

Formation functions for:
    - Identify gatherings: long and close interactions

"""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
from sklearn.cluster import KMeans
import display
import pandas as pd
import dataprocessing as dp


def eval_formation(data_kinect, control_points, stop_time, stop_distance):
    """
    Evaluate if the people in the trajectory data are creating F-Formations

    :param data_kinect: dataframe with data
    :param control_points: points with real world coordinates in which people stopped
    :param stop_time: in seconds to review in the stop
    :param stop_distance: in meters to review in the stop
    :return: True
    """

    column_values = data_kinect[["ID_subject"]].values
    unique_values = np.unique(column_values)
    location_stops=pd.DataFrame()

    for subject in unique_values:
        individual = data_kinect[data_kinect['ID_subject'] == subject]
        location_stops = location_stops.append(spatemp_stop(individual, stop_time, stop_distance), ignore_index=True)

    if(len(location_stops)==0):
        detected_formations = 0
        print("No stops detected")
    else:
        shared_stops = intersection_stops(location_stops, stop_time, stop_distance)
        #display.display_body_direction_stops_all(data_kinect, shared_stops, control_points).show()
        bodies_oriented = intersection_orientation(shared_stops, control_points)
        
    return True


def diff_seconds(start, end):
    """Calculate the difference in seconds between two timestamps
    :param start: timestamp
    :param end: timestamp
    :return: diference in seconds 
    """
    diff = (end - start)
    total_secs=diff.seconds
    return total_secs


def spatemp_stop(data_kinect, wait_time, distance):
    """
    Identify a stop in the track:
    Conditions: same location and for a time longer than wait_time seconds
    :param data_kinect: dataframe with trajectory and body data
    :param wait_time: limit in seconds for considering a stop
    :param distance: limit in meters for considering a stop
    :return: numbered stops detected per timestamp
    """
    # Define the distance function to use
    data_kinect=data_kinect.sort_values(by=['date_exp'], ascending=[True],ignore_index=True)
    stop_radius=distance
    seconds_for_a_stop=wait_time
    stops = []

    x_0 = data_kinect.iloc[0]['shl_x']
    y_0 = data_kinect.iloc[0]['shl_y']
    t_0 = data_kinect.iloc[0]['date_exp']
    data_sample_0= data_kinect.iloc[0]

    for i in range(data_kinect.shape[0]-1):

        x =  data_kinect.iloc[i+1]['shl_x']
        y =  data_kinect.iloc[i]['shl_y']
        t= data_kinect.iloc[i+1]['date_exp']
        data_sample=data_kinect.iloc[i+1]

        Dt = diff_seconds(t_0, t)
        Dr = spatial_distance([x_0, y_0], [x, y])

        if Dr < stop_radius:
            if Dt > seconds_for_a_stop:
                series=pd.Series([x_0,y_0,t_0], index=['x_stop','y_stop','t_stop'])
                init=data_sample_0.append(series)
                stops += [init]

                x_0=x
                y_0= y
                t_0 = t
                data_sample_0=data_sample
        else:
            # Not a stop
            x_0=x
            y_0= y
            t_0 = t
            data_sample_0 = data_sample

    stops_df=pd.DataFrame(stops)
    #display.display_2d_origin_global(data_kinect, stops_df).show()

    return stops_df


def intersection_stops(location_stops):
    """
    Label shared stops from the individual stops detected

    :param location_stops: detected stops
    :return: numbered stops detected per group
    """
    location_stops=location_stops.sort_values(by=['date_exp'], ascending=[True], ignore_index=True)

    #check last item
    #print(location_stops)
    shared_stops = []

    x_0 = location_stops.iloc[0]['x_stop']
    y_0 = location_stops.iloc[0]['y_stop']
    t_0 = location_stops.iloc[0]['t_stop']
    data_sample_0 = location_stops.iloc[0]

    label=0

    for i in range(0,location_stops.shape[0]-1):

        x = location_stops.iloc[i + 1]['x_stop']
        y = location_stops.iloc[i + 1]['y_stop']
        t = location_stops.iloc[i + 1]['t_stop']
        data_sample = location_stops.iloc[i + 1]
        Dt = diff_seconds(t_0, t)
        Dr = spatial_distance([x_0, y_0], [x, y])

        if Dr < 1.2:
            if Dt <= 2:
                series = pd.Series(label, index=['shared_stop'])
                init = data_sample_0.append(series)
                shared_stops += [init]

                x_0 = x
                y_0 = y
                t_0 = t
                data_sample_0 = data_sample
            else:
                
                series = pd.Series(label, index=['shared_stop'])
                init = data_sample_0.append(series)
                shared_stops += [init]
                label += 1
                x_0 = x
                y_0 = y
                t_0 = t
                data_sample_0 = data_sample
        else:
            # Not a shared stop
            
            series = pd.Series(label, index=['shared_stop'])
            init = data_sample_0.append(series)
            shared_stops += [init]

            x_0 = x
            y_0 = y
            t_0 = t
            label += 1
            data_sample_0 = data_sample

        print(str(label)+"=distance " + str(Dr) + " - secs " + str(Dt))

    shared_stops_df = pd.DataFrame(shared_stops)
    #display.display_2d_origin_global(location_stops, shared_stops_df).show()
    return shared_stops_df


def spatial_distance(pA, pB):
    """ Calculate the distance between two given points
    :param pA: point A coordinates 
    :param pB: point B coordinates
    :return: distance between point A and b
    """
    sq_dist = np.power(pB[0] - pA[0],2)  + np.power(pB[1] - pA[1],2)
    return np.sqrt(sq_dist)


def intersection_orientation(shared_stops, control_points):
    """Filtering group stop by selecting a unique stop
    :param shared_stops: labeled stops by group
    :param control_points: fixed stop points from the experiment 

    """
    data_stop=shared_stops.iloc[:,:]
    avg_subjects=(data_stop.groupby(['shared_stop','ID_subject']).median())
   
    display.display_body_direction_stops_fov(data_stop, control_points,avg_subjects).show()

    return True


def spatemp_stop_kmeans(data_kinect):
    """
    Identify a stop in the track:
    Conditions: same location and for a time longer than 3 seconds
    :return: Point of coordinates with stop
    """
    K_clusters = range(1,11)
    kmeans = [KMeans(n_clusters=i,init='random',
        n_init=10, max_iter=300,
        tol=1e-04, random_state=0) for i in K_clusters]
    print(kmeans)
    Y_axis = data_kinect[['re_body_angle']]
    score = [kmeans[i].fit(Y_axis).score(Y_axis) for i in range(len(kmeans))]

    # Visualize
    plt.plot(K_clusters, score,marker='o')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Score')
    plt.title('Elbow Curve')
    plt.show()

    kmeans = KMeans(n_clusters=8, init='k-means++')
    kmeans.fit(data_kinect[['re_body_angle']])  # Compute k-means clustering.
    data_kinect['cluster_label'] = kmeans.fit_predict(data_kinect[['re_body_angle']])
    centers = kmeans.cluster_centers_  # Coordinates of cluster centers.
    labels = kmeans.fit_predict(data_kinect[['re_body_angle']])  # Labels of each point when we fit the Kmeans
    data_kinect.to_csv('data/csv/classification_complete_clean_sides_89.csv', decimal=',', sep=';')

    sns.set()
    sns.lmplot(x="origin_x", y="origin_y", data=data_kinect, fit_reg=False, hue='cluster_label', legend=False)
    plt.ylabel('(Y) Distance from Origin')
    plt.xlabel('(X) Distance from Origin')
    plt.scatter(centers[:, 1], centers[:, 2], c='black', s=200, alpha=0.5)
    plt.title('Kinect Trajectory: ' )
    plt.legend(loc='lower left')

    # data_kinect.plot.scatter(x='origin_x', y='origin_y', c=labels,  cmap='viridis')
    plt.scatter(centers[:, 1], centers[:, 2], c='black', s=200, alpha=0.5)

    plt.show()

    return True