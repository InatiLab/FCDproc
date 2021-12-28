.. include:: links.rst

===========================
Processing pipeline details
===========================

*fcdproc* is comprised of 3 levels: Preprocessing, Modeling, and Detection

Preprocessing of structural MRI
-------------------------------
The anatomical sub-workflow expects 3 MRI contrasts as its inputs (T1, T2, and FALIR). then it performs the follwoing steps:

* T1 axialization with respect to TT_N27 template ``placed under $bids_dir/__files/TT_N27.nii``
* T2 and FLAIR coregistration to T1
* subject specific intensity normalization
* feature generation
* surface reconstruction **(fs-suma)-details in the follwoing section**
* surface feature normalization

.. figure:: _static/Single_Subject_with_FCD_mask.png

.. note:: 
    for FCD positive patients who have their fcd_mask dervied from the original input T1, please place them under
    $bids_dir/mask/$subject_id/fcd.msk.nii. The single subject workflow would then coregisters the input T1 to the
    axialized T1, apply the transformation metrix to the fcd.msk.nii to get it in alignment with T1 and then maps 
    them from volume domain to surface domain.
    

The fs-suma workflow perform freesurfer's reconall to reconstruct the brain surface from T1 and T2 structural images.
If enabled, several steps in the *fcdproc* pipeline are added or replaced.
All surface reconstruction may be disabled with the ``--fs_no_reconall`` flag.

In order to bypass reconstruction in *fcdproc*, place existing reconstructed
subjects in ``<output dir>/freesurfer`` prior to the run, or specify an external
subjects directory with the ``--fs_subjects_dir`` flag.
*fcdproc* will perform any missing ``recon-all`` steps, and continue with SUMA to convert 
the cortical surface into AFNI-based fromat.

.. figure:: _static/Freesurfer_SUMA_wf.png

Normative Modeling
------------------
We perfrom the following steps to train our FCD-detector model:

* dimensionality reduction of the initial feature vectors across HVs to components required to explain 90% of the variance ``PCA``
* iterative non-linear gaussianization to obtain a multivariate normal distribution of features ``GAUSS``
* surface-based smoothing and averaging of features across HVs at each vertex on the gray-white junction surface ``control_avg``
* The same features were computed at each vertex within the training FCD masks in MRI+ patients to generate a normalized average FCD feature vector ``fcd_detector``


.. figure:: _static/Modeling.png

FCD Lesion Detection
--------------------
At this step, smoothed normalized features at each vertex were projected onto the FCD average unit vector,
allowing for estimation of similarity to FCDs, then corrected for the expected appearance at each vertex. 

.. figure:: _static/Detection.png