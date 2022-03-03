# -*- coding: utf-8 -*-


import click
import ast
import os
import sys
from copy import deepcopy
import numpy as  np
from fcdproc.workflow.base import Main_FCD_pipeline
from pkg_resources import get_distribution, DistributionNotFound
from warnings import simplefilter
# ignore all future warnings
simplefilter(action='ignore', category=FutureWarning)

try:
    __version__ = get_distribution("fcdproc").version
except DistributionNotFound:
     # package is not installed
    pass
            
            
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=__version__)
@click.option('--analysis_mode', type=click.Choice(['preprocess', 'model', 'detect'], case_sensitive=False))
@click.option('--work_dir', type=click.STRING , help='Working directory', required=True)
@click.option('--output_dir', type=click.STRING , help='Output data directory',required=True)
@click.option('--bids_dir', type=click.STRING , help='BIDS data directory',required=True)
@click.option('--participant_label', type=click.STRING, default='', help="Preprocess: Subject id to be processed (the 'sub-' prefix can be removed)")
@click.option('--fs_reconall/--fs_no_reconall', default=False, help='Preprocess: Option to run freesurfer reconstruction')
@click.option('--fs_subjects_dir', type=click.STRING , is_flag=False, default="freesurfer", help='Preprocess: Path to existing subject freesurfer directory (default: OUTPUT_DIR/freesurfer)')
@click.option('--fs_license_file', type=click.STRING , help='Preprocess: Path to freesurfer license key file')
@click.option('--clean_workdir', is_flag=True, help='Preprocess: Clear working directory of contents to save space on user OS')
@click.option('--controls', type=click.STRING, default='', help="Model: List of control subject with normal brains; example format: '[1,5]'")
@click.option('--pt_positive', type=click.STRING, default='', help='Model: List of patients with known FCD lesions')
@click.option('--pt_negative', type=click.STRING, default='', help="Model/Detect: List of MRI negative patients (default: '[]')")


def fcdproc(analysis_mode, bids_dir, output_dir, work_dir, participant_label, controls, pt_positive, pt_negative, fs_reconall, fs_license_file, fs_subjects_dir, clean_workdir):
    """ Create fcd pipeline that can perform single subject processing, modeling and detecting of FCD lesion"""
    
    
    click.echo(f"performing {analysis_mode} analysis")
    #pylint: disable=too-many-arguments
    pipeline = Main_FCD_pipeline(bids_dir, output_dir, work_dir, analysis_mode, participant_label, controls, pt_positive, pt_negative, fs_reconall, fs_license_file, fs_subjects_dir, clean_workdir)
    pipeline.run()
    