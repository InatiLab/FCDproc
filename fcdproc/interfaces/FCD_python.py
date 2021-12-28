#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 09:11:24 2021

@author: abdollahis2
"""

import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, Directory, Str,File, TraitedSpec
    
from nipype.utils.filemanip import  split_filename
from fcdproc.utils.misc import flat_and_select, seperate_subj_features

NHEMI=36002

class SelectCortexInputSpec(BaseInterfaceInputSpec):
    in_file = traits.List(exist=True, mandatory=True, desc="SUMA 1D file") 
    in_dir = Directory(exist=True, mandatory=True, desc="SUMA working directory")
    out_prefix = Str(desc="output file prefix")
    
class SelectCortexOutputSpec(TraitedSpec):
    lh_data = File(desc='output left hemisphere file in the form of std.60.lh.sel_ctx.1D.dset')
    rh_data = File(desc='output right hemisphere file in the form of std.60.rh.sel_ctx.1D.dset')
    
class SelectCortex(BaseInterface):
    
    input_spec = SelectCortexInputSpec
    output_spec = SelectCortexOutputSpec
    
    def _run_interface(self, runtime):
        import numpy as np 

        
        wdir = self.inputs.in_dir 
        file = self.inputs.in_file
        out_prefix = self.inputs.out_prefix
            
        def loadDset(lh_data,rh_data):
           lh_data = np.loadtxt(lh_data, dtype=np.float32, comments='#')
           rh_data = np.loadtxt(rh_data, dtype=np.float32, comments='#')
           
           if lh_data.ndim == 1:
                lh_data = lh_data.reshape([lh_data.shape[0],1])
           if rh_data.ndim == 1:
                rh_data = rh_data.reshape([rh_data.shape[0],1])

           data = np.vstack([lh_data, rh_data])

           return data 

        def saveData(data, wdir, outName):
         nleft=36002
        
         if data.ndim == 1:
            lh_data = data[:nleft]
            rh_data = data[nleft:]
         else:
            lh_data = data[:nleft,:]
            rh_data = data[nleft:,:]
            
           
         np.savetxt(wdir+f'/std.60.lh.{outName}.1D.dset', lh_data)
         np.savetxt(wdir+f'/std.60.rh.{outName}.1D.dset', rh_data)
    	
        y = loadDset(file[0], file[1])
        sel_y = np.ravel(y == 1639705) | np.ravel(y == 3294840)

        xx = np.ones([y.shape[0]])
        xx[sel_y] = 0
        saveData(xx, wdir, out_prefix)
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        out_prefix = self.inputs.out_prefix
        wdir = self.inputs.in_dir
        
        outputs["lh_data"] = os.path.join(wdir,'std.60.lh.'+ out_prefix +'.1D.dset')
        outputs["rh_data"] = os.path.join(wdir,'std.60.rh.'+ out_prefix +'.1D.dset')
        
        return outputs
    
    
class ConcatFeatInputSpec(BaseInterfaceInputSpec):
    lh_features = traits.List(desc="list of t1,t2,fl features 1D files on left hemisphere")    
    rh_features = traits.List(desc="list of t1,t2,fl features 1D files on right hemisphere") 
    lh_selctx = traits.File(desc="left hemisphere sel cortex")
    rh_selctx = traits.File(desc="right hemisphere sel cortex")
    #in_dir = Directory(exist=True, mandatory=True, desc="SUMA working directory")
    
    
class ConcatFeatOutputSpec(TraitedSpec):
    
    lh_data = File(desc='output left hemisphere file in the form of std.60.lh.features.1D.dset')
    rh_data = File(desc='output right hemisphere file in the form of std.60.rh.features.1D.dset')
    
class ConcatFeat(BaseInterface):
    
    input_spec = ConcatFeatInputSpec
    output_spec = ConcatFeatOutputSpec
    
    def _run_interface(self, runtime):
        import numpy as np
        lh_feat = self.inputs.lh_features
        rh_feat = self.inputs.rh_features
        lh_sel = self.inputs.lh_selctx
        rh_sel = self.inputs.rh_selctx
        wdir_lh, base, ext = split_filename(lh_feat[0])

         
        def loadDset(lh_data,rh_data):
           lh_data = np.loadtxt(lh_data, dtype=np.float32, comments='#')
           rh_data = np.loadtxt(rh_data, dtype=np.float32, comments='#')
           
           if lh_data.ndim == 1:
                lh_data = lh_data.reshape([lh_data.shape[0],1])
           if rh_data.ndim == 1:
                rh_data = rh_data.reshape([rh_data.shape[0],1])

           data = np.vstack([lh_data, rh_data])

           return data 

        def saveData(data, wdir, outName, sel=None):
       
            nboth = 72004
            nleft = 36002

            if sel is None:
                my_data = data
            else:
                if data.ndim == 1:
                    my_data = np.zeros([nboth])
                    my_data[sel] = data
                else:
                    my_data = np.zeros([nboth,data.shape[1]])
                    my_data[sel,:] = data
                    
            if data.ndim == 1:
                lh_data = my_data[:nleft]
                rh_data = my_data[nleft:]
            else:
                lh_data = my_data[:nleft,:]
                rh_data = my_data[nleft:,:]

            np.savetxt(wdir_lh+f'/std.60.lh.{outName}.1D.dset', lh_data)
            np.savetxt(wdir_lh+f'/std.60.rh.{outName}.1D.dset', rh_data)
           
            
        sel = loadDset(lh_sel, rh_sel)
        sel = np.ravel(sel == 0)
            
        data=[]
        for i in range(len(lh_feat)):
            xx = loadDset(lh_feat[i], rh_feat[i])
            data.append(xx)
                
        data = np.hstack(data)
        data[sel,:] = 0
        saveData(data, wdir_lh, 'features')
           
        
        return runtime
    
    def _list_outputs(self):
        import os
        outputs = self._outputs().get()
        lh_feat = self.inputs.lh_features
        wdir_lh, base, ext = split_filename(lh_feat[0])

        
        outputs["lh_data"] = os.path.abspath(wdir_lh+'/std.60.lh.features.1D.dset')
        outputs["rh_data"] = os.path.abspath(wdir_lh+'/std.60.rh.features.1D.dset')
        
        return outputs
    
    
class FeatGlobalScaleInputSpec(BaseInterfaceInputSpec):
    
    lh_features = traits.File(desc="list of all features 1D files on left hemisphere")    
    rh_features = traits.File(desc="list of all features 1D files on right hemisphere") 
    lh_selctx = traits.File(desc="left hemisphere sel cortex")
    rh_selctx = traits.File(desc="right hemisphere sel cortex")
        
    
class FeatGlobalScaleOutputSpec(TraitedSpec):
    
    lh_data = File(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.1D.dset')
    rh_data = File(desc='output right hemisphere file in the form of std.60.rh.features.globalSTD.1D.dset')
    
class FeatGlobalScale(BaseInterface):
    
    
      input_spec = FeatGlobalScaleInputSpec
      output_spec = FeatGlobalScaleOutputSpec
    
      def _run_interface(self, runtime):
        import numpy as np
        lh_feat = self.inputs.lh_features
        rh_feat = self.inputs.rh_features
        lh_sel = self.inputs.lh_selctx
        rh_sel = self.inputs.rh_selctx
        wdir, base, ext = split_filename(lh_feat)

         
        def loadDset(lh_data,rh_data):
           lh_data = np.loadtxt(lh_data, dtype=np.float32, comments='#')
           rh_data = np.loadtxt(rh_data, dtype=np.float32, comments='#')
           
           if lh_data.ndim == 1:
                lh_data = lh_data.reshape([lh_data.shape[0],1])
           if rh_data.ndim == 1:
                rh_data = rh_data.reshape([rh_data.shape[0],1])

           data = np.vstack([lh_data, rh_data])

           return data 

        def saveData(data, wdir, outName, sel=None):
            
            nboth = 72004
            nleft = 36002

            if sel is None:
                my_data = data
            else:
                if data.ndim == 1:
                    my_data = np.zeros([nboth])
                    my_data[sel] = data
                else:
                    my_data = np.zeros([nboth,data.shape[1]])
                    my_data[sel,:] = data
                    
            if data.ndim == 1:
                lh_data = my_data[:nleft]
                rh_data = my_data[nleft:]
            else:
                lh_data = my_data[:nleft,:]
                rh_data = my_data[nleft:,:]

            np.savetxt(wdir+f'/std.60.lh.{outName}.1D.dset', lh_data)
            np.savetxt(wdir+f'/std.60.rh.{outName}.1D.dset', rh_data)
            
        sel = loadDset(lh_sel, rh_sel)
        sel = np.ravel(sel == 1)
            
        data = loadDset(lh_feat, rh_feat)
        data = data[sel,:] 
       
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        Z = np.zeros(data.shape)
        for r in range(Z.shape[0]):
            Z[r,:] = (data[r,:] - mean) / std
        
        saveData(Z, wdir, 'features.globalSTD', sel=sel)
            
        return runtime
    
      def _list_outputs(self):
        import os
        outputs = self._outputs().get()
        lh_feat = self.inputs.lh_features
        wdir, base, ext = split_filename(lh_feat)

        
        outputs["lh_data"] = os.path.abspath(wdir+'/std.60.lh.features.globalSTD.1D.dset')
        outputs["rh_data"] = os.path.abspath(wdir+'/std.60.rh.features.globalSTD.1D.dset')
        
        return outputs  
    
    
class TrainPCAInputSpec(BaseInterfaceInputSpec):

    features = traits.List(desc="list of all standardized features 1D files on both hemisphere")    
    selctx = traits.List(desc="list of both hemisphere sel cortex")
    group = traits.List(desc="subject group to perform analysis on. can be controls, pt_positive, or pt_negative")

class TrainPCAOutputSpec(TraitedSpec):
    
   pca = traits.File(desc="learned pca model that explains 90% of variance")
   data = traits.File(desc="pca-reduced dataset from all controls")


class TrainPCA(BaseInterface):
    
   input_spec = TrainPCAInputSpec
   output_spec = TrainPCAOutputSpec

   def _run_interface(self, runtime):
        import numpy as np
        import os
        import joblib
        from sklearn.decomposition import PCA
        
        feature = self.inputs.features
        feat_flat = [item for sublist in feature for item in sublist]
        
        sel = self.inputs.selctx
        selctx_flat = [item for sublist in sel for item in sublist]
        
        subj_list = self.inputs.group
        
        features = seperate_subj_features(feat_flat, subj_list)
        selctx = seperate_subj_features(selctx_flat, subj_list)
        
        dset_dir, base, ext = split_filename(feat_flat[0])
        data_dir = os.path.dirname(dset_dir)
        subj_dir = os.path.dirname(data_dir)
        wdir = os.path.dirname(subj_dir)+'/model'
        dat_dir = os.path.dirname(subj_dir)+'/data'
        if not os.path.exists(wdir):
            os.makedirs(wdir)
        if not os.path.exists(dat_dir):
            os.makedirs(dat_dir)
        
        def loadDset(lh_data,rh_data):
           lh_data = np.loadtxt(lh_data, dtype=np.float32, comments='#')
           rh_data = np.loadtxt(rh_data, dtype=np.float32, comments='#')
           
           if lh_data.ndim == 1:
                lh_data = lh_data.reshape([lh_data.shape[0],1])
           if rh_data.ndim == 1:
                rh_data = rh_data.reshape([rh_data.shape[0],1])

           data = np.vstack([lh_data, rh_data])

           return data 

        
        data = []
        for i in range(int(len(features)/2)):
           
           sel = loadDset(selctx[2*i], selctx[2*i+1])
           sel = np.ravel(sel == 1)
           xx = loadDset(features[2*i], features[2*i+1])
           xx = xx[sel,:]
           data.append(xx)
           
        data = np.vstack(data)
        
        pca = PCA(copy=True, iterated_power='auto', n_components=0.9, random_state=None, svd_solver='auto', tol=0.0, whiten=False)
        Z = pca.fit_transform(data)
        joblib.dump(pca, wdir+'/PCA.globalSTD')
        joblib.dump(Z, dat_dir+'/globalSTD.PCA')
       
        return runtime
    
         
   def _list_outputs(self): 
       import os
       outputs = self._outputs().get()
       feature = self.inputs.features
       feat_flat = [item for sublist in feature for item in sublist]
       dset_dir, base, ext = split_filename(feat_flat[0])
       data_dir = os.path.dirname(dset_dir)
       subj_dir = os.path.dirname(data_dir)
       wdir = os.path.dirname(subj_dir)+'/model'
       dat_dir = os.path.dirname(subj_dir)+'/data'
       
       if not os.path.exists(wdir):
            os.makedirs(wdir)
       if not os.path.exists(dat_dir):
            os.makedirs(dat_dir)
        
       outputs["pca"] = os.path.abspath(wdir+'/PCA.globalSTD')
       outputs["data"] = os.path.abspath(dat_dir+'/globalSTD.PCA')
        
       return outputs    
    
class ApplyPCAInputSpec(BaseInterfaceInputSpec):

    features = traits.List(desc="list of all standardized features 1D files on both hemisphere")    
    selctx = traits.List(desc="list of both hemisphere sel cortex")
    model = traits.File(desc="trained pca model that explains %90 of variance")

class ApplyPCAOutputSpec(TraitedSpec):
    
    data = traits.List(traits.File(desc='output left hemisphere file in the form of std.60.${hemi}.features.globalSTD.PCA.1D.dset'))
    
    
class ApplyPCA(BaseInterface):
    
   input_spec = ApplyPCAInputSpec
   output_spec = ApplyPCAOutputSpec

   def _run_interface(self, runtime):
        import numpy as np
        import joblib
        
        
        feature = self.inputs.features
        feature_flat =  [item for sublist in feature for item in sublist]
        sel = self.inputs.selctx
        selctx_flat = [item for sublist in sel for item in sublist]
        pca_model = self.inputs.model
       
        
        def loadDset(lh_data,rh_data):
           lh_data = np.loadtxt(lh_data, dtype=np.float32, comments='#')
           rh_data = np.loadtxt(rh_data, dtype=np.float32, comments='#')
           
           if lh_data.ndim == 1:
                lh_data = lh_data.reshape([lh_data.shape[0],1])
           if rh_data.ndim == 1:
                rh_data = rh_data.reshape([rh_data.shape[0],1])

           data = np.vstack([lh_data, rh_data])

           return data 
       
        def saveData(data, wdir, outName, sel=None):
            
            nboth = 72004
            nleft = 36002

            if sel is None:
                my_data = data
            else:
                if data.ndim == 1:
                    my_data = np.zeros([nboth])
                    my_data[sel] = data
                else:
                    my_data = np.zeros([nboth,data.shape[1]])
                    my_data[sel,:] = data
                    
            if data.ndim == 1:
                lh_data = my_data[:nleft]
                rh_data = my_data[nleft:]
            else:
                lh_data = my_data[:nleft,:]
                rh_data = my_data[nleft:,:]

            np.savetxt(wdir+f'/std.60.lh.{outName}.1D.dset', lh_data)
            np.savetxt(wdir+f'/std.60.rh.{outName}.1D.dset', rh_data)
        
        
        for i in range((len(feature))):
           
            sel = loadDset(selctx_flat[2*i], selctx_flat[2*i+1])
            sel = np.ravel(sel == 1)
            data = loadDset(feature_flat[2*i], feature_flat[2*i+1])
            data = data[sel,:]
            wdir, base, ext = split_filename(feature_flat[2*i])
            model = joblib.load(pca_model)
            Z = model.transform(data)
            
            saveData(Z, wdir, 'features.globalSTD.PCA', sel=sel)
        
        return runtime
    
         
   def _list_outputs(self): 
       import os

       outputs = self._outputs().get()
       feature = self.inputs.features
       feature_flat =  [item for sublist in feature for item in sublist]
       
       pca_list = []
       for i in range(len(feature)):
           wdir, base, ext = split_filename(feature_flat[2*i])
           for hemi in ['lh', 'rh']:
               
               pca_list.append(os.path.join(wdir,'std.60.'+ hemi +'.features.globalSTD.PCA.1D.dset'))
           
   
       outputs['data'] = pca_list
       
       return outputs
    
    
class TrainGaussInputSpec(BaseInterfaceInputSpec):
    
        features_pca = traits.List(desc="list of all standardized features 1D files on both hemisphere")    
        selctx = traits.List(desc="list of both hemisphere sel cortex")
        group = traits.List(desc="subject group to perform analysis on. can be controls, pt_positive, or pt_negative")
        
class TrainGaussoutputSpec(TraitedSpec):

    gauss_iter1 = traits.File(desc="learned gaussinaization model on first iteration")
    gauss_iter2 = traits.File(desc="learned gaussinaization model on second iteration")
    gauss_iter3 = traits.File(desc="learned gaussinaization model on third iteration")
    gauss_iter4 = traits.File(desc="learned gaussinaization model on fourth iteration")
    gauss_iter5 = traits.File(desc="learned gaussinaization model on fifth iteration")
    gauss_iter6 = traits.File(desc="learned gaussinaization model on sixth iteration")
    gauss_iter7 = traits.File(desc="learned gaussinaization model on seventh iteration")
    gauss_iter8 = traits.File(desc="learned gaussinaization model on eighth iteration")
    gauss_iter9 = traits.File(desc="learned gaussinaization model on nineth iteration")
    gauss_iter10 = traits.File(desc="learned gaussinaization model on tenth iteration")
    model_dir = Directory(desc='gauss model output directory')
    
class TrainGauss(BaseInterface):    
    
    input_spec = TrainGaussInputSpec
    output_spec = TrainGaussoutputSpec
    
    def _run_interface(self, runtime):
        
        import numpy as np
        import os
        import joblib
        from sklearn.preprocessing import QuantileTransformer
        from sklearn.decomposition import PCA
    
    
        featurePCA = self.inputs.features_pca
        subj_list = self.inputs.group
        selctx = self.inputs.selctx
        selctx_flat = [item for sublist in selctx for item in sublist]

        features = seperate_subj_features(featurePCA, subj_list)
        selctx = seperate_subj_features(selctx_flat, subj_list)
        
        dset_dir, base, ext = split_filename(featurePCA[0])
        data_dir = os.path.dirname(dset_dir)
        subj_dir = os.path.dirname(data_dir)
        wdir = os.path.dirname(subj_dir)+'/model'
        dat_dir = os.path.dirname(subj_dir)+'/data'

            
        def loadDset(lh_data,rh_data):
           lh_data = np.loadtxt(lh_data, dtype=np.float32, comments='#')
           rh_data = np.loadtxt(rh_data, dtype=np.float32, comments='#')
           
           if lh_data.ndim == 1:
                lh_data = lh_data.reshape([lh_data.shape[0],1])
           if rh_data.ndim == 1:
                rh_data = rh_data.reshape([rh_data.shape[0],1])

           data = np.vstack([lh_data, rh_data])

           return data 
       
        data = []
        for i in range(int(len(selctx)/2)):
           
           sel = loadDset(selctx[2*i], selctx[2*i+1])
           sel = np.ravel(sel == 1)
           xx = loadDset(features[2*i], features[2*i+1])
           xx = xx[sel,:]
           data.append(xx)
           
        data = np.vstack(data)
        
        for n in [1,2,3,4,5,6,7,8,9,10]:
           if not os.path.exists(wdir+f'GAUSS.NITER{n}.features.globalSTD.PCA'):
               print('Fitting GAUSS NITER {} for features.globalSTD.PCA across controls...'.format(n))
               if n == 1:
                   X = data
               else:
                   m = np.int(n-1)
                   X = joblib.load(dat_dir+f'/features.globalSTD.PCA.GAUSS.NITER{m}')['PCA']
               
               norm = QuantileTransformer(output_distribution='normal', n_quantiles=1000, subsample=X.shape[0])
               Y = norm.fit_transform(X)
               pca = PCA()
               Z = pca.fit_transform(Y)
               my_model={}
               my_model['NORM'] = norm 
               my_model['PCA'] = pca
               my_data={}
               my_data['NORM'] = Y
               my_data['PCA'] = Z
               joblib.dump(my_model, wdir+f'/GAUSS.NITER{n}.features.globalSTD.PCA')
               joblib.dump(my_data, dat_dir+f'/features.globalSTD.PCA.GAUSS.NITER{n}')
               
        return runtime
           
    def _list_outputs(self):
              import os
              outputs = self._outputs().get()
              featurePCA = self.inputs.features_pca
              dset_dir, base, ext = split_filename(featurePCA[0])
              data_dir = os.path.dirname(dset_dir)
              subj_dir = os.path.dirname(data_dir)
              wdir = os.path.dirname(subj_dir)+'/model'
              

              outputs["gauss_iter1"] = os.path.abspath(wdir+'/GAUSS.NITER1.features.globalSTD.PCA')
              outputs["gauss_iter2"] = os.path.abspath(wdir+'/GAUSS.NITER2.features.globalSTD.PCA')
              outputs["gauss_iter3"] = os.path.abspath(wdir+'/GAUSS.NITER3.features.globalSTD.PCA')
              outputs["gauss_iter4"] = os.path.abspath(wdir+'/GAUSS.NITER4.features.globalSTD.PCA')
              outputs["gauss_iter5"] = os.path.abspath(wdir+'/GAUSS.NITER5.features.globalSTD.PCA')
              outputs["gauss_iter6"] = os.path.abspath(wdir+'/GAUSS.NITER6.features.globalSTD.PCA')
              outputs["gauss_iter7"] = os.path.abspath(wdir+'/GAUSS.NITER7.features.globalSTD.PCA')
              outputs["gauss_iter8"] = os.path.abspath(wdir+'/GAUSS.NITER8.features.globalSTD.PCA')
              outputs["gauss_iter9"] = os.path.abspath(wdir+'/GAUSS.NITER9.features.globalSTD.PCA')
              outputs["gauss_iter10"] = os.path.abspath(wdir+'/GAUSS.NITER10.features.globalSTD.PCA')
              outputs["model_dir"] = os.path.abspath(wdir)
              
              return outputs

                 
class ApplyGaussInputSpec(BaseInterfaceInputSpec):

    features_pca = traits.List(desc="list of all standardized features 1D files on both hemisphere")    
    selctx = traits.List(desc="list of both hemisphere sel cortex")
    model_dir = traits.Directory(desc="directory to find all Gauss trained models")

class ApplyGaussOutputSpec(TraitedSpec):
    
    gauss_n1 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')
    gauss_n2 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')
    gauss_n3 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')
    gauss_n4 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')
    gauss_n5 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')
    gauss_n6 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')
    gauss_n7 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')  
    gauss_n8 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')
    gauss_n9 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')
    gauss_n10 = traits.List(desc='output left hemisphere file in the form of std.60.lh.features.globalSTD.PCA.1D.dset')
   
    
    
class ApplyGauss(BaseInterface):
    
   input_spec = ApplyGaussInputSpec
   output_spec = ApplyGaussOutputSpec

   def _run_interface(self, runtime):
        import numpy as np
        import joblib
        
        
        featurePCA = self.inputs.features_pca
        selctx = self.inputs.selctx
        selctx_flat = [item for sublist in selctx for item in sublist]
        model_dir = self.inputs.model_dir

        
        def loadDset(lh_data,rh_data):
           lh_data = np.loadtxt(lh_data, dtype=np.float32, comments='#')
           rh_data = np.loadtxt(rh_data, dtype=np.float32, comments='#')
           
           if lh_data.ndim == 1:
                lh_data = lh_data.reshape([lh_data.shape[0],1])
           if rh_data.ndim == 1:
                rh_data = rh_data.reshape([rh_data.shape[0],1])

           data = np.vstack([lh_data, rh_data])

           return data 
       
        def loadGaussDset(wdir, fname):
           lh_data = np.loadtxt(wdir+f'/std.60.lh.{fname}.1D.dset', dtype=np.float32, comments='#')
           rh_data = np.loadtxt(wdir+f'/std.60.rh.{fname}.1D.dset', dtype=np.float32, comments='#')
           
           if lh_data.ndim == 1:
                lh_data = lh_data.reshape([lh_data.shape[0],1])
           if rh_data.ndim == 1:
                rh_data = rh_data.reshape([rh_data.shape[0],1])

           data = np.vstack([lh_data, rh_data])

           return data 
       
       
        def saveData(data, wdir, outName, sel=None):
            
            nboth = 72004
            nleft = 36002

            if sel is None:
                my_data = data
            else:
                if data.ndim == 1:
                    my_data = np.zeros([nboth])
                    my_data[sel] = data
                else:
                    my_data = np.zeros([nboth,data.shape[1]])
                    my_data[sel,:] = data
                    
            if data.ndim == 1:
                lh_data = my_data[:nleft]
                rh_data = my_data[nleft:]
            else:
                lh_data = my_data[:nleft,:]
                rh_data = my_data[nleft:,:]

            np.savetxt(wdir+f'/std.60.lh.{outName}.1D.dset', lh_data)
            np.savetxt(wdir+f'/std.60.rh.{outName}.1D.dset', rh_data)
        
      
            
        for i in range(len(selctx)):
          
            for n in [1,2,3,4,5,6,7,8,9,10]:
           
                sel = loadDset(selctx_flat[2*i], selctx_flat[2*i+1])
                sel = np.ravel(sel == 1)
                wdir, base, ext = split_filename(selctx_flat[2*i])
                
                if n == 1:
                    data = loadDset(featurePCA[2*i], featurePCA[2*i+1])
                else:
                    m = np.int(n-1)
                    data = loadGaussDset(wdir,f'features.globalSTD.PCA.GAUSS.NITER{m}' )
                        
                data = data[sel,:]
                model = joblib.load(model_dir+f'/GAUSS.NITER{n}.features.globalSTD.PCA')
                Y = model['NORM'].transform(data)
                Z = model['PCA'].transform(Y)
                
                saveData(Z, wdir, f'features.globalSTD.PCA.GAUSS.NITER{n}', sel=sel)
        
        return runtime
    
         
   def _list_outputs(self): 
       import os
       outputs = self._outputs().get()
       selctx = self.inputs.selctx
       selctx_flat = [item for sublist in selctx for item in sublist]
       
       gauss_n10_list = []
       for i in range((len(selctx))):
           
           wdir, base, ext = split_filename(selctx_flat[2*i])
           for hemi in ['lh', 'rh']:
               gauss_n10_list.append(os.path.abspath(wdir+'/std.60.' + hemi + '.features.globalSTD.PCA.GAUSS.NITER10.1D.dset'))
           
       outputs["gauss_n10"] = gauss_n10_list
       
       for i in range((len(selctx))):
           wdir, base, ext = split_filename(selctx_flat[2*i])
           
           outputs["gauss_n1"] = [os.path.abspath(wdir+'/std.60.lh.features.globalSTD.PCA.GAUSS.NITER1.1D.dset'), os.path.abspath(wdir+'/std.60.rh.features.globalSTD.PCA.GAUSS.NITER1.1D.dset')]
           outputs["gauss_n2"] = [os.path.abspath(wdir+'/std.60.lh.features.globalSTD.PCA.GAUSS.NITER2.1D.dset'), os.path.abspath(wdir+'/std.60.rh.features.globalSTD.PCA.GAUSS.NITER2.1D.dset')]
           outputs["gauss_n3"] = [os.path.abspath(wdir+'/std.60.lh.features.globalSTD.PCA.GAUSS.NITER3.1D.dset'), os.path.abspath(wdir+'/std.60.rh.features.globalSTD.PCA.GAUSS.NITER3.1D.dset')]
           outputs["gauss_n4"] = [os.path.abspath(wdir+'/std.60.lh.features.globalSTD.PCA.GAUSS.NITER4.1D.dset'), os.path.abspath(wdir+'/std.60.rh.features.globalSTD.PCA.GAUSS.NITER4.1D.dset')]
           outputs["gauss_n5"] = [os.path.abspath(wdir+'/std.60.lh.features.globalSTD.PCA.GAUSS.NITER5.1D.dset'), os.path.abspath(wdir+'/std.60.rh.features.globalSTD.PCA.GAUSS.NITER5.1D.dset')]
           outputs["gauss_n6"] = [os.path.abspath(wdir+'/std.60.lh.features.globalSTD.PCA.GAUSS.NITER6.1D.dset'), os.path.abspath(wdir+'/std.60.rh.features.globalSTD.PCA.GAUSS.NITER6.1D.dset')]
           outputs["gauss_n7"] = [os.path.abspath(wdir+'/std.60.lh.features.globalSTD.PCA.GAUSS.NITER7.1D.dset'), os.path.abspath(wdir+'/std.60.rh.features.globalSTD.PCA.GAUSS.NITER7.1D.dset')]
           outputs["gauss_n8"] = [os.path.abspath(wdir+'/std.60.lh.features.globalSTD.PCA.GAUSS.NITER8.1D.dset'), os.path.abspath(wdir+'/std.60.rh.features.globalSTD.PCA.GAUSS.NITER8.1D.dset')]
           outputs["gauss_n9"] = [os.path.abspath(wdir+'/std.60.lh.features.globalSTD.PCA.GAUSS.NITER9.1D.dset'), os.path.abspath(wdir+'/std.60.rh.features.globalSTD.PCA.GAUSS.NITER9.1D.dset')]
           
           
       return outputs
       
    
    
class train_FCD_detector_InputSpec(BaseInterfaceInputSpec):
    
    features = traits.List(desc='list of subjects smoothed feature data')
    fcd_mask = traits.List(desc='list of fcd_mask for patient postive')
    
        
class train_FCD_detector_OutputSpec(TraitedSpec):

    fcd_detector = traits.File(desc='fcd detector learned model')
    
class train_FCD_detector(BaseInterface):    
    
    input_spec = train_FCD_detector_InputSpec
    output_spec = train_FCD_detector_OutputSpec
    
    def _run_interface(self, runtime):
        
        import numpy as np
        from sklearn.decomposition import TruncatedSVD
        import joblib
        
        features = self.inputs.features
        fcd_mask = self.inputs.fcd_mask
        
            
            
        dset_dir, base, ext = split_filename(features[0])
        data_dir = os.path.dirname(dset_dir)
        subj_dir = os.path.dirname(data_dir)
        wdir = os.path.dirname(subj_dir)+'/model'
        
        data = []
        for i in range(len(fcd_mask)):
                
                feat_data = np.loadtxt(features[i], dtype=np.float32, comments='#')
    
                mask_data = np.loadtxt(fcd_mask[i], dtype=np.float32, comments='#')
            
                fcd_indx = np.ravel(mask_data == 1)
                
                feature_data = feat_data[fcd_indx,:]
                
                if len(feature_data) != 0:
                  
                    data.append(feature_data)
                   
                else:
                    continue
        
        fcds_means = np.vstack([d.mean(axis=0) for d in data])
        #SVD
        svd = TruncatedSVD(n_components=2)
        svd.fit(fcds_means)
        
        x_hat = svd.components_[0]
        y_hat = svd.components_[1]
        y_hat = -1.0*y_hat
        
        joblib.dump(x_hat, wdir+'/fcd_detector_v1')
        
        return runtime
    
         
    def _list_outputs(self): 
       import os
       outputs = self._outputs().get()
       features = self.inputs.features
       dset_dir, base, ext = split_filename(features[0])
       data_dir = os.path.dirname(dset_dir)
       subj_dir = os.path.dirname(data_dir)
       wdir = os.path.dirname(subj_dir)+'/model'
       
       outputs["fcd_detector"] = os.path.abspath(wdir+'/fcd_detector_v1')
        
        
       return outputs
    
    
class control_avg_InputSpec(BaseInterfaceInputSpec):

    features = traits.List(desc='list of control subject smoothed data')        
    control_list = traits.List(desc='list of control subjects')
    
class control_avg_outputSpec(TraitedSpec): 
    
    lh_avg = traits.File(desc='average of left hemisphere dataset')
    rh_avg = traits.File(desc='average of right hemisphere dataset')
    
class control_avg(BaseInterface):
    
    input_spec = control_avg_InputSpec
    output_spec = control_avg_outputSpec
    
    def _run_interface(self, runtime):
        
        import numpy as np
        
        
        features = self.inputs.features
        control_list = self.inputs.control_list

        dset_dir, base, ext = split_filename(features[0])
        data_dir = os.path.dirname(dset_dir)
        subj_dir = os.path.dirname(data_dir)
        dat_dir = os.path.dirname(subj_dir)+'/data/'
        
        
               
        lh_arr=[]
        rh_arr=[]
        for n,subj in enumerate(control_list):
            
            lh_feature=np.loadtxt(features[2*n])
            lh_arr.append(lh_feature)
        
            rh_feature=np.loadtxt(features[2*n+1])
            rh_arr.append(rh_feature)
        
        
        lh_data = np.array(lh_arr)
        lh_avg = np.mean(lh_data, axis=0)
        
        rh_data = np.array(rh_arr)
        rh_avg = np.mean(rh_data, axis=0)

        
        np.savetxt(dat_dir + 'lh_avg.1D.dset', lh_avg)
        np.savetxt(dat_dir + 'rh_avg.1D.dset', rh_avg)  
        
        return runtime
    
    def _list_outputs(self):
        import os
        
        outputs = self._outputs().get() 
        features = self.inputs.features
        #control_list = self.inputs.control_list
        
        dset_dir, base, ext = split_filename(features[0])
        data_dir = os.path.dirname(dset_dir)
        subj_dir = os.path.dirname(data_dir)
        dat_dir = os.path.dirname(subj_dir)+'/data'
        
        outputs["lh_avg"] = os.path.abspath(dat_dir+'/lh_avg.1D.dset')
        
        outputs["rh_avg"] = os.path.abspath(dat_dir+'/rh_avg.1D.dset')
    
        return outputs
    
class ApplyFCDdetector_InputSpec(BaseInterfaceInputSpec):
    
        
    features = traits.List(desc='list of MRI negative epilepsy patinets')
    subject_list = traits.List(desc='list of patient negatives')
    fcd_detector = traits.File(desc='the detector model learnt from pt positives')
    lh_avg = traits.File(desc='left hemishphere average file')
    rh_avg = traits.File(desc='right hemisphere average file')
    
class ApplyFCDdetector_outputSpec(TraitedSpec):
        
    data = traits.List(traits.File(desc='output left hemisphere file in the form of std.60.${hemi}.fcd_proj_{n}.1D.dset'))
    
class ApplyFCDdetector(BaseInterface):
    
    input_spec = ApplyFCDdetector_InputSpec
    output_spec = ApplyFCDdetector_outputSpec
    
    def _run_interface(self, runtime):
        
        
        import numpy as np
        import joblib
        import os
        
        x_hat = self.inputs.fcd_detector
        lh_avg = self.inputs.lh_avg
        rh_avg = self.inputs.rh_avg 
        features = self.inputs.features
        subj_list = self.inputs.subject_list
        
        

        lh_avg = np.loadtxt(lh_avg, dtype=np.float32, comments='#')
        rh_avg =  np.loadtxt(rh_avg, dtype=np.float32, comments='#')
        fcd_model = joblib.load(x_hat)

        
        for subj in subj_list:
            
            for norm in [0,1]:
                
                subject_proj = np.zeros([2, NHEMI])
                for hemi_idx, hemi in enumerate(['lh', 'rh']):
                    if hemi == 'lh':
                        mean_data = lh_avg
                    else:
                        mean_data = rh_avg
                    
                    for file in features:
                    
                        if subj in file and hemi in file:
                            
                            subj_data = np.loadtxt(file, dtype=np.float32, comments='#')
                            wdir = os.path.dirname(file)
                            proj_dir = wdir +'/projections/'
                            
                            if not os.path.exists(proj_dir):
                               os.makedirs(proj_dir)
                            
                    if norm == 0:
                        z_data = subj_data
                        
                    elif norm == 1:
                        z_data = subj_data - mean_data
                            
                    proj = np.dot(z_data, fcd_model)   
                    subject_proj[hemi_idx, :] = proj
                    np.savetxt(proj_dir + 'std.60.{}.fcd_proj_{}.1D.dset'.format(hemi, str(norm)), proj)
                  
        
        return runtime                    

    def _list_outputs(self):
        
        import os
        
        outputs = self._outputs().get() 
        features = self.inputs.features
        subj_list = self.inputs.subject_list
            
        fcd_dectector_list = []
        for subj in subj_list:
            for norm in [0,1]:
                for hemi in ['lh', 'rh']:
                    for file in features:
                        wdir = os.path.dirname(file)
                        proj_dir = wdir +'/projections/'
                        if subj in file and hemi in file:
                            fcd_dectector_list.append(os.path.join(proj_dir, 'std.60.' + hemi + '.fcd_proj_'+ str(norm) +'.1D.dset'))
                            
                            
        outputs['data'] = fcd_dectector_list             
                
        return outputs
                            
class train_FCD_detector2_InputSpec(BaseInterfaceInputSpec):
    
    features = traits.List(desc='list of subjects smoothed feature data')
    fcd_mask = traits.List(desc='list of fcd_mask for patient postive')
    lh_avg = traits.File(desc='left hemishphere average file')
    rh_avg = traits.File(desc='right hemisphere average file')
    subject_list = traits.List(desc='list of patient positives')

        
class train_FCD_detector2_OutputSpec(TraitedSpec):

    fcd_detector = traits.File(desc='fcd detector learned model')
    
class train_FCD_detector2(BaseInterface):    
    
    input_spec = train_FCD_detector2_InputSpec
    output_spec = train_FCD_detector2_OutputSpec
    
    def _run_interface(self, runtime):
        
        import numpy as np
        import joblib
        import os
        
        features = self.inputs.features
        fcd_mask = self.inputs.fcd_mask
        lh_avg = self.inputs.lh_avg
        rh_avg = self.inputs.rh_avg 
        pt_positive = self.inputs.subject_list
          
            
        lh_avg = np.loadtxt(lh_avg, dtype=np.float32, comments='#')
        rh_avg =  np.loadtxt(rh_avg, dtype=np.float32, comments='#')
        
        
        dset_dir, base, ext = split_filename(features[0])
        data_dir = os.path.dirname(dset_dir)
        subj_dir = os.path.dirname(data_dir)
        wdir = os.path.dirname(subj_dir)+'/model'

        data = []
        for i,subj in enumerate(pt_positive):

            for hemi in ['lh', 'rh']:
                if subj and hemi in features[2*i]:
                    print('processing {} data for subj {}'.format(hemi, subj))
                    feat_data = np.loadtxt(features[2*i], dtype=np.float32, comments='#')
                    mask_data = np.loadtxt(fcd_mask[2*i], dtype=np.float32, comments='#')

                    fcd_indx = np.ravel(mask_data == 1)
                    feat_data = feat_data[fcd_indx,:]
                    avg_data = lh_avg[fcd_indx,:]
                    lh_feat = feat_data - avg_data

        
                if subj and hemi in features[2*i+1]:
                    print('processing {} data for subj {}'.format(hemi, subj))
                    feat_data = np.loadtxt(features[2*i+1], dtype=np.float32, comments='#')
                    mask_data = np.loadtxt(fcd_mask[2*i+1], dtype=np.float32, comments='#')

                    fcd_indx = np.ravel(mask_data == 1)
                    feat_data = feat_data[fcd_indx,:]
                    avg_data = rh_avg[fcd_indx,:]
                    rh_feat = feat_data - avg_data
                
            both = []
            if lh_feat.shape[0] > 0:
                both.append(lh_feat)
            if rh_feat.shape[0] > 0:
                both.append(rh_feat)
        
            subj_data = np.vstack(both)
            print('subj {} data shape is {}'.format(subj, subj_data.shape))
            subj_mean = subj_data.mean(axis=0)
   
            subj_fcd_hat = subj_mean / np.linalg.norm(subj_mean)
    
            data.append(subj_fcd_hat)
            
        dd = np.vstack([d for d in data])
        vhat = np.mean(dd,axis=0)
        vhat /= np.linalg.norm(vhat)
        
        joblib.dump(vhat, wdir+'/fcd_detector')
        
        return runtime
    
         
    def _list_outputs(self): 
       import os
       outputs = self._outputs().get()
       features = self.inputs.features
       dset_dir, base, ext = split_filename(features[0])
       data_dir = os.path.dirname(dset_dir)
       subj_dir = os.path.dirname(data_dir)
       wdir = os.path.dirname(subj_dir)+'/model'
       
       outputs["fcd_detector"] = os.path.abspath(wdir+'/fcd_detector')
        
        
       return outputs


class generate_similarity_map_InputSpec(BaseInterfaceInputSpec):

    infl_surf = traits.List(desc="list of left and right hemisphere inflated surface (gifti-format)")
    proj_data = traits.List(desc="list of (un)normalized projectection vectors")
    subject_list = traits.List(desc='list of patient negatives')

class generate_similarity_map_OutputSpec(TraitedSpec):

    sim_map = traits.List(traits.File(desc='output left/right hemisphere similarity map file in the form of surf_projection_{norm}_{hemi}.html'))

class generate_similarity_map(BaseInterface):    
    
    input_spec = generate_similarity_map_InputSpec
    output_spec = generate_similarity_map_OutputSpec
    
    def _run_interface(self, runtime):
         
        import os
        import joblib
        import numpy as np
        from nilearn import plotting
        import matplotlib.pyplot as plt
        
        COOL_WARM = plt.cm.get_cmap('coolwarm')
        surface = self.inputs.infl_surf
        projection = self.inputs.proj_data
        subj_list = self.inputs.subject_list

        for subj in subj_list:
            infl_data=[]
            infl200_data=[]
            unnorm_proj=[]
            norm_proj=[]
            for item in surface:
                if subj in item and 'inflated' in item:
                    infl_data.append(item)
            for item in surface:
                if subj in item and 'inf_200' in item:
                    infl200_data.append(item)

            for proj_file in projection:
                if subj in proj_file and 'proj_0' in proj_file:               
                    unnorm_proj.append(proj_file)
                elif subj in proj_file and 'proj_1' in proj_file:
                    norm_proj.append(proj_file) 

            path = os.path.dirname(norm_proj[0])

            view = plotting.view_surf(infl_data[0],np.loadtxt(unnorm_proj[0]), cmap=COOL_WARM, bg_map=None, black_bg=True, vmax=3, title='left_inflated_surf_unnormalized_projection')
            view.save_as_html(path+'/left_inflated_surf_unnormalized_projection.html')
            view = plotting.view_surf(infl200_data[0], np.loadtxt(unnorm_proj[0]), cmap=COOL_WARM, bg_map=None, black_bg=True, vmax=3, title='left_inflated_Pial_surf_unnormalized_projection') 
            view.save_as_html(path+'/left_pial_inflated_surf_unnormalized_projection.html')
            view = plotting.view_surf(infl_data[1],np.loadtxt(unnorm_proj[1]), cmap=COOL_WARM, bg_map=None, black_bg=True, vmax=3, title='right_inflated_surf_unnormalized_projection')
            view.save_as_html(path+'/right_inflated_surf_unnormalized_projection.html')
            view = plotting.view_surf(infl200_data[1], np.loadtxt(unnorm_proj[1]), cmap=COOL_WARM, bg_map=None, black_bg=True, vmax=3, title='right_inflated_Pial_surf_unnormalized_projection') 
            view.save_as_html(path+'/right_pial_inflated_surf_unnormalized_projection.html')
            view = plotting.view_surf(infl_data[0],np.loadtxt(norm_proj[0]), cmap=COOL_WARM, bg_map=None, black_bg=True, vmax=3, title='left_inflated_surf_normalized_projection')
            view.save_as_html(path+'/left_inflated_surf_normalized_projection.html')
            view = plotting.view_surf(infl200_data[0], np.loadtxt(norm_proj[0]), cmap=COOL_WARM, bg_map=None, black_bg=True, vmax=3, title='left_inflated_Pial_surf_normalized_projection') 
            view.save_as_html(path+'/left_pial_inflated_surf_normalized_projection.html')
            view = plotting.view_surf(infl_data[1],np.loadtxt(norm_proj[1]), cmap=COOL_WARM, bg_map=None, black_bg=True, vmax=3, title='right_inflated_surf_normalized_projection')
            view.save_as_html(path+'/right_inflated_surf_normalized_projection.html')
            view = plotting.view_surf(infl200_data[1], np.loadtxt(norm_proj[1]), cmap=COOL_WARM, bg_map=None, black_bg=True, vmax=3, title='right_inflated_Pial_surf_normalized_projection') 
            view.save_as_html(path+'/right_pial_inflated_surf_normalized_projection.html')

        return runtime

    def _list_outputs(self):

        import os

        outputs = self._outputs().get()
        projection = self.inputs.proj_data
        subj_list = self.inputs.subject_list

        html_list = [] 
        for subj in subj_list:
            for proj_file in projection:
                if subj in proj_file:
                    subj_path = os.path.dirname(proj_file)
            i=0
            surface = ['inflated', 'pial_inflated']
            norm = ['unnorm', 'norm']
            hemi = ['lh', 'rh']
            
            html_list.append(os.path.join(subj_path+'/'+hemi[i]+'_'+surface[i]+'_surf_'+norm[i]+'_projection.html'))
            html_list.append(os.path.join(subj_path+'/'+hemi[i]+'_'+surface[i]+'_surf_'+norm[i+1]+'_projection.html'))
            html_list.append(os.path.join(subj_path+'/'+hemi[i]+'_'+surface[i+1]+'_surf_'+norm[i]+'_projection.html'))
            html_list.append(os.path.join(subj_path+'/'+hemi[i]+'_'+surface[i+1]+'_surf_'+norm[i+1]+'_projection.html'))
            html_list.append(os.path.join(subj_path+'/'+hemi[i+1]+'_'+surface[i]+'_surf_'+norm[i]+'_projection.html'))
            html_list.append(os.path.join(subj_path+'/'+hemi[i+1]+'_'+surface[i]+'_surf_'+norm[i+1]+'_projection.html'))
            html_list.append(os.path.join(subj_path+'/'+hemi[i+1]+'_'+surface[i+1]+'_surf_'+norm[i]+'_projection.html'))
            html_list.append(os.path.join(subj_path+'/'+hemi[i+1]+'_'+surface[i+1]+'_surf_'+norm[i+1]+'_projection.html'))

        outputs['sim_map'] = html_list

        return outputs
            