import os
import subprocess
from warnings import warn

from ln2t_tools.utils.defaults import DEFAULT_RAWDATA

def list_available_datasets():
    [print(name[:-8]) for name in os.listdir(DEFAULT_RAWDATA) if name.endswith("-rawdata")]


def list_missing_subjects(rawdata_dir: str, output_dir: str):
    if not os.path.isdir(rawdata_dir):
        print(f"Error: {rawdata_dir} does not exist.")
        return

    os.makedirs(output_dir, exist_ok=True)

    raw_sub_folders = [name for name in os.listdir(rawdata_dir) if os.path.isdir(os.path.join(rawdata_dir, name)) and name.startswith("sub-")]
    output_sub_folders = [name for name in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, name)) and name.startswith("sub-")]

    print(f"Folders in {rawdata_dir} that are not in {output_dir}:")
    for folder in raw_sub_folders:
        if folder not in output_sub_folders:
            print(folder)


def check_apptainer_is_installed(apptainer_cmd: str):
    if not os.path.isfile(apptainer_cmd):
        print(f"Apptainer not found at {apptainer_cmd}, are you sure it is installed?")
        exit(1)


def ensure_image_exists(apptainer_dir: str, tool: str, version: str):
    if tool == "freesurfer":
        file_path = os.path.join(apptainer_dir, f"freesurfer.freesurfer.{version}.sif")
        create_command = f"apptainer build {file_path} docker://freesurfer/freesurfer:{version}"
    elif tool == "fmriprep":
        file_path = os.path.join(apptainer_dir, f"nipreps.fmriprep.{version}.sif")
        create_command = f"apptainer build {file_path} docker://nipreps/fmriprep:{version}"
    else:
        print(f"Unknown tool: {tool}")
        exit(1)

    if not os.path.isfile(file_path):
        print(f"File {file_path} does not exist. Creating it...")
        os.makedirs(apptainer_dir, exist_ok=True)
        subprocess.run(create_command, shell=True, check=True)
        print(f"File {file_path} created successfully.")
    else:
        print(f"File {file_path} already exists.")

    return file_path


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
    t1w_list = layout.get(sub=participant_label,
                          scope="rawdata",
                          suffix="T1w",
                          return_type="filename",
                          extension=".nii.gz")

    if len(t1w_list) > 1:
        warn(f"Found more than one (actually, "
             f"{len(t1w_list)}) T1w images for subject "
             f"{participant_label}: {t1w_list}"
             f"The tools does not support this very well yet, and we will only process the first image.")

    return t1w_list

def get_flair_list(layout, participant_label):
    flair_list = layout.get(sub=participant_label,
                          scope="rawdata",
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
    subprocess.run(apptainer_cmd, shell=True, check=True)

