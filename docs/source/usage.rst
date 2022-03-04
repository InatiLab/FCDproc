.. include:: links.rst

.. _Usage :

Usage Notes
===========


Execution and the BIDS format
-----------------------------
The *fcdproc* workflow takes as principal input the path of the dataset
that is to be processed.
The input dataset is required to be in valid :abbr:`BIDS (Brain Imaging Data
Structure)` format.
We highly recommend that you validate your dataset with the free, online
`BIDS Validator <http://bids-standard.github.io/bids-validator/>`_.

The common parts of the command follow the `BIDS-Apps
<https://github.com/BIDS-Apps>`_ definition.
Example: ::

    fcdproc --work_dir work/ --output_dir out/ --bids_dir  data/bids_root/ 

Further information about BIDS and BIDS-Apps can be found at the
`NiPreps portal <https://www.nipreps.org/apps/framework/>`__.

Command-Line Arguments
----------------------
This pipeline can be run in 3 steps:

Step 1 - Preprocess: ::

    fcdproc --analysis_mode 'preprocess'  --work_dir <path> --output_dir <path> --bids_dir <path> --participant_label {subj_id}
            [--fs_reconall/fs_no_reconall] --fs_subjects_dir  --fs_license_file --clean_workdir

* In the preprocessing step, you will need to type in subject_id without the 'sub-' prefix for the --participant_label option.
* If you have pre-run FreeSurfer, include option '--fs_no_reconall' after copying the FreeSurfer results under ``OUTPUT_DIR/freesurfer/``
* The fs_license_file is the license.txt file included in your FreeSurfer directory.
* Users should ensure that all FCD+ patients have a resection mask at ``<bids_dir>/mask/$subj/fcd.msk.nii``. For the user's convenience, an automated resection mask tool has been created by InatiLab at
    https://github.com/InatiLab/RsxnMskProc.git
* Since the working directory can take up to 25GB of your computer space, you may use the --clean_workdir option to delete intermediate results.

Step 2 - Model: ::

    fcdproc --analysis_mode 'model' --work_dir <path> --output_dir <path> --bids_dir <path>
            --controls '[01,02,24,30]'  --pt_positive '[31,40]' --pt_negative '[45]'

* In the modeling step, users train a PCA reduction, gaussianization, and FCD detector model.
* The established model used in publication was trained using 30 normal controls and 10 FCD+ patients.
* Outputs of this step include both data & model directories created under ``<output_dir>`` path.
* If you have included a pt_negative list, detection results will be stored at ``<output_dir>/fcdproc/$subj/data/dset/projections/``

Step 3 - Detect: ::

    fcdproc --analysis_mode 'detect' --work_dir <path> --output_dir <path> --bids_dir <path> --pt_negative '[50,51,52]'

* After training your fcd model, new MRI negative patients are run using step 1 (preprocess) followed by step 3 (detect).
* This step creates brain abnormality projections under ``<output_dir>/fcdproc/$subj/data/dset/projections/`` 

The FreeSurfer license
----------------------
*fcdproc* uses FreeSurfer tools, which require a license to run.

To obtain a FreeSurfer license, simply register for free at
https://surfer.nmr.mgh.harvard.edu/registration.html.

When using manually-prepared environments or singularity, FreeSurfer will search
for a license key file first using the ``$FS_LICENSE`` environment variable and then
in the default path to the license key file (``$FREESURFER_HOME/license.txt``).

Using a previous run of *FreeSurfer*
------------------------------------
*fcdproc* will automatically reuse previous runs of *FreeSurfer* if a subject directory
named ``freesurfer/`` is found in the output directory (``<output_dir>/freesurfer``).
Reconstructions for each participant will be checked for completeness, and any missing
components will be recomputed.
You can use the ``--fs_subjects_dir`` flag to specify a different location to save
FreeSurfer outputs.
If precomputed results are found, they will be reused.


**Support and communication**.
All bugs, concerns and enhancement requests for this software can be submitted here:
https://github.com/InatiLab/fcdproc/issues.

