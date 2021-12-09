from os import path
from setuptools import setup, find_packages
import sys
import subprocess



# NOTE: This file must remain Python 2 compatible for the foreseeable future,
# to ensure that we error out properly for people with outdated setuptools
# and/or pip.
min_version = (3, 6)
if sys.version_info < min_version:
    error = """
fcdproc does not support Python {0}.{1}.
Python {2}.{3} and above is required. Check your Python version like so:
python3 --version
This may be due to an out-of-date pip. Make sure you have pip >= 9.0.1.
Upgrade pip like so:
pip install --upgrade pip
""".format(
        *sys.version_info[:2], *min_version
    )
    sys.exit(error)

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open(path.join(here, "requirements.txt")) as requirements_file:
    # Parse requirements.txt, ignoring any commented-out lines.
    requirements = [
        line
        for line in requirements_file.read().splitlines()
        if not line.startswith("#")
    ]

try:
    from semantic_release import setup_hook
    setup_hook(sys.argv)
except ImportError:
    pass

__version__='0.0.15'
setup(
    name="fcdproc",
    version= __version__,
    description="Python package for FCD lesion detection.",
    long_description=readme,
    author="Inati Lab, NINDS, NIH",
    author_email="shervin.abd71@gmail.com",
    url="https://github.com/ShervinAbd92/fcdproc",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "Create_FCD_Pipeline=fcdproc.cli:Create_FCD_Pipeline"
        ]
    },
    include_package_data=True,
    package_data={
        'fcdproc': ['data/__files/*.annot', 'data/__files/*.txt', 'data/__files/TT_N27.nii']
    },
    install_requires=requirements,
    license="Public Domain",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
    ],
)

