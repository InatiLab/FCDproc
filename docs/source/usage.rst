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
This Pipeline can be run in 3 steps:

step1: preprocess: ::

    fcdproc --analysis_mode 'preprocess'  --work_dir <path> --output_dir <path> --bids_dir <path> --participant_label {subj_id}
            [--fs_reconall/fs_no_reconall] --fs_subjects_dir  --fs_license_file --clean_workdir

* In the preprocessing step, you will need to type in subject_id without the 'sub-' prefix for --participant_label option.
* If you have pre-run freesurfer, you can choose '--fs_no_reconall' as well as copying the freesurfer results under OUTPUT_DIR/freesurfer/
* The fs_license_file is the license.txt file that is saved where you have saved your freesurfer software package.
* Since the working directory can take up to 25GB of your computer space, we added --clean_workdir option that allows 
the user delete the intermediate results.

step2: Model: ::
    fcdproc --analysis_mode 'model' --work_dir <path> --output_dir <path> --bids_dir <path>
            --controls '[01,02,...,30]'  --pt_poitive '[31,32,...,40]' --pt_negative '[41,42,...,45]'

* In the modeling step, you will train a PCA reduction, guassianization, and fcd detector model.
* By end of this steps, you should be able to see data & model directories created under your <output_dir> path.
* If you have included your pt_negative list, at this stage you will be able to see the dection results under <output_dir>/ fcdproc/$subj/data/dset/projections/      

step3: Detect: ::
    fcdproc --analysis_mode 'detect' --work_dir <path> --output_dir <path> --bids_dir <path> --pt_negative '[50,51,52]'

* After training your fcd model, whenever you get a new MRI negative patient, you will have to run them through preprocess step1 and then step3
* This step will create the brain abnormality projections under <output_dir>/ fcdproc/$subj/data/dset/projections/ 

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

