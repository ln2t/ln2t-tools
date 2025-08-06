import os

# Default variables
DEFAULT_APPTAINER_DIR = "/opt/apptainer"
DEFAULT_FS_VERSION = "7.3.2"
DEFAULT_FMRIPREP_VERSION = "25.1.4"
DEFAULT_FS_LICENSE = "/opt/freesurfer/.license"
DEFAULT_RAWDATA = os.path.join(os.environ['HOME'], "rawdata")
DEFAULT_DERIVATIVES = os.path.join(os.environ['HOME'], "derivatives")