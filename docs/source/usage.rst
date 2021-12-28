.. include:: links.rst

.. _Usage :

Usage Notes
===========


Execution and the BIDS format
-----------------------------
The *fcdproc* workflow takes as principal input the path of the dataset
that is to be processed.
The input dataset is required to be in valid :abbr:`BIDS (Brain Imaging Data
Structure)` format, and it must include at least one T1w structural image and
(unless disabled with a flag) a BOLD series.
We highly recommend that you validate your dataset with the free, online
`BIDS Validator <http://bids-standard.github.io/bids-validator/>`_.

The exact command to run *fcdproc* depends on the Installation_ method.
The common parts of the command follow the `BIDS-Apps
<https://github.com/BIDS-Apps>`_ definition.
Example: ::

    fcdproc --work_dir work/ --output_dir out/ --bids_dir  data/bids_root/ 

Further information about BIDS and BIDS-Apps can be found at the
`NiPreps portal <https://www.nipreps.org/apps/framework/>`__.

Command-Line Arguments
----------------------

.. click:: fcdproc.cli:fcdproc 
   :prog: fcdproc
   :nested: full
   

.. _fs_license:

The FreeSurfer license
----------------------
*fcdproc* uses FreeSurfer tools, which require a license to run.

To obtain a FreeSurfer license, simply register for free at
https://surfer.nmr.mgh.harvard.edu/registration.html.

When using manually-prepared environments or singularity, FreeSurfer will search
for a license key file first using the ``$FS_LICENSE`` environment variable and then
in the default path to the license key file (``$FREESURFER_HOME/license.txt``).

.. _prev_derivs:

Using a previous run of *FreeSurfer*

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*fcdproc* will automatically reuse previous runs of *FreeSurfer* if a subject directory
named ``freesurfer/`` is found in the output directory (``<output_dir>/freesurfer``).
Reconstructions for each participant will be checked for completeness, and any missing
components will be recomputed.
You can use the ``--f_subjects_dir`` flag to specify a different location to save
FreeSurfer outputs.
If precomputed results are found, they will be reused.


**Support and communication**.
All bugs, concerns and enhancement requests for this software can be submitted here:
https://github.com/InatiLab/fcdproc/issues.

