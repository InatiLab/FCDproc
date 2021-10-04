#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Jan 6 2021

@author: Shervin Abdollahi

Node definitions for Nipype pipeline
This code wraps the preprocessing components

################   TODO  ################

"""

import os
#import numpy as np
from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import (
    
    CommandLineInputSpec,
    CommandLine,
    TraitedSpec,
    traits,
    isdefined,
    File,
    Str,
    Directory,
) 
from nipype.interfaces.afni.base import (
    AFNICommandBase,
    AFNICommand,
    AFNICommandInputSpec,
    AFNICommandOutputSpec,
    AFNIPythonCommandInputSpec,
    AFNIPythonCommand,
    Info,
    no_afni,
)

from nipype.interfaces.freesurfer.base import (
    FSCommand,
    FSTraitedSpec,
    FSTraitedSpecOpenMP,
    FSCommandOpenMP,
    Info,
    )
from nipype.utils.filemanip import fname_presuffix, split_filename

filters = ["mask","ave","max","max_abs","median","midpoint","min","mode", "seg_val"]
# Axialization Interface

class AxializeAnatInputSpec(AFNICommandInputSpec):
    in_file = File(exists=True, mandatory=True, argstr='-inset %s', position=-1, desc="the input dataset", copyfile=True)
    ref_file = File(exists=True, argstr='-refset %s', desc="file to be used as a reference")
    prefix = traits.Str(argstr='-prefix %s',position=-2, name_source="%s_axialized", genfile=True, desc='output file')
    mode_t1w = traits.Bool(argstr='-mode_t1w', desc='specifying the type of image contrast', default_value=True, usedefault=True)
    no_mask = traits.Str(argstr='-extra_al_inps %s', desc='Dont try to use a subregion for warping', default_value='-nomask', usedefault=True)
    skull_strip = traits.Bool(argstr='-focus_by_ss', desc='make a brain mask by simply skullstripping input dataset', default_value=True, usedefault=True)  
    no_qc = traits.Bool(argstr='-no_qc_view', desc='turn off default+automatic QC image saving/viewing', default_value=True, usedefault=True)  
    
class AxializeAnatOutputSpec(TraitedSpec):
    
    out_file = File(desc='output image file name')

class AxializeAnat(AFNICommand):
    _cmd = 'fat_proc_axialize_anat'
    input_spec = AxializeAnatInputSpec
    output_spec = AxializeAnatOutputSpec

    def _list_outputs(self):
       outputs = self.output_spec().get()
       if not isdefined(self.inputs.prefix):
           outputs['out_file'] = self._gen_filename(self.inputs.in_file, suffix='_axialize.nii.gz')
       else:
           outputs['out_file'] = os.path.abspath(self.inputs.prefix+'.nii.gz')
    
       return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
           return self._list_outputs()[name]
    
    
    
    
class GenerateFeatInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, mandatory=True, argstr='%s', position=-1, desc="the input dataset", copyfile=True)
    num_scales = traits.Int(argstr='--num_scales %d', desc='number of spatial scales- default is 3', default_value=3, usedefault=True)
    prefix = traits.Str(argstr='--output %s', desc='output file')
    
class GenerateFeatOutputSpce(TraitedSpec):
    out_file = File(desc='output image file name')

class GenerateFeat(CommandLine):
    
    _cmd = 'compute_features'
    input_spec = GenerateFeatInputSpec
    output_spec = GenerateFeatOutputSpce
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self.inputs.prefix+'.nii')
    
        return outputs
        
    
class SumaMakeSpecInputSpec(CommandLineInputSpec):
    subject_id = Str(argstr='-sid %s', position=-1, mandatory=True, desc='subject_id to be processed')
    in_file = Directory(argstr='-fspath %s', exists=True, mandatory=True, desc='subject freesurfer directory')
    ld = traits.Int(argstr='-ld %d', default_value=60, usedefault=True, desc='Create standard mesh surfaces with mesh density linear depth')
    NIFTI = traits.Bool(argstr='-NIFTI', default_value=True, usedefault=True, desc='Produce files in exchangeable formats')

class SumaMakeSpecOutputSpec(TraitedSpec):
    SUMAfolder = Directory(desc='ouput directory called SUMA')
    surf_A = traits.List(desc='surface_A')
    surf_B = traits.List(desc='surface_B')
    my_map = traits.List(desc='mapfile')
    curv = traits.List(desc='curvature')
    sulc = traits.List(desc='sulc')
    thickness = traits.List(desc='thickness')
    surfvol = File(desc='subject surface volume file')
    spec = traits.List(desc='{both, lh,rh} spec file')
    aparc_annot = traits.List(desc='aparc annot file')
    inf200 = traits.List(desc='inf_200 surface file')
    inflated = traits.List(desc='inflated surface file')
    pial = traits.List(desc='pial surface file')
    sphere = traits.List(desc='sphere surface file')
    sphere_reg = traits.List(desc='shpere reg surface file')
    white = traits.List(desc='white surface file')
    smoothwm = traits.List(desc='smooth white matter surface file')
    dual_sphere_reg = traits.List(desc='lh/rh.sphere.reg surface file')
    

class SumaMakeSpecFS(CommandLine):
    
    _cmd = '@SUMA_Make_Spec_FS'
    input_spec = SumaMakeSpecInputSpec
    output_spec = SumaMakeSpecOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        in_dir, base, ext = split_filename(self.inputs.in_file)
        id = self.inputs.subject_id
        
        outputs['SUMAfolder'] = os.path.abspath(os.path.join(self.inputs.in_file,'SUMA'))
        outputs['surf_A'] = [os.path.join(self.inputs.in_file, 'SUMA/lh.smoothwm.gii'), os.path.join(self.inputs.in_file ,'SUMA/rh.smoothwm.gii')]
        outputs['surf_B'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.smoothwm.gii'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.smoothwm.gii')]
        outputs['my_map'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.'+id+'_lh.niml.M2M'), os.path.join(self.inputs.in_file ,'SUMA/std.60.'+id+'_rh.niml.M2M')]
        outputs['curv'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.curv.niml.dset'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.curv.niml.dset')]
        outputs['sulc'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.sulc.niml.dset'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.sulc.niml.dset')]
        outputs['thickness'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.thickness.niml.dset'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.thickness.niml.dset')]
        outputs['surfvol'] = os.path.join(self.inputs.in_file, 'SUMA/'+id+'_SurfVol.nii')
        outputs['spec'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.'+id+'_both.spec'), os.path.join(self.inputs.in_file ,'SUMA/std.60.'+id+'_lh.spec'), os.path.join(self.inputs.in_file ,'SUMA/std.60.'+id+'_rh.spec')]
        outputs['aparc_annot'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.aparc.a2009s.annot.niml.dset'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.aparc.a2009s.annot.niml.dset')]
        outputs['inf200'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.inf_200.gii'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.inf_200.gii')]
        outputs['inflated'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.inflated.gii'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.inflated.gii')]
        outputs['pial'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.pial.gii'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.pial.gii')]
        outputs['sphere'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.sphere.gii'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.sphere.gii')] 
        outputs['sphere_reg'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.sphere.reg.gii'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.sphere.reg.gii')]
        outputs['white'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.white.gii'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.white.gii')]
        outputs['smoothwm'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.smoothwm.gii'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.smoothwm.gii')]
        outputs['dual_sphere_reg'] = [os.path.join(self.inputs.in_file, 'SUMA/std.60.lh.rh.sphere.reg.gii'), os.path.join(self.inputs.in_file ,'SUMA/std.60.rh.lh.sphere.reg.gii')]
        
        
        
        return outputs

class FSread_InputSpec(FSTraitedSpec):
     in_file = File(argstr='-input %s', exists=True, mandatory=True, desc="Binary formatted FreeSurfer annotation file")
     out_file = File(argstr='-dset %s', desc = "Write the annotation and colormap as a niml formatted Label Dset")
     cmap = File(argstr='-FScmap %s', mandatory=True, exists=True, desc='colormap files')
     hemi = traits.Enum('lh', 'rh', argstr='-hemi %s', mandatory=True, desc='target hemisphere')
     
class FSread_OutputSpec(TraitedSpec):
    out_file = File(desc= 'niml formated label Dset')
    

class FSread(FSCommand):
    
        _cmd = 'FSread_annot'
        input_spec = FSread_InputSpec
        output_spec = FSread_OutputSpec

        def _list_outputs(self):
           outputs = self.output_spec().get()
           outputs["out_file"] = os.path.abspath(self.inputs.out_file)
           #outputs["out_file"] = os.path.abspath(self.inputs.in_file+'.niml.dset')
           return outputs    
    
class Surf2SurfInputSpec(CommandLineInputSpec):
    surf_A = File(argstr='-i %s', mandatory=True, exists=True, desc='input surface A- Gifti XML surface format')
    surf_B = File(argstr='-i %s', mandatory=True, exists=True, desc='input surface B- Gifti XML surface format')
    prefix = Str(argstr='-prefix %s', dsec='output file prefix')
    mapfile = File(argstr='-mapfile %s', desc='use mapping from s2 to s2 that is stored in this file')
    dset = File(argstr='-dset %s', mandatory=True, exists=True, desc='file to be interpolated')
    output_params = traits.Str(argstr='-output_params %s', desc='mapping paramter to include in output')
    overwrite =  traits.Bool(argstr='-overwrite', desc='overwrite the 1D file', default_value=True, usedefault=True)

    
class Surf2SurfOutputSpec(TraitedSpec):

    out_file = File(desc='output file in form of:std.60.${hemi}.${dset}.niml.dset')
    
    
class Surf2Surf(CommandLine):
    _cmd  = 'SurfToSurf'
    input_spec = Surf2SurfInputSpec
    output_spec = Surf2SurfOutputSpec 

    def _list_outputs(self):
           outputs = self.output_spec().get()
           path, base, ext = split_filename(self.inputs.dset)
           prefix = self.inputs.prefix
           
           if ext == '.niml.dset':
               
               outputs["out_file"] = os.path.abspath(prefix + '.' + base + '.niml.dset')
           elif ext == '.dset':
           
               filename, file_extension = os.path.splitext(base)
               outputs["out_file"] = os.path.abspath(prefix + '.' + filename + '.niml.dset')

           return outputs

    
    
#this example is taken from  https://github.com/nipy/nipype/blob/47fe00b38/nipype/interfaces/freesurfer/utils.py#L571-L671  
class SurfaceSmoothInputSpec(FSTraitedSpec):
    in_file = File(mandatory=True, argstr="--i %s", desc="input surface file")
    subject_id = traits.Str(mandatory=True, argstr="--s %s", desc="subject id of surface file")
    hemi = traits.Enum("lh", "rh", argstr="--hemi %s", mandatory=True, desc="hemisphere to operate on")
    fwhm = traits.Float(argstr="--fwhm %d",default_value=5, usedefault=True, desc="effective FWHM of the smoothing process")
    out_file = File(argstr="--o %s", genfile=True, desc="surface file to write")
    cortex = traits.Bool(argstr="--cortex", default_value=True, usedefault=True, desc="only smooth within ``$hemi.cortex.label``")
    smooth = traits.Bool(argstr="--smooth-only",default_value=True, usedefault=True, desc="only smooth (implies --no-detrend)")
    surface = traits.Enum("thickness", "w-g.pct", desc='the surface type to smooth' )

class SurfaceSmoothOutputSpec(TraitedSpec):
    
    out_file = File(exists=True, desc="smoothed surface file")

class SurfaceSmooth(FSCommand):
    
    _cmd = 'mris_fwhm'
    input_spec = SurfaceSmoothInputSpec
    output_spec = SurfaceSmoothOutputSpec
        
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_file"] = self.inputs.out_file
        
        if not isdefined(outputs["out_file"]):
            if isdefined(self.inputs.in_file):
                source = self.inputs.in_file
                        
            if isdefined(self.inputs.fwhm) and isdefined(self.inputs.surface):
                kernel = self.inputs.fwhm
                surface = self.inputs.surface
                
                if surface == 'w-g.pct':
                     
                    outputs['out_file'] = fname_presuffix(source, suffix='.fwhm%d.mgh'  % kernel, newpath=None, use_ext=False)
            
                if surface == 'thickness':
               
                    outputs['out_file'] = fname_presuffix(source, suffix='.%s.fwhm%d.mgh' % (surface, kernel), newpath=None, use_ext=False)
        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs 
 
    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None
    
class CopyFileInputSpec(CommandLineInputSpec):
    
    in_file = File(desc='data file to be copied', exists=True, mandatory=True, argstr="%s", position=1)
    suffix = traits.Str(desc='the suffix for the new copied file', default_value='.gii.dset', usedefault=True, mandatory=True)
    out_file = traits.Str(dsec='output file name', argstr='%s', position=-1, genfile=True) 
    
class CopyFileOutputSpec(TraitedSpec):
    
    out_file = File(desc='The output filename of the new dataset')
    
class CopyFiles(CommandLine):
    _cmd = 'cp -r'
    input_spec = CopyFileInputSpec
    output_spec = CopyFileOutputSpec
    
    def _list_outputs(self):
        
        outputs = self.output_spec().get()
        
        if not isdefined(self.inputs.out_file):
            
            if isdefined(self.inputs.in_file):
                source = self.inputs.in_file
                
                if isdefined(self.inputs.suffix):
                    suffix = self.inputs.suffix
                    
                    outputs['out_file'] = fname_presuffix(source, suffix=suffix, newpath=None, use_ext=False)

        else:
            outputs['out_file'] = os.path.abspath(self.inputs.out_file)
            
        return outputs
    
    
    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()[name]
        return None
    
        
    
class SUMA_align2expInputSpec(CommandLineInputSpec):
    
    in_file_BRIK = traits.File(desc="input axiliazed t1 BRIK file", argstr='-exp_anat %s', exists=True, copyfile=True)
    #in_file_HEAD = traits.File(desc="input axiliazed t1 HEAD file", exists=True, copyfile=True)
    surf_file = traits.Str(exists=True, mandatory=True, argstr='-surf_anat %s', desc="Surf volume file", copyfile=True)
    prefix = traits.Str(argstr='-prefix %s', desc='output file prefix')
    outputtype = traits.Enum("AFNI", "NIFTI", desc="AFNI output filetype")

class SUMA_align2expOutputSpec(TraitedSpec):
    
     out_file_HEAD = File(desc='output surfvol file aligned to t1 file')
     out_file_BRIK = File(desc='output surfvol file aligned to t1 file')
    
class SUMA_align2Exp(CommandLine):
    
    _cmd = '@SUMA_AlignToExperiment'
    input_spec = SUMA_align2expInputSpec
    output_spec = SUMA_align2expOutputSpec
    #output_spec = AFNICommandOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        in_dir, base, suffix = split_filename(self.inputs.in_file_BRIK)
        surf_dir, base2, ext = split_filename(self.inputs.surf_file)
        prefix = self.inputs.prefix
    
        #outputs['out_file_HEAD'] = os.path.join(in_dir, prefix+'+orig.HEAD')
        #outputs['out_file_BRIK'] = os.path.join(in_dir, prefix+'+orig.BRIK')
        outputs['out_file_HEAD'] = os.path.join(surf_dir, prefix+'+orig.HEAD')
        outputs['out_file_BRIK'] = os.path.join(surf_dir, prefix+'+orig.BRIK')
        

        
        return outputs
      

class Vol2Surf_InputSpec(CommandLineInputSpec):
    
    spec_file = traits.File(desc="SUMA spec file", argstr='-spec %s',exists=True, mandatory=True)
    surf_A = traits.Str(desc="the first ref surface to use", argstr='-surf_A %s', default_value='white', usedefault=True)   
    surf_B = traits.File(desc="the second ref surface to use", argstr='-surf_B %s', xor=['use_norm'], exists=True)
    f_steps = traits.Int(desc="the number of evenly spaced points along each segment", argstr='-f_steps %d')
    f_index = traits.Enum("voxels", "nodes", requires=["f_steps"], desc="specifies whether to use all segment point values in the filter (usingthe 'nodes' TYPE), or to use only those corresponding to unique volume voxels")
    f_p1_mm = traits.Float(desc="distance in millimeters to add to the first point of each line segment", argstr='-f_p1_mm %.2f')
    f_pn_mm = traits.Float(desc="distance in millimeters to add to the second point of each line segment", argstr='-f_pn_mm %.2f')
    f_p1_fr = traits.Float(desc="a change to point p1, in the direction of point pn, but the change is a fraction of the original distance, not a pure change in millimeters", argstr='-f_p1_fr %.2f')
    f_pn_fr = traits.Float(desc="the FRACTION is in the direction from p1 to pn", argstr='-f_pn_fr %.2f')
    surf_vol = traits.File(desc="AFNI volume dset that surface is mapped to", argstr='-sv %s')
    in_file = traits.File(desc="voume to be sampled on surface", argstr='-grid_parent %s', exist=True, mandatory=True)
    map_func = traits.Str(argstr='-map_func %s', desc="filters for values along the segment", default_value='mask', usedefault=True)
    use_norm = traits.Bool(desc="use normals for the second surface", argstr='-use_norm', default_value=True)
    keep_nor_dir = traits.Bool(desc="keep the direction of the normals", argstr='-keep_norm_dir')
    norm_len = traits.Int(desc="keep the direction of the normals", argstr='-norm_len %d', requires=['use_norm'], default_value=1)
    out_file = traits.File(desc="output file name", argstr='-out_1D %s', genfile=True)
    header = traits.Bool(desc="do not output column headers", argstr='-no_headers', default_value=True, usedefault=True)
    outcol = traits.Bool(desc="output only all result columns", argstr='-outcols_results', default_value=True, usedefault=True)

    
class Vol2Surf_OutputSpec(TraitedSpec):
    
    out_file = traits.File(desc="output 1D file", exist=True)
    
class Vol2Surf(CommandLine):

    _cmd = "3dVol2Surf"
    input_spec = Vol2Surf_InputSpec
    output_spec = Vol2Surf_OutputSpec

    def _list_outputs(self):
       outputs = self.output_spec().get()
       
       if not isdefined(self.inputs.out_file):
           if isdefined(self.inputs.in_file):
               path1, base, ext1 = split_filename(self.inputs.in_file)
           if isdefined(self.inputs.spec_file):
               path2, prefix, ext2 = split_filename(self.inputs.spec_file)
               hemi = prefix.split('_')[1]
               
            
           outputs['out_file'] = fname_presuffix(base, prefix='std.60.'+hemi+'.', suffix='.v2s.1D.dset', newpath=path2, use_ext=False)
                
       else:
           outputs['out_file'] = os.path.abspath(self.inputs.out_file)
              
       
       return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
           return self._list_outputs()[name]

        return None

    
class SurfSmooth_InputSpec(CommandLineInputSpec):  
    
    spec_file = traits.File(desc="SUMA spec file", argstr='-spec %s',exists=True, mandatory=True)
    surf_A = traits.Str(desc="the surface to smooth", argstr='-surf_A %s', default_value='white', usedefault=True)   
    in_file = traits.File(desc="file containing data (in 1D or NIML format)", argstr='-input %s', exist=True, mandatory=True)
    fwhm = traits.Float(desc="Blur by a Gaussian filter that has a Full Width at Half Maximum in surface coordinate units (usuallly mm) of F", argstr='-fwhm %d')
    met = traits.Enum("HEAT_07", "HEAT_05", "LM", "NN_geom", desc="methods to filter the data on surface", argstr='-met %s', mandatory=True)
    out_file = traits.File(desc="output file name", argstr='-output %s', genfile=True)
    b_mask = traits.File(desc="binary mask 1D file", argstr='-b_mask %s', exists=True, mandatory=True)
    
class SurfSmooth_OutputSpec(TraitedSpec):
    
    out_file = traits.File(desc="output 1D file", exist=True)
    
    
class SurfSmooth(CommandLine):
    
    _cmd = "SurfSmooth"
    input_spec = SurfSmooth_InputSpec
    output_spec = SurfSmooth_OutputSpec
    
    def _list_outputs(self):
       outputs = self.output_spec().get()
       
       if not isdefined(self.inputs.out_file):
           if isdefined(self.inputs.in_file):
               path, base, ext1 = split_filename(self.inputs.in_file)
               base1 = base.split('.1D')[0]
               
               
           if isdefined(self.inputs.fwhm):  
               n = self.inputs.fwhm
           
           outputs['out_file'] = fname_presuffix(base1, suffix='.fwhm%d.1D.dset' %n, newpath=path, use_ext=False)
                
       else:
           outputs['out_file'] = os.path.abspath(self.inputs.out_file)
              
       
       return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
           return self._list_outputs()[name]

        return None

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    






























































				
	   



