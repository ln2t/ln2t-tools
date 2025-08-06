"""Default values and constants for ln2t_tools."""
from pathlib import Path

# Default directories
DEFAULT_RAWDATA = Path.home() / Path("rawdata")
DEFAULT_DERIVATIVES = Path.home() / Path("derivatives")
DEFAULT_APPTAINER_DIR = Path("/opt/apptainer")

# Tool versions
DEFAULT_FS_VERSION = "7.3.2"
DEFAULT_FMRIPREP_VERSION = "23.1.3"

# FreeSurfer license
DEFAULT_FS_LICENSE = Path("/opt/freesurfer/license.txt")