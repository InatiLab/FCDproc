#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Fri Mar 5 

@author: shervin Abdollahi

"""

def annot_niml_dset_filename(fsread_out_list):
    # this will return a list of out_file names used by FSread_annot function
    import os
    output = [os.path.basename(fsread_out_list[i])+ '.niml.dset' for i in range(len(fsread_out_list))]
    return output
    
def colormap_surface_filename(fsread_out_list):
    # this will return a list of colormap filenames used by FSread_annot function
    import os
    output = [os.path.basename(fsread_out_list[i].rsplit('.',1)[0] +'_ColorLUT.txt') for i in range(len(fsread_out_list))]
    return output

def joinpath(directory, file=None):
    import os
    
    if isinstance(file, list):
        output = [os.path.join(directory, file[i]) for i in range(len(file))]  
    elif isinstance(file, str):
        
        output = os.path.join(directory, file)
    else:
        output = directory
        
    return output

def split_file_ext(filename):
    import os
    temp1 = [os.path.splitext(i) for i in filename]
    temp2 = [os.path.splitext(j[0]) for j in temp1]
    output = [ z[0]+'.1D.dset' for z in temp2]
    return output
    

def convert_list_2_str(file):
    if isinstance(file, list):
       path =  str(file[0])
    
    return path

def flaten_list(list_files):
            
    return [j for i in list_files for j in i]        
        
def convert_filename(directory, dset):
    import os
    output_list = []
    for hemi in 'lh', 'rh':
        file = os.path.join(directory,f'{hemi}.{dset}.gii')
        output_list.append(file)

    return output_list
    
def glob_nii_feature_names(foldername):
    import re
    test1 = [ re.split('_',i)[-2] for i in foldername]
    test2 = [ re.split('/',i)[-1] for i in test1]
    test3 = [ j+'_features' for j in test2]
    return test3

def split_hemi_files(spec_file,hemi):

    if isinstance(spec_file, list):
        for i in range(len(spec_file)):
            
            if hemi in spec_file[i]:
                file = spec_file[i]
                
            elif hemi in spec_file[i]:
                file = spec_file[i]
                
    return file

def seperate_subj_features(features_list, pt_positive):
    features = []
    for i in range(len(features_list)):
        for subj in pt_positive:
            if subj in features_list[i]:
                features.append(features_list[i])
                
    return features
    
    
def flat_and_select(list_files, group):
    feature_list = [j for i in list_files for j in i]
    features = []
    for i in range(len(feature_list)):
        for subj in group:
            if subj in feature_list[i]:
                features.append(feature_list[i])
                
                
def top_dir(path):
    import os
    return os.path.dirname(path)
    
    return features     
    
    
    
    