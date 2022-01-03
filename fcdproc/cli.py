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

class PythonLiteralOption(click.Option):

    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except:
            raise click.BadParameter(value)
            
            
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=__version__)
@click.option('--work_dir', type=click.STRING , help='working directory', required=True)
@click.option('--analysis_mode', type=click.Choice(['preprocess', 'model', 'detect'], case_sensitive=False))
@click.option('--participant_label', type=click.STRING, default='', help='subject id to be processed (the sub- prefix can be removed)')
@click.option('--controls', cls=PythonLiteralOption, default=[], help='list of control subject with normal brains')
@click.option('--pt_positive', cls=PythonLiteralOption, default=[], help='list of patients with known fcd lesions')
@click.option('--pt_negative', cls=PythonLiteralOption, default=[], help='list of patients with MRI negative fcd lesions')
@click.option('--fs_reconall/--fs_no_reconall', default=False, help='option to run freesurfer reconstruction')
@click.option('--fs_subjects_dir', type=click.STRING , is_flag=False, default="freesurfer", help='path to existing subjects directory to reuse (default: OUTPUT_DIR/freesurfer)')
@click.option('--fs_license_file', type=click.STRING , help='path to Freesurfer licencse key file')
@click.option('--clean_workdir', is_flag=True, help='Clears working directory of contents to save some space on user OS')
@click.option('--output_dir', type=click.STRING , help='output data directory',required=True)
@click.option('--bids_dir', type=click.STRING , help='inputs BIDS data directory',required=True)


def fcdproc(bids_dir, output_dir, work_dir, analysis_mode, participant_label, controls, pt_positive, pt_negative, fs_reconall, fs_license_file, fs_subjects_dir, clean_workdir):
    """ Create fcd pipeline that can perform single subject processing, modeling and detecting of FCD lesion"""
    
    
    click.echo(f"performing {analysis_mode} analysis")
    #pylint: disable=too-many-arguments
    pipeline = Main_FCD_pipeline(bids_dir, output_dir, work_dir, analysis_mode, participant_label, controls, pt_positive, pt_negative, fs_reconall, fs_license_file, fs_subjects_dir, clean_workdir)
    pipeline.run()
    