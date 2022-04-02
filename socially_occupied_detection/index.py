# -*- coding: utf-8 -*-
"""
Created on Mon 09 Feb 2021
@author: Violeta

Skeleton data processing for spatial reconstruction
"""

import process_orientation_data as pod
import process_data_classification as dc
import upload_files as upf



if __name__ == "__main__":
    
    pod.process_data_orientation(type='frontaldl')
    
    #dc.classify_orientations()

    #upf.upload_csv()


