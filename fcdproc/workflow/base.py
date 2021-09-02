#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Mon Jan  6 10:45:22 2021

@author: shervin Abdollahi.

"""
#############################################  Import Section #############################################

import os
import sys
from copy import deepcopy
from fcdproc import config



def create_FCD_pipeline():
    '''
    Build *FCDproc* pipeline
    
    This workflow organizes the execution of FCDPROC, with a sub-workflow for
    each subject.
    If FreeSurfer's ``recon-all`` is to be run, a corresponding folder is created
    and populated with any needed template subjects under the derivatives folder.
    '''
    import numpy as np
    import nipype.pipeline.engine as pe
    from niworkflows.interfaces.bids import BIDSFreeSurferDir
    from nipype.interfaces.io import DataFinder
    from fcdproc.utils.misc import convert_list_2_str

    from nipype.interfaces.io import SelectFiles

    #from nipype import config
    #config.enable_debug_mode()


    fcdproc_wf = pe.Workflow(name='fcdproc_wf')
    fcdproc_wf.base_dir = '/Users/abdollahis2/github/ShervinAbd92/fcdproc/' #work_dir
    fcdproc_dir = '/Users/abdollahis2/github/ShervinAbd92/fcdproc/fcdproc/derivatives/fcdproc'
    #fcdproc_dir = str(config.execution.fcdproc_dir)
    #analysis_mode = config.workflow.analysis_mode


    #freesurfer = config.workflow.run_reconall
    freesurfer = True
    if freesurfer:
        
        fsdir = pe.Node(
            BIDSFreeSurferDir(
                derivatives='/Users/abdollahis2/github/ShervinAbd92/fcdproc/fcdproc/derivatives',
                freesurfer_home=os.getenv('FREESURFER_HOME'),
                spaces= ['fsnative']),
            name='fsdir', 
            run_without_submitting=True)
        
        fsdir.inputs.subjects_dir = '/Users/abdollahis2/github/ShervinAbd92/fcdproc/fcdproc/derivatives/freesurfer'
        
        
        if config.execution.fs_subjects_dir is not None:
            fsdir.inputs.subjects_dir = str(config.execution.fs_subjects_dir.absolute())
     

    #controls = config.execution.controls
    controls =['01', '02', '03', '05', '06',  '07', '09',  '11', '12', '13',  '14',  '15', '16', '17', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32','34','35']
    #pt_positive = config.execution.patient_positive
    pt_positive = ['50', '52', '55', '57', '58', '59', '61', '62', '63', '65']
    #pt_negative = config.execution.patient_negative
    pt_negative = ['51','53','56','60','66', '67', '68', '69', '70']   
   
    subjects = controls+pt_positive+pt_negative
   
    
    anat_dir = pe.Node(DataFinder(root_paths=fcdproc_dir, max_depth=0),name='anat_dir', run_without_submitting=True)
    
    #defining analysis mode: preprocess, model, detect
    analysis_mode = 'detect'
    
    if analysis_mode == 'preprocess':
        for subject_id in subjects:
        
            single_subject_wf = init_single_subject_wf(subject_id)
            
            
            for node in single_subject_wf._get_all_nodes():
                node.config = deepcopy(single_subject_wf.config)
        
            if freesurfer:
                fcdproc_wf.connect(fsdir, 'subjects_dir', single_subject_wf, 'inputnode.subjects_dir')
            else:
                fcdproc_wf.add_nodes([single_subject_wf])
    
    
    if analysis_mode == 'model':
        
        model_exist = os.path.isdir(fcdproc_dir+'/model')
        
    
        anat_dir = pe.Node(DataFinder(root_paths=fcdproc_dir, max_depth=0),name='anat_dir', run_without_submitting=True)
    
        if not model_exist: 

            # training pca and gauss model            
            pca_gauss_modeling = init_pca_gauss_detector_model_wf(controls=controls, pt_pos=[], pt_neg=[], action='train')
        
            fcdproc_wf.connect(anat_dir, ('out_paths', convert_list_2_str), pca_gauss_modeling, 'inputnode.base_directory')
                               
        
            for node in pca_gauss_modeling._get_all_nodes():
                node.config = deepcopy(pca_gauss_modeling.config)

        
        if model_exist:
            
        
            #applying the learned model to patient data        
            pca_gauss_apply = init_pca_gauss_detector_model_wf(controls=[], pt_pos=pt_positive, pt_neg=[], action='apply')
        
            fcdproc_wf.connect(anat_dir, ('out_paths', convert_list_2_str), pca_gauss_apply, 'inputnode.base_directory')
        
            for node in pca_gauss_apply._get_all_nodes():
                node.config = deepcopy(pca_gauss_apply.config)

            
            #training for fcd_detector model   
            fcd_detector_model = init_pca_gauss_detector_model_wf(controls=controls, pt_pos=pt_positive, pt_neg=[], action='train_fcd_detector')
            
            fcdproc_wf.connect(anat_dir, ('out_paths', convert_list_2_str), fcd_detector_model, 'inputnode.base_directory')   
            
                    
            
    if analysis_mode == 'detect':
        
        anat_direcotry = anat_dir.clone(name='anatomical_dir')
        
        detector_apply = apply_fcd_detector_wf(subject=pt_negative)
            
        fcdproc_wf.connect(anat_direcotry, ('out_paths', convert_list_2_str), detector_apply, 'inputnode.base_directory')   
        
        
        
    return fcdproc_wf

def init_single_subject_wf(subject_id):
    
    """
    Organize the preprocessing pipeline for a single subject.
    
    It collects the data and prepares the sub-workflows to perform anatomical processing.
    
    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes
    
    Parameters
    ----------
    subject_id : :obj:`str`
        Subject label for this single-subject workflow.
    fcd_mask : :obj:`bool`
        fcd mask for patient postive
        
    Inputs
    ------
    subjects_dir : :obj:`str`
        FreeSurfer's ``$SUBJECTS_DIR``.
    
    """
    import os
    import nipype.pipeline.engine as pe
    from nipype.interfaces.io import DataSink, DataGrabber, SelectFiles
    import nipype.interfaces.utility as niu
    import nipype.interfaces.afni as afni 
    import nipype.interfaces.freesurfer as fs
    from niworkflows.interfaces.bids import BIDSDataGrabber, BIDSInfo
    from niworkflows.utils.bids import collect_data, collect_participants
    from fcdproc.utils.misc import glob_nii_feature_names, split_hemi_files
    from fcdproc.interfaces import FCD_preproc, FCD_python
    from fcdproc.workflow.anatomical import subject_fs_suma_wf
    from niworkflows.utils.spaces import Reference, SpatialReferences
    from fmriprep.interfaces import SubjectSummary
    from smriprep.workflows.anatomical import init_anat_preproc_wf
    from niworkflows.utils.misc import fix_multi_T1w_source_name
    from fmriprep.workflows.bold.resampling import init_bold_surf_wf
    
    name = "single_subject_%s_wf" % subject_id
    bids_dir = '/Users/abdollahis2/github/ShervinAbd92/fcdproc/fcdproc/data/'
    #bids_dir = config.excution.bids_dir
    helper_dir = os.path.join(bids_dir, '__files/')
    
    subject_data = collect_data(bids_dir, subject_id, bids_validate=True)[0]
    mask_data = os.path.isfile(bids_dir+'mask/'+subject_id+'/fcd.msk.nii')
    
    #if 'flair' in config.workflow.ignore:
    #    subject_data['flair'] = []
    
    #if 't2w' in config.workflow.ignore:
    #    subject_data['t2w'] = []
        
    spaces = SpatialReferences(['anat', 'fsnative', 'fsaverage'])
    
    workflow = pe.Workflow(name=name)
       
    fcdproc_dir = '/Users/abdollahis2/github/ShervinAbd92/fcdproc/fcdproc/derivatives/fcdproc'
    #fcdproc_dir = str(config.execution.fcdproc_dir)
    workflow.base_dir = fcdproc_dir
    
    
    inputnode = pe.Node(niu.IdentityInterface(fields=['subjects_dir']), name='inputnode')
    
    outputnode = pe.Node(niu.IdentityInterface(fields=['t1w_preproc', 'spec']), name='outputnode')

    bids_src = pe.Node(BIDSDataGrabber(anat_only=True, 
                                       subject_data=subject_data,
                                       subject_id=subject_id),
                       name="bidssrc")
    
    if mask_data:
        mask = pe.Node(SelectFiles(templates={'fcd_mask' : 'mask/{subject_id}/fcd.msk.nii'}, base_directory=bids_dir), name='fcd_mask_sel', run_without_submitting=True)
        mask.inputs.subject_id = subject_id
    
    
    bids_info = pe.Node(BIDSInfo(
        bids_dir=config.execution.bids_dir, bids_validate=False), name='bids_info')
    
    
    workflow.connect(bids_src, ('t1w', fix_multi_T1w_source_name), bids_info, 'in_file')
    
    #axialize
    axialized = pe.Node(interface=FCD_preproc.AxializeAnat(), name='axialize_T1')
    axialized.inputs.ref_file = helper_dir + 'TT_N27.nii'
    axialized.inputs.prefix = 'T1_axialize'
    axialized.inputs.outputtype = 'NIFTI'
    
    workflow.connect(bids_src, 't1w', axialized, 'in_file')    

    #Coregister t2w & flair to axialized t1 node
    allineate1 = pe.Node(interface=afni.Allineate(), name='allineate_T2')
    allineate2 = allineate1.clone(name='allineate_FL')
    allineate1.inputs.cost = 'nmi'
    allineate2.inputs.cost = 'nmi'
    allineate1.inputs.outputtype = 'NIFTI'
    allineate2.inputs.outputtype = 'NIFTI'
    allineate1.inputs.out_file = 'T2_allineate.nii'
    allineate2.inputs.out_file = 'FL_allineate.nii'
    if mask_data:
        allineate3 = allineate1.clone(name='allineate_T1_images')
        allineate3.inputs.cost = 'nmi'
        allineate3.inputs.outputtype = 'NIFTI'
        allineate3.inputs.out_file = 'orig_2_reg_t1.nii'
        allineate3.inputs.out_matrix = 'orig_2_reg.1D'
        
        workflow.connect(bids_src, 't1w', allineate3, 'in_file')
        workflow.connect(axialized, 'out_file', allineate3, 'reference')
        
        allineate4 = allineate1.clone(name='allineate_fcd_mask')
        allineate4.inputs.cost = 'nmi'
        allineate4.inputs.outputtype = 'NIFTI'
        allineate4.inputs.out_file = 'fcd_mask_al.nii'
        
        
        workflow.connect(allineate3, 'out_matrix', allineate4, 'in_matrix')
        workflow.connect(mask, 'fcd_mask', allineate4, 'in_file')
        
        
    workflow.connect(bids_src, 't2w', allineate1, 'in_file')
    workflow.connect(axialized, 'out_file', allineate1, 'reference')

    workflow.connect(bids_src, 'flair', allineate2, 'in_file')
    workflow.connect(axialized, 'out_file', allineate2, 'reference')
    
    
    
    
    #Merg dataset into a list which can be used for the feature generation
    reg_merge = pe.Node(niu.Merge(3), name='reg_merg')
      
    workflow.connect(axialized, 'out_file',  reg_merge, 'in1')
    workflow.connect(allineate1, 'out_file', reg_merge, 'in2')
    workflow.connect(allineate2, 'out_file', reg_merge, 'in3')
    
    
    #generate_featurs node
    feature = pe.MapNode(interface=FCD_preproc.GenerateFeat(), name='feature', iterfield=['in_file', 'prefix'])
    
    workflow.connect(reg_merge, 'out' , feature, 'in_file')
    workflow.connect(reg_merge, ('out', glob_nii_feature_names), feature, 'prefix')
    
    fs_suma = subject_fs_suma_wf(output_dir=fcdproc_dir, freesurfer=True, omp_nthreads=1)
    
    workflow.connect(inputnode, 'subjects_dir', fs_suma, 'inputnode.subjects_dir')
    workflow.connect(bids_info, 'subject', fs_suma, 'inputnode.subject_id')
    workflow.connect(axialized, 'out_file', fs_suma, 'inputnode.t1w')
    workflow.connect(allineate1, 'out_file', fs_suma, 'inputnode.t2w')

    if mask_data:
        mask_vol2surf_lh = pe.Node(FCD_preproc.Vol2Surf(), name='mask_vol2surf_lh')
        mask_vol2surf_rh = pe.Node(FCD_preproc.Vol2Surf(), name='mask_vol2surf_rh')
        
        workflow.connect(fs_suma, 'outputnode.surfvol_Alnd_BRIK', mask_vol2surf_lh, 'surf_vol')
        workflow.connect(allineate4, 'out_file', mask_vol2surf_lh, 'in_file')    
        workflow.connect(fs_suma, ('outputnode.spec', split_hemi_files, 'lh'), mask_vol2surf_lh, 'spec_file')    

    
        workflow.connect(fs_suma, 'outputnode.surfvol_Alnd_BRIK', mask_vol2surf_rh, 'surf_vol')
        workflow.connect(allineate4, 'out_file', mask_vol2surf_rh, 'in_file')    
        workflow.connect(fs_suma, ('outputnode.spec', split_hemi_files, 'rh'), mask_vol2surf_rh, 'spec_file') 
    
    #going from volume to surface for features data
    vol2lh_surf = pe.MapNode(FCD_preproc.Vol2Surf(), iterfield=['in_file'], name='vol2_lh_surf')
    
    workflow.connect(fs_suma, 'outputnode.surfvol_Alnd_BRIK', vol2lh_surf, 'surf_vol')
    workflow.connect(feature, 'out_file', vol2lh_surf, 'in_file')    
    workflow.connect(fs_suma, ('outputnode.spec', split_hemi_files, 'lh'), vol2lh_surf, 'spec_file')    
    
    vol2rh_surf = pe.MapNode(FCD_preproc.Vol2Surf(), iterfield=['in_file'], name='vol2_rh_surf')

    workflow.connect(fs_suma, 'outputnode.surfvol_Alnd_BRIK', vol2rh_surf, 'surf_vol')
    workflow.connect(feature, 'out_file', vol2rh_surf, 'in_file')    
    workflow.connect(fs_suma, ('outputnode.spec', split_hemi_files, 'rh'), vol2rh_surf, 'spec_file')    
    
    
    concat_feat = pe.Node(FCD_python.ConcatFeat(), name='concat_feat')
        
    workflow.connect(fs_suma, 'outputnode.lh_selctx', concat_feat, 'lh_selctx')
    workflow.connect(fs_suma, 'outputnode.rh_selctx', concat_feat, 'rh_selctx')
    workflow.connect(vol2lh_surf, 'out_file', concat_feat, 'lh_features')
    workflow.connect(vol2rh_surf, 'out_file', concat_feat, 'rh_features')
    
    scale_feat = pe.Node(FCD_python.FeatGlobalScale(), name='scale_feat')
    
    workflow.connect(fs_suma, 'outputnode.lh_selctx', scale_feat, 'lh_selctx')
    workflow.connect(fs_suma, 'outputnode.rh_selctx', scale_feat, 'rh_selctx')
    workflow.connect(concat_feat, 'lh_data', scale_feat, 'lh_features')
    workflow.connect(concat_feat, 'rh_data', scale_feat, 'rh_features')
    
    ## datasink
    datasink = pe.Node(DataSink(), name='suma_sink')
    datasink.inputs.base_directory = fcdproc_dir
    datasink.inputs.parameterization = False
    #datasink = pe.Node(DataSink(base_directory=experiment_dir,container=output_dir),name="datasink")
    #datasink.inputs.container = '.'

    #data 
    workflow.connect(fs_suma, 'outputnode.subject_id', datasink, 'container')
    workflow.connect(fs_suma,'outputnode.t1w', datasink, 'data')
    workflow.connect(fs_suma, 'outputnode.surfvol_Alnd_HEAD', datasink, 'data.@surfvol_HEAD')
    workflow.connect(fs_suma, 'outputnode.surfvol_Alnd_BRIK', datasink, 'data.@surfvol_BRIK')
    workflow.connect(fs_suma, 'outputnode.white', datasink, 'data.@white')
    workflow.connect(fs_suma, 'outputnode.sphere_reg', datasink, 'data.@sphere_reg')
    workflow.connect(fs_suma, 'outputnode.sphere', datasink, 'data.@sphere')
    workflow.connect(fs_suma, 'outputnode.pial', datasink, 'data.@pial')
    workflow.connect(fs_suma, 'outputnode.inflated', datasink, 'data.@inflated')
    workflow.connect(fs_suma, 'outputnode.inf200', datasink, 'data.@inf200')
    workflow.connect(fs_suma, 'outputnode.aparc_annot', datasink, 'data.@apartannot') 
    workflow.connect(fs_suma, 'outputnode.spec', datasink, 'data.@spec')
    workflow.connect(fs_suma, 'outputnode.smoothwm', datasink, 'data.@smoothwm')
    #workflow.connect(feature, 'out_file', datasink, 'data.@features' )
    #dset
    workflow.connect(fs_suma, 'outputnode.curv', datasink, 'data.dset')
    workflow.connect(fs_suma, 'outputnode.sulc', datasink, 'data.dset.@sulc')
    workflow.connect(fs_suma, 'outputnode.thickness', datasink, 'data.dset.@thicksm')
    workflow.connect(fs_suma, 'outputnode.wg_pct', datasink, 'data.dset.@wgsm')
    workflow.connect(fs_suma, 'outputnode.lh_selctx', datasink, 'data.dset.@lh_selctx')
    workflow.connect(fs_suma, 'outputnode.rh_selctx', datasink, 'data.dset.@rh_selctx')
    workflow.connect(vol2lh_surf, 'out_file', datasink, 'data.dset.@lh_vol2surf')
    workflow.connect(vol2rh_surf, 'out_file', datasink, 'data.dset.@rh_vol2surf')
    workflow.connect(concat_feat, 'lh_data', datasink, 'data.dset.@lh_feat')
    workflow.connect(concat_feat, 'rh_data', datasink, 'data.dset.@rh_feat')    
    workflow.connect(scale_feat, 'lh_data', datasink, 'data.dset.@lh_scale')
    workflow.connect(scale_feat, 'rh_data', datasink, 'data.dset.@rh_scale')
    
    if mask_data:
        workflow.connect(mask_vol2surf_lh, 'out_file', datasink, 'data.dset.@lh_fcd_mask')
        workflow.connect(mask_vol2surf_rh, 'out_file', datasink, 'data.dset.@rh_fcd_mask')
    
    workflow.write_graph(graph2use='orig', dotfilename=f'/Users/abdollahis2/github/ShervinAbd92/fcdproc/fcdproc_wf/single_subject_{subject_id}_wf/graph_detailed.dot')
    return workflow

def init_pca_gauss_detector_model_wf(controls, pt_pos, pt_neg, action):
    
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

    import nipype.pipeline.engine as pe
    import nipype.interfaces.utility as niu
    from fcdproc.utils.misc import flaten_list, seperate_subj_features
    from nipype.interfaces.io import SelectFiles
    import fcdproc.interfaces.FCD_python  as FCD_python 
    from fcdproc.interfaces.FCD_preproc import SurfSmooth


    subjects = controls+pt_pos+pt_neg
    pipeline = pe.Workflow(name="PCA_Gauss_modeling")

    
    inputnode = pe.Node(niu.IdentityInterface(fields=['base_directory']), name='inputnode')
    
    def top_dir(path):
        import os
        return os.path.dirname(path)
    
    
    template = {'feature': '{subject_id}/data/dset/*features.globalSTD.1D.dset', 'selctx' : '{subject_id}/data/dset/*sel_ctx.1D.dset'}
    select = pe.MapNode(SelectFiles(template, sort_filelist=True),
                    iterfield=['subject_id'], name='select_files', run_without_submitting=True)
    select.inputs.subject_id = subjects
    pipeline.connect(inputnode, 'base_directory', select, 'base_directory')

    ApplyPCA = pe.Node(FCD_python.ApplyPCA(), name='pca_apply')
    ApplyGauss = pe.Node(FCD_python.ApplyGauss(), name='gauss_apply')
    
    if action == 'train':        
           
       TrainPCA = pe.Node(FCD_python.TrainPCA(), name='pca_train')

       pipeline.connect(select, 'feature', TrainPCA, 'features')
       pipeline.connect(select, 'selctx', TrainPCA, 'selctx')            
            
       #apply PCA
       pipeline.connect(TrainPCA, 'pca', ApplyPCA, 'model')
       pipeline.connect(select, 'feature', ApplyPCA, 'features')
       pipeline.connect(select, 'selctx', ApplyPCA, 'selctx')
            
    
       TrainGauss = pe.Node(FCD_python.TrainGauss(), name='gauss_train')
            
       pipeline.connect(ApplyPCA, 'data', TrainGauss, 'features_pca')
       pipeline.connect(select, 'selctx', TrainGauss, 'selctx')
        
       #apply Gauss
       pipeline.connect(ApplyPCA, 'data', ApplyGauss, 'features_pca')
       pipeline.connect(select, 'selctx', ApplyGauss, 'selctx')
       pipeline.connect(TrainGauss, ('gauss_iter1', top_dir), ApplyGauss, 'model_dir')  
         
       
    elif action == 'apply':
        
       model_template = {'pca_model' : 'model/PCA.{dset}', 'gauss_model' : 'model/GAUSS.NITER10.features.{dset}.PCA' }
       select_model = pe.Node(SelectFiles(model_template), name='select_model')
       select_model.inputs.dset = 'globalSTD'
        
       pipeline.connect(inputnode, 'base_directory', select_model, 'base_directory')

       ApplyPCAmodel = ApplyPCA.clone(name='pca_apply_pt')
       
       pipeline.connect(select_model, 'pca_model', ApplyPCAmodel, 'model')
       pipeline.connect(select, 'feature', ApplyPCAmodel, 'features')
       pipeline.connect(select, 'selctx', ApplyPCAmodel, 'selctx')
        
       ApplyGAUSSmodel = ApplyGauss.clone(name='gauss_apply_pt')

       pipeline.connect(ApplyPCAmodel, 'data', ApplyGAUSSmodel, 'features_pca')
       pipeline.connect(select, 'selctx', ApplyGAUSSmodel, 'selctx')
       pipeline.connect(select_model, ('gauss_model', top_dir), ApplyGAUSSmodel, 'model_dir')    
       
     
    elif action == 'train_fcd_detector':
        
          
        #grab everyones features
        smooth_template = {'features': '{subject_id}/data/dset/*features.globalSTD.PCA.GAUSS.NITER10.1D.dset', 
                           'specs' : '{subject_id}/data/*_?h.spec',
                           'selctx' : '{subject_id}/data/dset/*sel_ctx.1D.dset'}
        
        select_features = pe.MapNode(SelectFiles(smooth_template, sort_files=True), iterfield=['subject_id'], name='select_features', run_without_submitting=True)
        
        select_features.inputs.subject_id = subjects
        pipeline.connect(inputnode, 'base_directory', select_features, 'base_directory')
            
            
        #smooth them
        smooth = pe.MapNode(SurfSmooth(), iterfield=['in_file','spec_file', 'b_mask'], name='feature_smooth')
        smooth.inputs.met = 'HEAT_07'
        smooth.inputs.fwhm = 10
        
        pipeline.connect(select_features, ('features',flaten_list), smooth, 'in_file')
        pipeline.connect(select_features, ('specs', flaten_list), smooth, 'spec_file')
        pipeline.connect(select_features, ('selctx', flaten_list), smooth, 'b_mask')
        
        
        mask_template = {'fcd_mask' :  '{subject_id}/data/dset/*fcd_mask_al.v2s.1D.dset'}
        select_mask = pe.MapNode(SelectFiles(mask_template, sort_files=True), iterfield=['subject_id'], name='select_mask', run_without_submitting=True)
        select_mask.inputs.subject_id = pt_pos
        pipeline.connect(inputnode, 'base_directory', select_mask, 'base_directory')   
        
        
        control_avg = pe.Node(FCD_python.control_avg(), name='control_avg')
        control_avg.inputs.control_list = controls
        
        pipeline.connect(smooth, ('out_file', seperate_subj_features, controls), control_avg, 'features')
        
        
        fcd_detector = pe.Node(FCD_python.train_FCD_detector2(), name='train_fcd')
        fcd_detector.inputs.subject_list = pt_pos
        
        pipeline.connect(smooth, ('out_file', seperate_subj_features, pt_pos), fcd_detector, 'features')
        pipeline.connect(select_mask, ('fcd_mask', flaten_list), fcd_detector, 'fcd_mask')
        pipeline.connect(control_avg, 'lh_avg', fcd_detector, 'lh_avg')
        pipeline.connect(control_avg, 'rh_avg', fcd_detector, 'rh_avg')
        
                               
    pipeline.write_graph(graph2use='orig', dotfilename=f'/Users/abdollahis2/github/ShervinAbd92/fcdproc/fcdproc_wf/PCA_GAUSS_modeling/{action}/graph_detailed.dot')

    return pipeline

def apply_fcd_detector_wf(subject):
    
    '''
    Stage applying the FCD detector model to MRI negative patients
    
    this includes:
        
        - selecting the fcd_detector model, averaged left & right hemisphere data for each node 
        - as well as selecting the MRI negative patients smoothed feature data
        -apply the fcd detector model
    
        
    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes
    
    from fcdproc.workflow import apply_fcd_detector_wf
    pca_gauss_model = apply_fcd_detector_wf(
                        subject=pt_neg,
                        base_directory = fcdproc_dir
                        )
    
    Parameters
    ----------
    subject : :obj:`list`
        Subject list for this  workflow.
    
        
    Inputs
    ------
    subjects : :obj:`list`
        list of subjects to have action on.

    base_directory: :obj:`str`
        where the data is taken
        
    outputs
    -------
    projection: :obj:`str`
        directory where normalized and unnormalized hemishpere data is stored
    
    '''

    import nipype.pipeline.engine as pe
    import nipype.interfaces.utility as niu
    from fcdproc.utils.misc import flaten_list
    from nipype.interfaces.io import SelectFiles
    import fcdproc.interfaces.FCD_python  as FCD_python 
    from fcdproc.interfaces.FCD_preproc import SurfSmooth

    pipeline2 = pe.Workflow(name="FCD_detector_Apply")

    
    inputnode = pe.Node(niu.IdentityInterface(fields=['base_directory']), name='inputnode')
    
    model_template = {'pca_model' : 'model/PCA.{dset}',
                      'gauss_model' : 'model/GAUSS.NITER1.features.{dset}.PCA',
                      'detector': 'model/fcd_detector',
                      'avg_lh': 'data/lh_avg.1D.dset', 
                      'avg_rh':'data/rh_avg.1D.dset',
                      'model_dir': 'model'}
    
    data_template = {'feature': '{subject_id}/data/dset/*features.globalSTD.1D.dset',
                    'selctx' : '{subject_id}/data/dset/*sel_ctx.1D.dset',
                    'specs' : '{subject_id}/data/*_?h.spec' }
    
    select_models = pe.Node(SelectFiles(model_template, sort_files=True), name='select_models_pt_neg', run_without_submitting=True)
    select_models.inputs.dset = 'globalSTD'
    pipeline2.connect(inputnode, 'base_directory', select_models, 'base_directory')
    
    
    select_data = pe.MapNode(SelectFiles(data_template, sort_files=True), iterfield=['subject_id'], name='select_data_pt_neg', run_without_submitting=True)
    select_data.inputs.subject_id = subject
    pipeline2.connect(inputnode, 'base_directory', select_data, 'base_directory')
    
    #apply PCA 
    ApplyPCAptNEG = pe.Node(FCD_python.ApplyPCA(), name='pca_apply_pt_neg')
    
    pipeline2.connect(select_models, 'pca_model', ApplyPCAptNEG, 'model')
    pipeline2.connect(select_data, 'feature',  ApplyPCAptNEG, 'features')
    pipeline2.connect(select_data, 'selctx', ApplyPCAptNEG, 'selctx')
    
                      
    #apply Gauss
    ApplyGaussptNEG = pe.Node(FCD_python.ApplyGauss(), name='gauss_apply_pt_neg')
    
    pipeline2.connect(select_models,'model_dir', ApplyGaussptNEG, 'model_dir')
    pipeline2.connect(select_data, 'selctx', ApplyGaussptNEG, 'selctx')
    pipeline2.connect(ApplyPCAptNEG, 'data', ApplyGaussptNEG, 'features_pca')
        
    
    #apply smooth
    smooth = pe.MapNode(SurfSmooth(), iterfield=['in_file','spec_file', 'b_mask'], name='feature_smooth_pt_neg')
    smooth.inputs.met = 'HEAT_07'
    smooth.inputs.fwhm = 10
    
    pipeline2.connect(ApplyGaussptNEG, 'gauss_n10', smooth, 'in_file')
    pipeline2.connect(select_data, ('specs', flaten_list), smooth, 'spec_file')
    pipeline2.connect(select_data, ('selctx', flaten_list), smooth, 'b_mask')
    
    
    #apply fcd detector
    apply_fcd_model = pe.Node(FCD_python.ApplyFCDdetector(), name='apply_fcd')
    apply_fcd_model.inputs.subject_list = subject
        
    pipeline2.connect(smooth, 'out_file', apply_fcd_model, 'features')
    pipeline2.connect(select_models, 'detector', apply_fcd_model, 'fcd_detector')
    pipeline2.connect(select_models, 'avg_lh', apply_fcd_model, 'lh_avg')
    pipeline2.connect(select_models, 'avg_rh', apply_fcd_model, 'rh_avg')
        
    pipeline2.write_graph(graph2use='orig', dotfilename='/Users/abdollahis2/github/ShervinAbd92/fcdproc/fcdproc_wf/FCD_detector_apply/graph_detailed.dot')
    return pipeline2
   

if __name__=='__main__':
    
    preproc_wf = create_FCD_pipeline()
    preproc_wf.run(plugin='Linear')


    
    
    
    
    
    






