#!/bin/bash

# Default variables
DEFAULT_APPTAINER_DIR="${HOME}/apptainer"
DEFAULT_VERSION="7.3.2"  # As of 20250801, version 7.3.2 is the once included in latest fmriprep (25.1.4)
DEFAULT_FS_LICENSE="/opt/freesurfer/.license"

# Apptainer variables
APPTAINER_CMD="/usr/bin/apptainer"
APPTAINER_OPT="--nv --cleanenv"

# Display usage information
usage() {
    echo "Usage: $0 [--input input_dir] [--output output_dir] [--fs-license fs_license] [--apptainer-dir apptainer_dir] [--version version] [--participant-label participant_label] [--more more_options]"
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
    local file_path="${apptainer_dir}/freesurfer.freesurfer.${version}.sif"
    local create_command="${APPTAINER_CMD} build ${file_path} docker://freesurfer/freesurfer:${version}"

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

# Initialize variables
input_dir=""
output_dir=""
fs_license="${DEFAULT_FS_LICENSE}"
apptainer_dir="${DEFAULT_APPTAINER_DIR}"
version="${DEFAULT_VERSION}"
more_options=""

# Parse command line options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --input)
            input_dir=$2
            shift
            ;;
        --output)
            output_dir=$2
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
            participant_label=$2
            shift
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
if [ -z "$input_dir" ] || [ -z "$output_dir" ] || [ -z "$participant_label" ]; then
    echo "Error: input, output and participant_label values must be specified."
    usage
fi

# Main script logic
echo "Input directory: $input_dir"
echo "Output directory: $output_dir"
echo "Freesurfer license: $fs_license"
echo "Apptainer directory: $apptainer_dir"
echo "Freesurfer version: ${version:-Not specified}"
echo "Participant label: ${participant_label}"
echo "More options: ${more_options:-Not specified}"

# Checks and set-up
check_apptainer_is_installed
ensure_image_exists "${apptainer_dir}" "${version}"
check_file_exists "${fs_license}"

participant_dir="${input_dir}/sub-${participant_label}"
participant_T1w="${participant_dir}/anat/sub-${participant_label}_T1w.nii.gz"
show_dir_content "${input_dir}"
check_file_exists "${participant_T1w}"

# Launch apptainer
echo "Launching apptainer image ${APPTAINER_IMG}"

${APPTAINER_CMD} run \
  -B "${fs_license}":/usr/local/freesurfer/.license \
  -B "${input_dir}":/rawdata \
  -B "${output_dir}":/derivatives "${app}" \
  ${APPTAINER_IMG} recon-all -all \
    -subjid "sub-${participant_label}"

exit 0

${APPTAINER_CMD} run \
  -B "${fs_license}":/usr/local/freesurfer/.license \
  -B "${input_dir}":/rawdata \
  -B "${output_dir}":/derivatives "${app}" \
  ${APPTAINER_IMG} recon-all -all \
  -subjid "sub-${participant_label}" \
  -i "/rawdata/sub-${participant_label}/anat/sub-${participant_label}_T1w.nii.gz" \
  -T2 "/rawdata/sub-${participant_label}/anat/sub-${participant_label}_FLAIR.nii.gz" \
  -sd "/derivatives"