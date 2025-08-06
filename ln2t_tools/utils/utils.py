import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from warnings import warn

from bids import BIDSLayout

from ln2t_tools.utils.defaults import (
    DEFAULT_RAWDATA,
    DEFAULT_DERIVATIVES
)

logger = logging.getLogger(__name__)

def check_apptainer_is_installed(apptainer_path: str = "/usr/bin/apptainer") -> None:
    """Verify Apptainer is installed and accessible.
    
    Args:
        apptainer_path: Path to apptainer executable
        
    Raises:
        FileNotFoundError: If apptainer is not found
    """
    if not shutil.which(apptainer_path):
        raise FileNotFoundError(
            f"Apptainer not found at {apptainer_path}. "
            "Please install Apptainer first."
        )

def ensure_image_exists(
    apptainer_dir: Path,
    tool: str,
    version: str
) -> Path:
    """Ensure Apptainer image exists and return its path.
    
    Args:
        apptainer_dir: Directory containing Apptainer images
        tool: Tool name ('freesurfer' or 'fmriprep')
        version: Tool version
        
    Returns:
        Path to Apptainer image
        
    Raises:
        FileNotFoundError: If image not found
    """
    if tool == "freesurfer":
        tool_owner = "freesurfer"
    elif tool == "fmriprep":
        tool_owner = "nipreps"
    else:
        raise ValueError(f"Unsupported tool: {tool}")
    image_path = apptainer_dir / f"{tool_owner}.{tool}.{version}.sif"
    if not image_path.exists():
        logger.warning(
            f"Apptainer image not found: {image_path}\n"
            f"Attempting to build the {tool} version {version} image..."
        )
        build_cmd = (
            f"apptainer build {image_path} docker://{tool_owner}/{tool}:{version}"
        )
        result = os.system(build_cmd)
        if result != 0 or not image_path.exists():
            raise FileNotFoundError(
                f"Failed to build Apptainer image: {image_path}\n"
                f"Please check Apptainer installation and Docker image availability."
            )
    return image_path

def list_available_datasets() -> None:
    """List available BIDS datasets in rawdata directory."""
    available = [name[:-8] for name in os.listdir(DEFAULT_RAWDATA) 
                if name.endswith("-rawdata")]
    
    if not available:
        logger.info(f"No datasets found in {DEFAULT_RAWDATA}")
        return
    
    logger.info("Available datasets:")
    for dataset in available:
        logger.info(f"  - {dataset}")

def list_missing_subjects(
    rawdata_dir: Path,
    output_dir: Path
) -> None:
    """List subjects present in rawdata but missing from output.
    
    Args:
        rawdata_dir: Path to BIDS rawdata directory
        output_dir: Path to derivatives output directory
    """
    raw_layout = BIDSLayout(rawdata_dir)
    raw_subjects = set(raw_layout.get_subjects())
    
    processed_subjects = {
        d.name[4:] for d in output_dir.glob("sub-*")
        if d.is_dir()
    }
    
    missing = raw_subjects - processed_subjects
    if missing:
        logger.info("Missing subjects:")
        for subject in sorted(missing):
            logger.info(f"  - {subject}")
    else:
        logger.info("No missing subjects found")

def check_file_exists(file_path: str):
    if not os.path.isfile(file_path):
        print(f"File {file_path} does not exist.")
        return False
    else:
        print(f"File {file_path} found.")
        return True


def check_participants_exist(layout, participant_list):
    """Check if participants exist in the BIDS layout.
    
    Args:
        layout: BIDSLayout object
        participant_list: List of participant labels or None to use all participants
    
    Returns:
        list: List of valid participant labels
    """
    if not participant_list:
        # If no participants specified, use all available in the dataset
        return layout.get_subjects()
        
    true_participant_list = []
    for participant in participant_list:
        if participant in layout.get_subjects():
            true_participant_list.append(participant)
        else:
            warn(f"Participant {participant} not found in the dataset, removing from the list.")

    if not true_participant_list:
        raise ValueError("No valid participants found in the dataset.")

    return true_participant_list


def get_t1w_list(layout, participant_label):
    t1w_list = layout.get(subject=participant_label,
                          scope="raw",
                          suffix="T1w",
                          return_type="filename",
                          extension=".nii.gz")

    return t1w_list

def get_flair_list(layout, participant_label):
    flair_list = layout.get(subject=participant_label,
                          scope="raw",
                          suffix="FLAIR",
                          return_type="filename",
                          extension=".nii.gz")

    if len(flair_list):
        warn(f"Found FLAIR images. Ignoring them (for now).")

    return flair_list


def build_apptainer_cmd(tool, **options):
    """Build Apptainer command for different neuroimaging tools.
    
    Args:
        tool (str): Tool name ('freesurfer' or 'fmriprep')
        **options: Dictionary containing required parameters
            - fs_license: Path to FreeSurfer license file
            - rawdata: Path to BIDS rawdata directory
            - derivatives: Path to derivatives directory
            - apptainer_img: Path to Apptainer image
            - participant_label: Subject ID
            - output_label: Output directory name
            - session: Optional session ID
            - run: Optional run number
            - flair_option: Optional FLAIR processing arguments
    
    Returns:
        str: Formatted Apptainer command
    """
    if tool == "freesurfer":
        if "fs_license" not in options:
            raise ValueError("FreeSurfer license file path is required")
        
        # Build subject ID with session and run if present
        subject_id = f"sub-{options['participant_label']}"
        if options.get('session'):
            subject_id += f"_ses-{options['session']}"
        if options.get('run'):
            subject_id += f"_run-{options['run']}"
            
        return (
            f"apptainer run -B {options['fs_license']}:/usr/local/freesurfer/.license "
            f"-B {options['rawdata']}:/rawdata -B {options['derivatives']}:/derivatives "
            f"{options['apptainer_img']} recon-all -all -subjid {subject_id} "
            f"-i {options['t1w']} "
            f"-sd /derivatives/{options['output_label']} {options.get('flair_option', '')}"
        )
    elif tool == "fmriprep":
        return (
            f"apptainer run -B {options['rawdata']}:/rawdata -B {options['derivatives']}:/derivatives "
            f"{options['apptainer_img']} /rawdata /derivatives/fmriprep participant "
            f"--participant-label {options['participant_label']} "
            f"--output-spaces MNI152NLin2009cAsym:res-2"
        )
    else:
        raise ValueError(f"Unsupported tool: {tool}")


def launch_apptainer(apptainer_cmd):
    print(f"Launching apptainer image {apptainer_cmd}")
    os.system(build_cmd)

