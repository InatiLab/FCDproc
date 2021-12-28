#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 16:46:36 2021

@author: abdollahis2

"""

import os
from niworkflows.engine.workflows import LiterateWorkflow as Workflow
import nipype.pipeline.engine as pe
import nipype.interfaces.afni as afni 
from fcdproc.interfaces import FCD_preproc, FCD_python
from fcdproc.utils.misc import flaten_list, seperate_subj_features, flat_and_select, top_dir
from nipype.interfaces.io import SelectFiles
import nipype.interfaces.utility as niu



def pca_gauss_detector_modeling_wf(*, output_dir, controls, pt_pos, pt_neg, name="pca_gauss_detector", omp_nthreads):
       
    '''
    Stage performing the PCA reduction & Gaussiniaztion model
    
    this includes:
        
        - train a pca model that explains%90 of variance on on healthy volunteeers 
        - Apply pca model on the standaradize features on healthy volunteers
        - train a Gaussianization model on the pca reduced features of healthy volunteers
        - Apply the gaussianzation model the pca reduced standardized model
    
        
    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes
    
    from fcdproc.workflow.model import init_pca_gauss_model_wf
    pca_gauss_model = init_pca_gauss_model_wf(
                        subject_list=controls,
                        action='train',
                        base_directory = fcdproc_dir
                        )
    
    Parameters
    ----------
    subject_list : :obj:`list`
        Subject list for this single-subject workflow.
    action : :obj:`str`
        train the model or apply it
        
    Inputs
    ------
    subjects_list : :obj:`list`
        list of subjects to have action on.
    action: :obj:`str`
        train the model or apply the model
    base_directory: :obj:`str`
        where the data is taken
        
    outputs
    -------
    pca_model
        pca model that explain %90 of variance
    gauss_model
        gaussinization model
    
    
    '''
    subjects = controls+pt_pos+pt_neg
    pipeline = Workflow(name=name)

    
    inputnode = pe.Node(niu.IdentityInterface(fields=['base_directory']), name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=['pca_model', 'model_dir', 'fcd_detector', 'avg_lh', 'avg_rh' ]), name='outputnode')
    
    template = {'feature': '{subject_id}/data/dset/*features.globalSTD.1D.dset',
                'selctx' : '{subject_id}/data/dset/*sel_ctx.1D.dset',
                'specs' : '{subject_id}/data/*_?h.spec',
                'surface': '{subject_id}/data/std.60.?h.inf*.gii',
                }
    
    select_feat = pe.MapNode(SelectFiles(template, sort_filelist=True), iterfield=['subject_id'], name='select_features', run_without_submitting=True)
    select_feat.inputs.subject_id = subjects
    pipeline.connect(inputnode, 'base_directory', select_feat, 'base_directory')
    
    mask_template = {'fcd_mask' :  '{subject_id}/data/dset/*fcd_mask_al.v2s.1D.dset'}
    select_mask = pe.MapNode(SelectFiles(mask_template, sort_files=True), iterfield=['subject_id'], name='select_fcd_mask', run_without_submitting=True)
    select_mask.inputs.subject_id = pt_pos
    pipeline.connect(inputnode, 'base_directory', select_mask, 'base_directory')  
       
    #train PCA on controls
    TrainPCA = pe.Node(FCD_python.TrainPCA(), name='pca_train_controls') 
    TrainPCA.inputs.group = controls
    
    pipeline.connect(select_feat, 'feature', TrainPCA, 'features')
    pipeline.connect(select_feat, 'selctx' , TrainPCA, 'selctx') 
    
    #Apply PCA on controls & pt_positive & pt_negatitve
    ApplyPCA = pe.Node(FCD_python.ApplyPCA(), name='pca_apply_all')
    pipeline.connect(TrainPCA, 'pca', ApplyPCA, 'model')
    pipeline.connect(select_feat, 'feature', ApplyPCA, 'features')
    pipeline.connect(select_feat, 'selctx', ApplyPCA, 'selctx')
    
    #train Gauss on controls
    TrainGauss = pe.Node(FCD_python.TrainGauss(), name='gauss_train_controls')
    TrainGauss.inputs.group = controls
    
    pipeline.connect(ApplyPCA, 'data', TrainGauss, 'features_pca')
    pipeline.connect(select_feat, 'selctx', TrainGauss, 'selctx')
        

    #apply gauss to controls & pt_positive & pt_negatitve
    ApplyGauss = pe.Node(FCD_python.ApplyGauss(), name='gauss_apply_all')
    
    pipeline.connect(ApplyPCA, 'data', ApplyGauss, 'features_pca')
    pipeline.connect(select_feat, 'selctx', ApplyGauss, 'selctx')
    pipeline.connect(TrainGauss, 'model_dir', ApplyGauss, 'model_dir')  


    #smooth the data for controls and pt_positive
    smooth = pe.MapNode(FCD_preproc.SurfSmooth(), iterfield=['in_file','spec_file', 'b_mask'], name='feature_smooth_all')
    smooth.inputs.met = 'HEAT_07'
    smooth.inputs.fwhm = 10
    
    pipeline.connect(ApplyGauss, 'gauss_n10', smooth, 'in_file')
    pipeline.connect(select_feat, ('specs', flaten_list), smooth, 'spec_file')
    pipeline.connect(select_feat, ('selctx', flaten_list), smooth, 'b_mask')
    
    
    #getting the average control        
    control_avg = pe.Node(FCD_python.control_avg(), name='control_avg')
    control_avg.inputs.control_list = controls
        
    pipeline.connect(smooth, ('out_file', seperate_subj_features, controls), control_avg, 'features')

    #train fcd detector
    fcd_detector = pe.Node(FCD_python.train_FCD_detector2(), name='train_fcd')
    fcd_detector.inputs.subject_list = pt_pos
        
    pipeline.connect(smooth, ('out_file', seperate_subj_features, pt_pos), fcd_detector, 'features')
    pipeline.connect(select_mask, ('fcd_mask', flaten_list), fcd_detector, 'fcd_mask')
    pipeline.connect(control_avg, 'lh_avg', fcd_detector, 'lh_avg')
    pipeline.connect(control_avg, 'rh_avg', fcd_detector, 'rh_avg')
    
    #applying the detector to pt negative
    apply_fcd_model = pe.Node(FCD_python.ApplyFCDdetector(), name='apply_fcd_pt_neg')
    apply_fcd_model.inputs.subject_list = pt_neg
    
    pipeline.connect(smooth, ('out_file', seperate_subj_features, pt_neg), apply_fcd_model, 'features')
    pipeline.connect(fcd_detector, 'fcd_detector',  apply_fcd_model, 'fcd_detector')
    pipeline.connect(control_avg, 'lh_avg', apply_fcd_model, 'lh_avg')
    pipeline.connect(control_avg, 'rh_avg', apply_fcd_model, 'rh_avg')
    
    #generate html simialarity maps
    sim_map = pe.Node(FCD_python.generate_similarity_map(), name='similarity_map')
    sim_map.inputs.subject_list = pt_neg
    
    pipeline.connect(select_feat, ('surface', flaten_list), sim_map, 'infl_surf')
    pipeline.connect(apply_fcd_model, 'data', sim_map, 'proj_data') 

    #saving the result in the output node
    pipeline.connect(TrainPCA, 'pca', outputnode, 'pca_model')
    pipeline.connect(TrainGauss, 'model_dir', outputnode, 'model_dir')
    pipeline.connect(control_avg, 'lh_avg', outputnode, 'avg_lh')
    pipeline.connect(control_avg, 'rh_avg', outputnode, 'avg_rh')
    pipeline.connect(fcd_detector, 'fcd_detector', outputnode, 'fcd_detector')
    
    
    return pipeline

























