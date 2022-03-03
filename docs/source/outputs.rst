.. _outputs:

---------------------
Outputs of *fcdproc*
---------------------

*fcdproc* generates 3 classes of outcomes:

1. ** Derivative (preprocessed data)** 

2. ** Model & data ** includes PCA, GAUSS, FCD-detector models as well as Average Controls data from both hemispheres 

3. ** Projections ** 8 :abbr:`HTML (hypertext markup language)` reports per MRI(-) subject, indicating 
similarity map on top of inflated pial surface.


Preprocessed Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Preprocessed and derivative (output) data are written to ``<output dir>/fcdproc/<subject_label>/`` ::
    
    <output_dir>/
      fcdproc/
        <subject_label>/
          data/
              std.60.<subject_label>_both.spec/
              std.60.<subject_label>_[LR].spec/
              std.60.[LR].pial.gii\
              std.60.[LR].white.gii\
              std.60.[LR].sphere.gii\
              std.60.[LR].sphere.reg.gii\
              std.60.[LR].smoothwm.gii\
              std.60.[LR].inflated.gii\
              std.60.[LR].inf_200.gii\
              std.60.[LR].aparc.a2009s.annot.niml.dset\
              SurfVol_Alnd+orig.(BRIK/HEAD)\
              T1_axialize.nii.gz\
              dset/
                std.60.[LR].curve.1D.dset/
                std.60.[LR].sulc.1D.dset/
                std.60.[LR].sel_ctx.1D.dset/
                std.60.[LR].thickness.fwhm5.1D.dset/
                std.60.[LR].w-g.pct.fwhm5.1D.dset/
                std.60.[LR].T1_features.1D.dset/
                std.60.[LR].T2_features.1D.dset/
                std.60.[LR].FL_features.1D.dset/
                std.60.[LR].features.1D.dset/
                std.60.[LR].features.globalSTD.1D.dset/
                std.60.[LR].features.globalSTD.PCA.1D.dset/
                std.60.[LR].features.globalSTD.PCA.GAUSS.NITER{1..10}.1D.dset/
                std.60.[LR].features.globalSTD.PCA.GAUSS.fwhm10.1D.dset/


Normative Data & FCD-Detector Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Models and normative data are written to ``<output dir>/fcdproc/`` ::

    <output_dir>/
      fcdproc/
        data/
          globalSTD.PCA/
          features.globalSTD.PCA.GAUSS.NITER{1..10}/
          lh_avg.1D.dset/
          rh_avg.1D.dset/
        model/
          PCA.globalSTD/
          GAUSS.NITER{1..10}.features.globalSTD.PCA\
          fcd_detector\


Projections
~~~~~~~~~~~~
Similarity map of MRI negative patients are written to 
``<output dir>/fcdproc/<subject_label>/data/dset/projections/`` ::

    <output_dir>/
      fcdproc/
        <subject_label>/
          data/
            dset/
              projections/
                std.60.[LR].fcd_proj_{0,1}.1D.dset/
                [LR]_[inflated/pial_inflated]_surf_[normalized/unnormalized]_projection.html/