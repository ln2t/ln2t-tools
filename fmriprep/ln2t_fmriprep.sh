#!/bin/bash

# Default variables
DEFAULT_APPTAINER_DIR="/opt/apptainer"
DEFAULT_VERSION="25.1.4"
DEFAULT_FREESURFER_VERSION="7.3.2"  # This is the version used in fMRIPrep 25.1.4 and we must have this to re-use pre-computed stuff
DEFAULT_FS_LICENSE="/opt/freesurfer/.license"
DEFAULT_RAWDATA="$HOME/rawdata"
DEFAULT_DERIVATIVES="$HOME/derivatives"

# Apptainer variables
APPTAINER_CMD="/usr/bin/apptainer"
APPTAINER_OPT="--nv --cleanenv"

# Display usage information
usage() {
    echo "Usage: $0 [--list-datasets] \
                    [--dataset dataset] \
                    [--output-label output_label] \
                    [--fs-license fs_license] \
                    [--apptainer-dir apptainer_dir] \
                    [--version version] \
                    [--participant-label participant_label] \
                    [--list-missing] \
                    [--more more_options]"
    exit 1
}

# Check apptainer program is installed
check_apptainer_is_installed() {
  if [ ! -f "${APPTAINER_CMD}" ]; then
    echo "Apptainer not found at ${APPTAINER_CMD}, are your sure it is installed?"
    exit 1
  fi
}

# Ensure apptainer image exists. If not, creates it.
ensure_image_exists() {
    local apptainer_dir="$1"
    local version="$2"
    local file_path="${apptainer_dir}/nipreps.fmriprep.${version}.sif"
    local create_command="${APPTAINER_CMD} build ${file_path} docker://nipreps/fmriprep:${version}"

    if [ ! -f "$file_path" ]; then
        echo "File $file_path does not exist. Creating it..."
        mkdir -p "${DEFAULT_APPTAINER_DIR}"
        eval "$create_command"
        if [ $? -eq 0 ]; then
            echo "File $file_path created successfully."
        else
            echo "Failed to create file $file_path."
            exit 1
        fi
    else
        echo "File $file_path already exists."
    fi

    APPTAINER_IMG="${file_path}"
}

# Generic function to check that a file exists and exit if not
check_file_exists() {
    local file_path="$1"
    if [ ! -f "$file_path" ]; then
      echo "File $file_path does not exist. Abording..."
      exit 1
    else
        echo "File $file_path found."
    fi
}

# List directory content
show_dir_content() {
  local directory=$1
  echo "Listing contents of ${directory}:"
  ls ${directory}
}

# Function to compare folders
compare_folders() {
    local rawdata_dir="$1"
    local output_dir="$2"

    # Check if the directories exist
    if [ ! -d "$rawdata_dir" ]; then
        echo "Error: $rawdata_dir does not exist."
        return 1
    fi

    if [ ! -d "$output_dir" ]; then
        echo "Error: $output_dir does not exist."
        return 1
    fi

    # Find sub-folders in rawdata that start with "sub-"
    local raw_sub_folders
    raw_sub_folders=($(find "$rawdata_dir" -maxdepth 1 -type d -name "sub-*" -printf "%f\n"))

    # Find sub-folders in output that start with "sub-"
    local output_sub_folders
    output_sub_folders=($(find "$output_dir" -maxdepth 1 -type d -name "sub-*" -printf "%f\n"))

    # Compare and print folders in rawdata that are not in output
    echo "Folders in $rawdata_dir that are not in $output_dir:"
    for folder in "${raw_sub_folders[@]}"; do
        if [[ ! " ${output_sub_folders[@]} " =~ " $folder " ]]; then
            echo "$folder"
        fi
    done
}

# Initialize variables
list_datasets=false
dataset=""
fs_license="${DEFAULT_FS_LICENSE}"
apptainer_dir="${DEFAULT_APPTAINER_DIR}"
version="${DEFAULT_VERSION}"
output_label="fmriprep_${version}"
more_options=""
list_missing=false

# Parse command line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --list-datasets)
            list_datasets=true
            shift
            ;;
        --dataset)
            dataset=$2
            shift
            ;;
        --output-label)
            output_label=$2
            shift
            ;;
        --fs-license)
            fs_license=$2
            shift
            ;;
        --apptainer-dir)
            apptainer_dir=$2
            shift
            ;;
        --version)
            version=$2
            shift
            ;;
        --participant-label)
            # Remove the 'sub-' if it was provided in the participant_label argument
            if [[ "$2" == sub-* ]]; then
              participant_label="${2#sub-}"
            else
              participant_label=$2
            fi
            shift
            ;;
        --list-missing)
            list_missing=true
            ;;
        --more)
            more_options=$2
            shift
            ;;
        *)
            echo "Unknown parameter passed: $1"
            usage
            ;;
    esac
    shift
done

# Check mandatory options
if [ "${list_datasets}" = false ] && [ -z "${dataset}" ] ; then
    echo "Error: dataset name must be specified."
    usage
fi

if [ "${list_datasets}" = false ] && [ "${list_missing}" = false ] && [ -z "${participant_label}" ]; then
    echo "Error: participant label must be specified."
    usage
fi

# Main script logic
echo "List datasets flag: ${list_datasets}"
echo "Dataset name: ${dataset:-Not specified}"
echo "Output label: ${output_label}"
echo "Freesurfer license: ${fs_license}"
echo "Apptainer directory: ${apptainer_dir}"
echo "fMRIPrep version: ${version:-Not specified}"
echo "Participant label: ${participant_label:-Not specified}"
echo "List missing flag: ${list_missing}"
echo "More options: ${more_options:-Not specified}"

if [ ${list_datasets} = true ]; then
  echo "Listing available datasets..."
  echo "================== AVAILABLE DATASETS =================="
  ls "${DEFAULT_RAWDATA}" | grep rawdata | sed 's/-rawdata//g'
  echo "========================================================"
  echo "Add your dataset name to the following line to list missing subjects in the outputs"
  echo "$0 --list-missing --dataset"
  exit 0
fi

dataset_rawdata="${DEFAULT_RAWDATA}/${dataset}-rawdata"
dataset_derivatives="${DEFAULT_DERIVATIVES}/${dataset}-derivatives"
output_dir="${dataset_derivatives}/${output_label}"

# Show missing runs if required
if [ ${list_missing} = true ]; then
  echo "Listing missing runs..."
  compare_folders "${dataset_rawdata}" "${output_dir}"
  echo "Add your participant label to the following line to run the tool:"
  echo "$0 --dataset ${dataset} --participant_label "
  exit 0
fi

show_dir_content "${dataset_rawdata}"

# Checks and set-up
check_apptainer_is_installed
ensure_image_exists "${apptainer_dir}" "${version}"
check_file_exists "${fs_license}"

# Launch apptainer
echo "Launching apptainer image ${APPTAINER_IMG}"

fs_option=""
freesurfer_dir=${dataset_derivatives}/freesurfer_${DEFAULT_FREESURFER_VERSION}
if [ -d "${freesurfer_dir}/sub-${participant_label}" ]; then
  echo "Found pre-computed Freesurfer outputs in ${freesurfer_dir}, re-using them."
  fs_option="--fs-subjects-dir /derivatives/freesurfer_${DEFAULT_FREESURFER_VERSION}"
fi
echo 'test'
${APPTAINER_CMD} run \
  -B "${fs_license}":/usr/local/freesurfer/.license \
  -B "${dataset_rawdata}":/rawdata \
  -B "${dataset_derivatives}":/derivatives \
  ${APPTAINER_IMG}  \
    /rawdata \
    /derivatives/${output_label} \
    --participant_label "${participant_label}" ${fs_option}
