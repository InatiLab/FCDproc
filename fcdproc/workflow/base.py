#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Mon Jan  6 10:45:22 2021

@author: shervin Abdollahi.

"""
#############################################  Import Section #############################################

import os
from copy import deepcopy
from fcdproc.utils.colors import Colors
from warnings import simplefilter
# ignore all future warnings
simplefilter(action='ignore', category=FutureWarning)


def Main_FCD_pipeline(bids_dir, output_dir, work_dir, analysis_mode, participant_label, controls , pt_positive, pt_negative, fs_reconall, fs_license_file, fs_subjects_dir, clean_workdir):
    '''
    Build *FCDproc* pipeline
    
    This workflow organizes the execution of FCDPROC, with a sub-workflow for
    each subject.
    If FreeSurfer's ``recon-all`` is to be run, a corresponding folder is created
    and populated with any needed template subjects under the derivatives folder.
    '''

    import nipype.pipeline.engine as pe
    from niworkflows.interfaces.bids import BIDSFreeSurferDir
    from nipype.interfaces.io import DataFinder
    from fcdproc.utils.misc import convert_list_2_str
    from fcdproc.workflow.modeling import pca_gauss_detector_modeling_wf

    fcdproc_wf = pe.Workflow(name='fcdproc_wf')
    fcdproc_wf.base_dir = work_dir
    fcdproc_dir = os.path.join(output_dir+'/fcdproc/')
    if not os.path.exists(fcdproc_dir):
        os.makedirs(fcdproc_dir)

    fsdir = pe.Node(
        BIDSFreeSurferDir(
            derivatives=output_dir,
            freesurfer_home=os.getenv('FREESURFER_HOME'),
            spaces= ['fsnative']),
        name='fsdir', 
        run_without_submitting=True)        
        
    if fs_subjects_dir != "freesurfer":
        fsdir.inputs.subjects_dir = fs_subjects_dir
    
    anat_dir = pe.Node(DataFinder(root_paths=fcdproc_dir, max_depth=0),name='anat_dir', run_without_submitting=True)   
    
    if analysis_mode == 'preprocess':
        print(Colors.PURPLE, f"single processing subject {participant_label}", Colors.END)
        single_subject_wf = init_single_subject_wf(participant_label, bids_dir, output_dir, work_dir)
        fcdproc_wf.connect(fsdir, 'subjects_dir', single_subject_wf, 'inputnode.subjects_dir')

            
    if analysis_mode == 'model':
        print(Colors.PURPLE, f"performing PCA-reduction, Gaussianization and FCD-detector modeling on your dataset", Colors.END)

        model_dir = os.path.join(fcdproc_dir+'/model')
        anat_dir = pe.Node(DataFinder(root_paths=fcdproc_dir, max_depth=0),name='anat_dir', run_without_submitting=True)
        
        pca_gauss_detector = pca_gauss_detector_modeling_wf(output_dir=model_dir, controls=controls, pt_pos=pt_positive, pt_neg=pt_negative, omp_nthreads=1)
        
        fcdproc_wf.connect(anat_dir, ('out_paths', convert_list_2_str), pca_gauss_detector, 'inputnode.base_directory')

            
    if analysis_mode == 'detect':
     
        print(Colors.PURPLE, f"detecting possible FCD lesion for subject list  {pt_negative}", Colors.END)
        anat_directory = anat_dir.clone(name='anatomical_dir')
        
        detector_apply = apply_fcd_detector_wf(subject=pt_negative)
            
        fcdproc_wf.connect(anat_directory, ('out_paths', convert_list_2_str), detector_apply, 'inputnode.base_directory')   
    
    if clean_workdir:
        from niworkflows.utils.misc import clean_directory
        if clean_directory(os.path.join(work_dir+'fcdproc_wf')):
        
            print(Colors.RED, f"will remove working directory to save some space on your system", Colors.END)


    return fcdproc_wf

def init_single_subject_wf(subject_id, bids_dir, output_dir, work_dir):
    
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
    from niworkflows.utils.misc import fix_multi_T1w_source_name
    from fmriprep.workflows.bold.resampling import init_bold_surf_wf
    from warnings import simplefilter
    # ignore all future warnings
    simplefilter(action='ignore', category=FutureWarning)
    
    name = "single_subject_%s_wf" % subject_id
    
    helper_dir = os.path.join(bids_dir+ '/__files/')
    
    subject_data = collect_data(bids_dir, subject_id, bids_validate=True)[0]
    mask_data = os.path.isfile(bids_dir+'/mask/'+subject_id+'/fcd.msk.nii')
    

    spaces = SpatialReferences(['anat', 'fsnative', 'fsaverage'])
    
    workflow = pe.Workflow(name=name)
    fcdproc_dir = os.path.join(output_dir+'/fcdproc/')   
    workflow.base_dir = fcdproc_dir
    
    inputnode = pe.Node(niu.IdentityInterface(fields=['subjects_dir']), name='inputnode')
    
    bids_src = pe.Node(BIDSDataGrabber(anat_only=True, 
                                       subject_data=subject_data,
                                       subject_id=subject_id
                                       ),
                       name="bidssrc")
    
    if mask_data:
        mask = pe.Node(SelectFiles(templates={'fcd_mask' : 'mask/{subject_id}/fcd.msk.nii'}, base_directory=bids_dir), name='fcd_mask_sel', run_without_submitting=True)
        mask.inputs.subject_id = subject_id
    
    
    bids_info = pe.Node(BIDSInfo(
        bids_dir=bids_dir, bids_validate=False), name='bids_info')
    
    
    workflow.connect(bids_src, ('t1w', fix_multi_T1w_source_name), bids_info, 'in_file')
    
    #axialize
    axialized = pe.Node(interface=FCD_preproc.AxializeAnat(), name='axialize_T1')
    axialized.inputs.ref_file = os.path.join(helper_dir+'TT_N27.nii')
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
    
    fs_suma = subject_fs_suma_wf(output_dir=fcdproc_dir, input_dir=bids_dir, freesurfer=True, omp_nthreads=1)
    
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
    
    
    return workflow



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

    pipeline2 = pe.Workflow(name="FCD_detector_apply_new_sbj")

    
    inputnode = pe.Node(niu.IdentityInterface(fields=['base_directory']), name='inputnode')
    
    model_template = {'pca_model' : 'model/PCA.{dset}',
                      'detector': 'model/fcd_detector',
                      'avg_lh': 'data/lh_avg.1D.dset', 
                      'avg_rh':'data/rh_avg.1D.dset',
                      'model_dir': 'model'}
    
 
    data_template = {'feature': '{subject_id}/data/dset/*features.globalSTD.1D.dset',
                    'selctx' : '{subject_id}/data/dset/*sel_ctx.1D.dset',
                    'specs' : '{subject_id}/data/*_?h.spec',
                    'surface': '{subject_id}/data/std.60.?h.inf*.gii',
                    }
    
    select_model = pe.Node(SelectFiles(model_template, sort_files=True), name='select_models', run_without_submitting=True)
    select_model.inputs.dset = 'globalSTD'
    pipeline2.connect(inputnode, 'base_directory', select_model, 'base_directory')
    
    select_data = pe.MapNode(SelectFiles(data_template, sort_files=True), iterfield=['subject_id'], name='select_data', run_without_submitting=True)
    select_data.inputs.subject_id = subject
    pipeline2.connect(inputnode, 'base_directory', select_data, 'base_directory')
    
    #apply PCA 
    ApplyPCAptNEG = pe.Node(FCD_python.ApplyPCA(), name='pca_apply')
    
    pipeline2.connect(select_model, 'pca_model', ApplyPCAptNEG, 'model')
    pipeline2.connect(select_data, 'feature',  ApplyPCAptNEG, 'features')
    pipeline2.connect(select_data, 'selctx', ApplyPCAptNEG, 'selctx')
    
                      
    #apply Gauss
    ApplyGaussptNEG = pe.Node(FCD_python.ApplyGauss(), name='gauss_apply')
    
    pipeline2.connect(select_model,'model_dir', ApplyGaussptNEG, 'model_dir')
    pipeline2.connect(select_data, 'selctx', ApplyGaussptNEG, 'selctx')
    pipeline2.connect(ApplyPCAptNEG, 'data', ApplyGaussptNEG, 'features_pca')
        
    
    #apply smooth
    smooth = pe.MapNode(SurfSmooth(), iterfield=['in_file','spec_file', 'b_mask'], name='feature_smooth')
    smooth.inputs.met = 'HEAT_07'
    smooth.inputs.fwhm = 10
    
    pipeline2.connect(ApplyGaussptNEG, 'gauss_n10', smooth, 'in_file')
    pipeline2.connect(select_data, ('specs', flaten_list), smooth, 'spec_file')
    pipeline2.connect(select_data, ('selctx', flaten_list), smooth, 'b_mask')
    
    
    #apply fcd detector
    apply_fcd_model = pe.Node(FCD_python.ApplyFCDdetector(), name='apply_fcd')
    apply_fcd_model.inputs.subject_list = subject
        
    pipeline2.connect(smooth, 'out_file', apply_fcd_model, 'features')
    pipeline2.connect(select_model, 'detector', apply_fcd_model, 'fcd_detector')
    pipeline2.connect(select_model, 'avg_lh', apply_fcd_model, 'lh_avg')
    pipeline2.connect(select_model, 'avg_rh', apply_fcd_model, 'rh_avg')

    #generate html simialarity maps
    sim_map = pe.Node(FCD_python.generate_similarity_map(), name='similarity_map')
    sim_map.inputs.subject_list = subject
    
    pipeline2.connect(select_data, ('surface', flaten_list),sim_map, 'infl_surf')
    pipeline2.connect(apply_fcd_model, 'data', sim_map, 'proj_data') 

    return pipeline2
   




    
    
    
    
    
    






