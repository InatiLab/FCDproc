#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 10:20:44 2021

@author: abdollahis2
"""

################################################## Import Section #############################################

import os
from nipype.interfaces.io import SelectFiles
import nipype.interfaces.utility as niu
from niworkflows.engine.workflows import LiterateWorkflow as Workflow
import nipype.pipeline.engine as pe
import nipype.interfaces.afni as afni 
from nipype.interfaces.afni.utils import ConvertDset
from nipype.interfaces.freesurfer import ReconAll, SurfaceTransform, MRIsConvert
from fcdproc.interfaces import FCD_preproc, FCD_python
from fcdproc.utils.misc import  annot_niml_dset_filename, colormap_surface_filename, joinpath, split_file_ext, convert_filename



def subject_fs_suma_wf(*, output_dir, input_dir, name="fs_suma", freesurfer, omp_nthreads):
    """
    Stage the freesurfer and SUMA preprocessing of anatomical dataset
    
    this includes:
        
        - Surface reconstruction with FreeSurfer
        - preparing for surface viewing in SUMA 
        - make cortex selector
        - resamples one CorticalSurface onto another (fsaverage)
        - interpolating data from one surface (S2) to another (S1)
        - smoothing and converting thickness and white-gray boundary surface
        - aligning freesurface surface volume to experimental t1 
        
        
        Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes
            
    from fcdproc.workflow.anatomical import subject_fs_suma_wf
    fs_suma_wf =  subject_fs_suma_wf(
                freesurfer=True,
                omp_nthreads=1,
                output_dir = fcdproc_dir,
                )    
            
    Parameters
    ----------
    output_dir : TYPE, optional
        Directory in which to save resullts. The default is fcdproc_dir.
    input_dir : TYPE, optional
        Directory to grab the input data. The default is bids_dir.
    name : TYPE, optional
        pipeline name. The default is "fs_suma".
    freesurfer : :obj:`bool`
        Enable FreeSurfer surface reconstruction (increases runtime by 6h,at the very least)
    omp_nthreads : :obj:`int`
         Maximum number of threads an individual process may use


    Inputs
    -------
    t1w 
        axialized t1
    t2w
        aligned t2 
    subject_dir
        freesurfer SUBJECT_DIR
    subject_id
        Freesurfer SUBJECT_ID
    
    outputs
    -------
    subject_dir
        freesurfer SUBJECT_DIR
    subject_id
        Freesurfer SUBJECT_ID
    surfvol_Alnd
        surface volume aligned to axialized experimental t1
    spec_files
        SUMA spec files for {left hemisphere, right hemisphere, both hemisphere}
    surfaces
        GIFTI surfaces (gray/white boundary{smooth}, thickness{smooth}, pial, inflated, inf_200, sphere, sphere.reg)
    aparc_annot_niml
        surface dset from aparc.a2009s template
    1D_dset
        sel_ctx, curve, sulc, smoothed thickness and wg boundary 1D dset
        
    """
    import os
    helper_dir = os.path.join(input_dir, '__files/')
    
    pipeline = Workflow(name=name)
     
    inputnode = pe.Node(niu.IdentityInterface(fields=["t1w", "t2w", "subjects_dir", "subject_id"]),name="inputnode")

    
    reconall = pe.Node(interface=ReconAll(),name="reconall")
    #reconall.inputs.subjects_dir = freesurfer_dir
    reconall.inputs.use_T2 = True
    reconall.inputs.directive = 'all'

    #join fs path
    joinpath1 = pe.Node(niu.Function(input_names=['directory', 'file'], output_names=['output'],function=joinpath), name='fs_sub_path')
    joinpath2 = joinpath1.clone(name='fs_label_dir')
    joinpath2.inputs.file = 'label'
    joinpath3 = joinpath1.clone(name='fsread_out')
    joinpath4 = joinpath1.clone(name='fsread_cmap')
    joinpath4.inputs.directory = helper_dir

    #run SUMA maske spec
    suma = pe.Node(interface=FCD_preproc.SumaMakeSpecFS(), name='Suma')

    #resampling cortical surface (this doesnt need to have the out_file inputed, by default it creates a filename:{lh/rh}.lausanne_250.02.annot)- MODIFY LATER
    mri_surf2surf = pe.MapNode(interface=SurfaceTransform(), iterfield=['source_annot_file','hemi', 'out_file'], name='mri_s2s')
    mri_surf2surf.inputs.hemi = ['lh', 'rh'] 
    mri_surf2surf.inputs.source_annot_file = [os.path.join(helper_dir+'lh.lausanne_250.annot'), os.path.join(helper_dir+'rh.lausanne_250.annot')]
    mri_surf2surf.inputs.source_subject = 'fsaverage'
    joinpath5 = joinpath1.clone(name='mri_surf2surf_dset')
    joinpath5.inputs.file = [os.path.basename(i) for i in mri_surf2surf.inputs.source_annot_file]
    
    #FSread_annot
    fsread = pe.MapNode(interface=FCD_preproc.FSread(), iterfield=['in_file', 'out_file', 'cmap', 'hemi'], name='fs_read')
    fsread.inputs.hemi = ['lh', 'rh']
    
    #rename spec files
    rename_spec = pe.MapNode(niu.Rename(format_string='std.60.%(hemi)s'), iterfield=['in_file','hemi'], name='renameSpec')
    rename_spec.inputs.hemi = ['both', 'lh', 'rh']
    rename_spec.inputs.keep_ext = True
    rename_spec.inputs.use_fullpath = True
    
    #surfTosurf node
    surf2surf = pe.MapNode(interface=FCD_preproc.Surf2Surf(), iterfield=['surf_A','surf_B','mapfile','dset'], name = 'surf2surf')
    surf2surf.inputs.output_params = 'NearestNode'
    joinpath6 = joinpath1.clone(name='surf2surf_prefix')
    joinpath6.inputs.file = 'std.60'
    
    #convertDset node
    convertDset = pe.MapNode(interface=ConvertDset(), iterfield=['in_file', 'out_file'], name='convertDset')
    convertDset.inputs.out_type = '1D'
    
    #select-cortex node
    sel_ctx = pe.Node(interface=FCD_python.SelectCortex(), name='sel_ctx')
    sel_ctx.inputs.out_prefix = 'sel_ctx'
    
    #select surf files
    surf_template = dict(thickness = "{subject_id}/surf/??.thickness",
                         wg_pct = "{subject_id}/surf/??.w-g.pct.mgh",
                         white = "{subject_id}/surf/??.white")
    
    
    surf_sf = pe.Node(interface=SelectFiles(surf_template, force_lists=True), name='surf_select')
    
    #thickness_smoothing
    thickness_smooth = pe.MapNode(interface=FCD_preproc.SurfaceSmooth(), iterfield=['hemi', 'in_file'], name='thinckness_fwhm')
    thickness_smooth.inputs.hemi = ['lh', 'rh']
    thickness_smooth.inputs.surface = 'thickness'
    
    #w-g.pct smoothing
    wg_pct_smooth = pe.MapNode(interface=FCD_preproc.SurfaceSmooth(), iterfield=['hemi', 'in_file'], name='wg_pct_fwhm')
    wg_pct_smooth.inputs.hemi = ['lh', 'rh']
    wg_pct_smooth.inputs.surface = 'w-g.pct'
    
    #mris_convert for (thickness.fwhm5, w-g.pct, w-g.pct.fwhm5)
    wg_convert = pe.MapNode(interface=MRIsConvert(), iterfield=['in_file', 'functional_file', 'out_file'], name='wg_convert')
    thick_convert = wg_convert.clone(name='thick_fwhm_convert')
    wg_sm_convert = wg_convert.clone(name='wg_fwhm_convert')
    
    #defining the output prefix for mris_convert function
    convert_prefix = pe.Node(niu.Function(input_names=['directory', 'dset'], output_names=['output'], function=convert_filename), name='wg_conv_pre')
    convert_prefix.inputs.dset = 'w-g.pct'
    
    thicksmooth_conv_pre = convert_prefix.clone(name='sm_thick_conv_pre')
    thicksmooth_conv_pre.inputs.dset = 'thickness.fwhm5'
    
    wgsmooth_conv_pre = convert_prefix.clone(name='sm_wg_conv_pre')
    wgsmooth_conv_pre.inputs.dset = 'w-g.pct.fwhm5'
    
    cp_wg_dset = pe.MapNode(interface=FCD_preproc.CopyFiles(), iterfield=['in_file'], name='cp_wg_dset')
    cp_wgsm_dset = cp_wg_dset.clone(name='cp_wgsm_dset')
    cp_thicksm_dset = cp_wg_dset.clone(name='cp_thicksm_dset')
    
    #SurftoSurf for smoothed dset
    surf2surf_wg_dset = surf2surf.clone(name='s2s_wg')
    surf2surf_wg_sm_dset = surf2surf.clone(name='s2s_wg_sm')
    surf2surf_thick_dset = surf2surf.clone(name='s2s_thick_sm')
    
    
    #convertDset smoothed surface
    convertDset_dset_curve = convertDset.clone(name='convert_curv_dset')
    convertDset_dset_curve.inputs.out_type = '1D'
    
    convertDset_dset_sulc = convertDset.clone(name='convert_sulc_dset')
    convertDset_dset_sulc.inputs.out_type = '1D'
    
    convertDset_dset_thick = convertDset.clone(name='convert_thick_dset')
    convertDset_dset_thick.inputs.out_type = '1D'
    
    convertDset_dset_wg = convertDset.clone(name='convert_wg_dset')
    convertDset_dset_wg.inputs.out_type = '1D'
    
    convertDset_dset_wgsm = convertDset.clone(name='convert_wgsm_dset')
    convertDset_dset_wgsm.inputs.out_type = '1D'
    
    convertDset_dset_thicksm = convertDset.clone(name='convert_thicksm_dset')
    convertDset_dset_thicksm.inputs.out_type = '1D'
    
    copy_t1 = pe.Node(interface=afni.Copy(), name='t1_copy')
    copy_t1.inputs.outputtype = 'AFNI'
    copy_t1.inputs.out_file = 't1'
    
   
    Align2Exp = pe.Node(interface=FCD_preproc.SUMA_align2Exp(), name='align2Exp')
    Align2Exp.inputs.outputtype = 'AFNI'
    Align2Exp.inputs.prefix = 'SurfVol_Alnd'  

                
        
    outputnode = pe.Node(niu.IdentityInterface(fields=["subjects_dir", "subject_id","t1w", "surfvol", "curv", "sulc", "thickness", "wg_pct", "aparc_annot",
                                                       "spec", "white", "smoothwm", "inf200", "inflated", "pial", "sphere", "sphere_reg","lh_selctx", "rh_selctx", 'surfvol_Alnd_HEAD', 'surfvol_Alnd_BRIK', 'subj_SUMA_dir']), name="outputnode")
    
    
    pipeline.connect(inputnode, 'subject_id', reconall, 'subject_id')
    pipeline.connect(inputnode, 'subjects_dir', reconall, 'subjects_dir')
    pipeline.connect(inputnode, 't1w', reconall, 'T1_files')
    pipeline.connect(inputnode, 't2w', reconall, 'T2_file')
    
    pipeline.connect(reconall, 'subject_id', joinpath1, 'file')
    pipeline.connect(reconall, 'subjects_dir', joinpath1, 'directory')
    #SUMA
    pipeline.connect(reconall, 'subject_id', suma, 'subject_id')
    pipeline.connect(joinpath1, 'output', suma, 'in_file')
    
    #mri_surf2surf
    pipeline.connect(reconall, 'subject_id', mri_surf2surf, 'target_subject') 
    pipeline.connect(reconall, 'subjects_dir', mri_surf2surf, 'subjects_dir')
    pipeline.connect(joinpath1, 'output', joinpath2, 'directory')
    pipeline.connect(joinpath2, 'output', joinpath5, 'directory')
    pipeline.connect(joinpath5, 'output', mri_surf2surf, 'out_file')

    #fsread_annot 
    pipeline.connect(mri_surf2surf, 'out_file', fsread, 'in_file')
    pipeline.connect(mri_surf2surf, ('out_file', annot_niml_dset_filename), joinpath3, 'file' )
    pipeline.connect(suma, 'SUMAfolder', joinpath3, 'directory')
    pipeline.connect(joinpath3, 'output', fsread, 'out_file')
    pipeline.connect(mri_surf2surf, ('out_file', colormap_surface_filename), joinpath4, 'file' )
    pipeline.connect(joinpath4, 'output', fsread, 'cmap')
    
    #suma_select
    #pipeline.connect(reconall, 'subject_id', suma_sf, 'subject_id')
    
    pipeline.connect(suma, 'spec', rename_spec, 'in_file')
    
    #surf2surf
    pipeline.connect(suma, 'surf_A', surf2surf, 'surf_A')
    pipeline.connect(suma, 'surf_B', surf2surf, 'surf_B')
    pipeline.connect(suma, 'my_map', surf2surf,'mapfile' )
    pipeline.connect(suma, 'SUMAfolder', joinpath6, 'directory')
    pipeline.connect(joinpath6, 'output', surf2surf, 'prefix')
    pipeline.connect(fsread, 'out_file', surf2surf, 'dset')
    
    
    #converDset
    pipeline.connect(surf2surf, 'out_file', convertDset, 'in_file')
    pipeline.connect(surf2surf, ('out_file', split_file_ext), convertDset, 'out_file')
    
    
    #selCortex
    pipeline.connect(suma, 'SUMAfolder', sel_ctx, 'in_dir')
    pipeline.connect(convertDset, 'out_file', sel_ctx , 'in_file')
    
    #surf_select 
    pipeline.connect(reconall, 'subject_id', surf_sf, 'subject_id')
    pipeline.connect(reconall, 'subjects_dir', surf_sf, 'base_directory')
   
    #mris_fwhm
    pipeline.connect(reconall, 'subject_id', thickness_smooth, 'subject_id')
    pipeline.connect(surf_sf, 'thickness', thickness_smooth, 'in_file')
    pipeline.connect(inputnode, 'subjects_dir',thickness_smooth, 'subjects_dir')

    pipeline.connect(reconall, 'subject_id', wg_pct_smooth, 'subject_id')
    pipeline.connect(surf_sf, 'wg_pct', wg_pct_smooth, 'in_file')
    pipeline.connect(inputnode, 'subjects_dir',wg_pct_smooth, 'subjects_dir')
    
    #mris_convert
    #w-g.pct
    pipeline.connect(suma, 'SUMAfolder', convert_prefix, 'directory')
    pipeline.connect(convert_prefix, 'output', wg_convert, 'out_file')
    pipeline.connect(surf_sf, 'wg_pct', wg_convert, 'functional_file')
    pipeline.connect(surf_sf, 'white', wg_convert, 'in_file')
    
    #thicknessfwhm
    pipeline.connect(suma, 'SUMAfolder', thicksmooth_conv_pre, 'directory')
    pipeline.connect(thicksmooth_conv_pre, 'output', thick_convert, 'out_file')
    pipeline.connect(thickness_smooth, 'out_file', thick_convert, 'functional_file')
    pipeline.connect(surf_sf, 'white', thick_convert, 'in_file')
    
    #w-g.pct.fwhm
    pipeline.connect(suma, 'SUMAfolder', wgsmooth_conv_pre, 'directory')
    pipeline.connect(wgsmooth_conv_pre, 'output', wg_sm_convert, 'out_file')
    pipeline.connect(wg_pct_smooth, 'out_file', wg_sm_convert, 'functional_file')
    pipeline.connect(surf_sf, 'white', wg_sm_convert, 'in_file')
    
    #copy .gii to .gii.dset
    pipeline.connect(wg_convert, 'converted', cp_wg_dset, 'in_file')
    pipeline.connect(wg_sm_convert, 'converted', cp_wgsm_dset, 'in_file')
    pipeline.connect(thick_convert, 'converted', cp_thicksm_dset, 'in_file')
    
    #surfToSurf for smoothed dataset
    
    pipeline.connect(cp_wg_dset, 'out_file', surf2surf_wg_dset,'dset')
    pipeline.connect(suma, 'surf_A', surf2surf_wg_dset, 'surf_A')
    pipeline.connect(suma, 'surf_B', surf2surf_wg_dset, 'surf_B')
    pipeline.connect(suma, 'my_map', surf2surf_wg_dset,'mapfile' )
    pipeline.connect(joinpath6, 'output',  surf2surf_wg_dset, 'prefix')
    
    
    pipeline.connect(cp_wgsm_dset, 'out_file',  surf2surf_wg_sm_dset,'dset')
    pipeline.connect(suma, 'surf_A', surf2surf_wg_sm_dset, 'surf_A')
    pipeline.connect(suma, 'surf_B', surf2surf_wg_sm_dset, 'surf_B')
    pipeline.connect(suma, 'my_map', surf2surf_wg_sm_dset,'mapfile' )
    pipeline.connect(joinpath6, 'output', surf2surf_wg_sm_dset, 'prefix')
    
    
    pipeline.connect(cp_thicksm_dset, 'out_file',  surf2surf_thick_dset,'dset')
    pipeline.connect(suma, 'surf_A', surf2surf_thick_dset, 'surf_A')
    pipeline.connect(suma, 'surf_B', surf2surf_thick_dset, 'surf_B')
    pipeline.connect(suma, 'my_map', surf2surf_thick_dset,'mapfile')
    pipeline.connect(joinpath6, 'output', surf2surf_thick_dset, 'prefix')
    
        
    #convert_smooth_Dset
    pipeline.connect(suma, 'curv', convertDset_dset_curve, 'in_file')
    pipeline.connect(suma, ('curv', split_file_ext), convertDset_dset_curve, 'out_file')
    
    pipeline.connect(suma, 'sulc', convertDset_dset_sulc, 'in_file')
    pipeline.connect(suma, ('sulc', split_file_ext), convertDset_dset_sulc, 'out_file')
    
    pipeline.connect(suma, 'thickness', convertDset_dset_thick, 'in_file')
    pipeline.connect(suma, ('thickness', split_file_ext), convertDset_dset_thick, 'out_file')
    
    pipeline.connect(surf2surf_wg_dset, 'out_file', convertDset_dset_wg, 'in_file')
    pipeline.connect(surf2surf_wg_dset, ('out_file', split_file_ext), convertDset_dset_wg, 'out_file')
    
    pipeline.connect(surf2surf_wg_sm_dset, 'out_file', convertDset_dset_wgsm, 'in_file')
    pipeline.connect(surf2surf_wg_sm_dset, ('out_file', split_file_ext), convertDset_dset_wgsm, 'out_file')
    
    pipeline.connect(surf2surf_thick_dset, 'out_file', convertDset_dset_thicksm, 'in_file')
    pipeline.connect(surf2surf_thick_dset, ('out_file', split_file_ext), convertDset_dset_thicksm, 'out_file')
    
    
    pipeline.connect(inputnode, 't1w', copy_t1, 'in_file')
    pipeline.connect(copy_t1, 'out_file', Align2Exp, 'in_file_BRIK')
    pipeline.connect(suma, 'surfvol', Align2Exp, 'surf_file')
    
    pipeline.connect(inputnode, 'subject_id', outputnode, 'subject_id')
    pipeline.connect(joinpath1, 'output', outputnode, 'subjects_dir')
    pipeline.connect(suma, 'SUMAfolder', outputnode, 'subj_SUMA_dir')
    pipeline.connect(inputnode, 't1w', outputnode, 't1w')
    pipeline.connect(suma, 'surfvol', outputnode, 'surfvol')
    pipeline.connect(suma, 'spec', outputnode, 'spec')
    pipeline.connect(convertDset_dset_curve, 'out_file', outputnode, 'curv')
    pipeline.connect(convertDset_dset_sulc, 'out_file', outputnode, 'sulc')
    pipeline.connect(convertDset_dset_thicksm, 'out_file', outputnode, 'thickness')
    pipeline.connect(convertDset_dset_wgsm, 'out_file', outputnode, 'wg_pct')
    pipeline.connect(suma, 'aparc_annot', outputnode, 'aparc_annot')
    pipeline.connect(suma, 'inf200', outputnode, 'inf200')
    pipeline.connect(suma, 'inflated', outputnode, 'inflated')
    pipeline.connect(suma, 'pial', outputnode, 'pial')
    pipeline.connect(suma, 'sphere', outputnode, 'sphere')
    pipeline.connect(suma, 'white', outputnode, 'white')
    pipeline.connect(suma, 'smoothwm', outputnode, 'smoothwm')
    pipeline.connect(suma, 'sphere_reg', outputnode, 'sphere_reg')    
    pipeline.connect(sel_ctx, 'lh_data', outputnode, 'lh_selctx')
    pipeline.connect(sel_ctx, 'rh_data', outputnode, 'rh_selctx' )
    pipeline.connect(Align2Exp, 'out_file_HEAD', outputnode, 'surfvol_Alnd_HEAD')
    pipeline.connect(Align2Exp, 'out_file_BRIK', outputnode, 'surfvol_Alnd_BRIK')
    
    #pipeline.write_graph(graph2use="colored", format="svg", simple_form=True)
    return pipeline 










