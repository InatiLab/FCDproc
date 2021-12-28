# fcdproc

Python package to detect FCD lesions in MRI negative epilepsy patients

## Installation

```bash
$ pip install fcdproc
```

## Usage

Usage: fcdproc [OPTIONS]

Options:
  --version                       Show the version and exit.
  --work_dir TEXT                 working directory  [required]
  --analysis_mode [preprocess|model|detect]
  --participant_label TEXT        subject id to be processed (the sub- prefix
                                  can be removed)
  --controls TEXT                 list of control subject with normal brains
  --pt_positive TEXT              list of patients with known fcd lesions
  --pt_negative TEXT              list of patients with MRI negative fcd
                                  lesions
  --fs_reconall / --fs_no_reconall
                                  option to run freesurfer reconstruction
  --fs_subjects_dir TEXT          path to existing subjects directory to reuse
                                  (default: OUTPUT_DIR/freesurfer)
  --fs_license_file TEXT          path to Freesurfer licencse key file
  --clean_workdir                 Clears working directory of contents to save
                                  some space on user OS
  --output_dir TEXT               output data directory  [required]
  --bids_dir TEXT                 inputs BIDS data directory  [required]
  -h, --help                      Show this message and exit.



## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`fcdproc` was created by InatiLab. It is licensed under the terms of the GNU General Public License v3.0 license.

## Credits
