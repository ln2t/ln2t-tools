#!/bin/bash

# Default variables
DEFAULT_APPTAINER_DIR="/opt/apptainer"
DEFAULT_FS_VERSION="7.3.2"
DEFAULT_FMRIPREP_VERSION="25.1.4"
DEFAULT_FS_LICENSE="/opt/freesurfer/.license"
DEFAULT_RAWDATA="$HOME/rawdata"
DEFAULT_DERIVATIVES="$HOME/derivatives"

# Apptainer variables
APPTAINER_CMD="/usr/bin/apptainer"
APPTAINER_OPT="--nv --cleanenv --fuse-mount-timeout 300"

# Display usage information
usage() {
    echo "Usage: $0 <tool> [--list-datasets] [--dataset dataset] [--output-label output_label] [--fs-license fs_license] [--apptainer-dir apptainer_dir] [--version version] [--participant-label participant_label] [--list-missing] [--more more_options]"
    echo "Available tools: freesurfer, fmriprep."
    echo "Type '$0 help' for help"
    exit 1
}

# Check apptainer program is installed
check_apptainer_is_installed() {
  if [ ! -f "${APPTAINER_CMD}" ]; then
    echo "Apptainer not found at ${APPTAINER_CMD}, are you sure it is installed?"
    exit 1
  fi
}

# Ensure apptainer image exists. If not, create it.
ensure_image_exists() {
    local apptainer_dir="$1"
    local tool="$2"
    local version="$3"
    local file_path
    local create_command

    if [ "$tool" == "freesurfer" ]; then
        file_path="${apptainer_dir}/freesurfer.freesurfer.${version}.sif"
        create_command="${APPTAINER_CMD} build ${file_path} docker://freesurfer/freesurfer:${version}"
    elif [ "$tool" == "fmriprep" ]; then
        file_path="${apptainer_dir}/nipreps.fmriprep.${version}.sif"
        create_command="${APPTAINER_CMD} build ${file_path} docker://nipreps/fmriprep:${version}"
    else
        echo "Unknown tool: $tool"
        exit 1
    fi

    if [ ! -f "$file_path" ]; then
        echo "File $file_path does not exist. Creating it..."
        mkdir -p "${apptainer_dir}"
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
      echo "File $file_path does not exist."
    else
      echo "File $file_path found."
    fi
}

# List directory content
show_dir_content() {
  local directory=$1
  echo "Listing contents of ${directory}:"
  ls "${directory}"
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
        mkdir -p "$output_dir"
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
version=""
output_label=""
tool=""
more_options=""
list_missing=false

# Parse command line options
if [ $# -eq 0 ]; then
    usage
fi

tool=$1
shift

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --list-datasets)
            list_datasets=true
            shift
            ;;
        --dataset)
            shift
            dataset=$1
            ;;
        --output-label)
            shift
            output_label=$1
            ;;
        --fs-license)
            shift
            fs_license=$1
            ;;
        --apptainer-dir)
            shift
            apptainer_dir=$1
            ;;
        --version)
            shift
            version=$1
            ;;
        --participant-label)
            shift
            # Remove the 'sub-' if it was provided in the participant_label argument
            if [[ "$1" == sub-* ]]; then
              participant_label="${1#sub-}"
            else
              participant_label=$1
            fi
            ;;
        --participant-list)
            shift
            # Collect all subsequent arguments until the next option
            while [[ $# -gt 0 && $1 != --* ]]; do
                if [[ "$1" == sub-* ]]; then
                  curr_participant_label="${1#sub-}"
                else
                  curr_participant_label=$1
                fi
                participant_list+=("${curr_participant_label}")
                shift
            done
            ;;
        --list-missing)
            shift
            list_missing=true
            ;;
        --more)
            shift
            more_options=$1
            ;;
        *)
            echo "Unknown parameter passed: $1"
            usage
            ;;
    esac
    shift
done

# Check mandatory options
if [ -z "${tool}" ]; then
    echo "Error: tool must be specified."
    usage
fi

if [ "${tool}" = "help" ]; then
  usage
fi

if [ "${list_datasets}" = false ] && [ -z "${dataset}" ]; then
    echo "Error: dataset name must be specified."
    usage
fi

#if [ "${list_datasets}" = false ] && [ "${list_missing}" = false ] && [ -z "${participant_label}" ]; then
#    echo "Error: participant label must be specified."
#    usage
#fi

# Set default version and output label based on tool
if [ "$tool" == "freesurfer" ]; then
    version=${version:-$DEFAULT_FS_VERSION}
    output_label=${output_label:-"freesurfer_${version}"}
elif [ "$tool" == "fmriprep" ]; then
    version=${version:-$DEFAULT_FMRIPREP_VERSION}
    output_label=${output_label:-"fmriprep_${version}"}
else
    echo "Unknown tool: $tool"
    exit 1
fi

# Main script logic
echo "Tool: ${tool}"
echo "List datasets flag: ${list_datasets}"
echo "Dataset name: ${dataset:-Not specified}"
echo "Participant list: ${participant_list[@]:-Not specified}"
echo "Output label: ${output_label}"
echo "Freesurfer license: ${fs_license}"
echo "Apptainer directory: ${apptainer_dir}"
echo "Version: ${version:-Not specified}"
echo "Participant label: ${participant_label:-Not specified}"
echo "List missing flag: ${list_missing}"
echo "More options: ${more_options:-Not specified}"

if [ ${list_datasets} = true ]; then
  echo "Listing available datasets..."
  echo "================== AVAILABLE DATASETS =================="
  ls "${DEFAULT_RAWDATA}" | grep rawdata | sed 's/-rawdata//g'
  echo "========================================================"
  echo "Add your dataset name to the following line to list missing subjects in the outputs"
  echo "$0 ${tool} --list-missing --dataset"
  exit 0
fi

dataset_rawdata="${DEFAULT_RAWDATA}/${dataset}-rawdata"
dataset_derivatives="${DEFAULT_DERIVATIVES}/${dataset}-derivatives"
output_dir="${dataset_derivatives}/${output_label}"

if [ -d "${output_dir}" ]; then
  echo "Output directory ${output_dir} already exists"
else
  echo "Creating output directory ${output_dir}"
  mkdir -p "${output_dir}"
fi

# Show missing runs if required
if [ ${list_missing} = true ]; then
  echo "Listing missing runs..."
  compare_folders "${dataset_rawdata}" "${output_dir}"
  echo "Add your participant label to the following line to run the tool:"
  echo "$0 ${tool} --dataset ${dataset} --participant-label"
  exit 0
fi

# Checks and set-up
show_dir_content "${dataset_rawdata}"
check_apptainer_is_installed
ensure_image_exists "${apptainer_dir}" "${tool}" "${version}"
check_file_exists "${fs_license}"

# Loop over participants
for participant_label in "${participant_list[@]}"; do
  if [ ! -z "${participant_label}" ]; then
    # Tool-specific steps
    if [ "$tool" == "freesurfer" ]; then
        participant_dir="${dataset_rawdata}/sub-${participant_label}"
        participant_T1w="${participant_dir}/anat/sub-${participant_label}_T1w.nii.gz"
        if [ -f "${participant_T1w}" ]; then
          if [ ! -d "${dataset_derivatives}/${output_label}/sub-${participant_label}" ]; then
            flair_option=""
            participant_flair="${participant_dir}/anat/sub-${participant_label}_FLAIR.nii.gz"
            if [ -f "${participant_flair}" ]; then
              echo "WARNING: untested feature using T2 flag in apptainer call!"
              flair_option="-T2 /rawdata/sub-${participant_label}/anat/sub-${participant_label}_FLAIR.nii.gz"
            fi
            # Launch apptainer for freesurfer
            echo "Launching apptainer image ${APPTAINER_IMG}"
            ${APPTAINER_CMD} run \
              -B "${fs_license}":/usr/local/freesurfer/.license \
              -B "${dataset_rawdata}":/rawdata \
              -B "${dataset_derivatives}":/derivatives \
              ${APPTAINER_IMG} recon-all -all \
                -subjid "sub-${participant_label}" \
                -i "/rawdata/sub-${participant_label}/anat/sub-${participant_label}_T1w.nii.gz" \
                -sd "/derivatives/${output_label}" ${flair_option}
          else
            echo "Output subject directory (${dataset_derivatives}/${output_label}/sub-${participant_label}) already exists, skipping subject "
          fi
        else
          echo "File ${participant_T1w} not found, skipping participant"
        fi
    elif [ "$tool" == "fmriprep" ]; then
        fs_option=""
        freesurfer_dir=${dataset_derivatives}/freesurfer_${DEFAULT_FS_VERSION}
        if [ -d "${freesurfer_dir}/sub-${participant_label}" ]; then
          echo "Found pre-computed Freesurfer outputs in ${freesurfer_dir}, re-using them."
          fs_option="--fs-subjects-dir /derivatives/freesurfer_${DEFAULT_FS_VERSION}"
        fi
        # Launch apptainer for fmriprep
        echo "Launching apptainer image ${APPTAINER_IMG}"
        ${APPTAINER_CMD} run \
          -B "${fs_license}":/usr/local/freesurfer/.license \
          -B "${dataset_rawdata}":/rawdata \
          -B "${dataset_derivatives}":/derivatives \
          ${APPTAINER_IMG} \
            /rawdata \
            /derivatives/${output_label} \
            participant \
            --fs-license-file /usr/local/freesurfer/.license \
            --participant_label "${participant_label}" ${fs_option}
    fi

  fi
done

