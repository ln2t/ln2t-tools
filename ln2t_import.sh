#!/bin/bash

# Default variables
DEFAULT_SOURCEDATA="$HOME/sourcedata"
DEFAULT_RAWDATA="$HOME/rawdata"
DEFAULT_DERIVATIVES="$HOME/derivatives"
SLEEP_TIME=5  # in seconds

# Dcm2bids-related variables
DCM2BIDS_CMD="dcm2bids"

# Display usage information
usage() {
    echo "Usage: $0 [--list-datasets] [--dataset dataset] [--participant-list participant_list] [--clean-uncompressed-dicom] [--check-content] [--list-uncompressed-dicom]"
    echo "Typical usages:"
    echo "$0 --list-dataset  # To list available datasets"
    echo "$0 --dataset DATASET --list-uncompressed-dicom # To list dicoms that are not yet compressed (possibly not yet imported)"
    echo "$0 --dataset DATASET --participant-list 01 42 666 # To compress and import data for subjects 01, 42 and 666"
    echo "$0 --dataset DATASET --participant-list 01 42 666 --check-content # To check content of imported subjects"
    echo "$0 --dataset DATASET --participant-list 01 42 666 --clean-uncompressed-dicom # To delete uncompressed dicoms (WARNING: this deletes data!)"
    echo "Notes:"
    echo "- data are assumed to be in dicom folders of the form AB01, AB42, AB666, etc, where AB stands for the dataset initials."
    echo "- the sourcedata directory of your dataset is assumed to contain a valid dcm2bids config file at dcm2bids/config.json"
    exit 1
}

# Generic function to check that a dir exists and exit if not
check_dir_exists() {
    local dir_path="$1"
    if [ ! -d "${dir_path}" ]; then
      echo "Directory ${dir_path} does not exist. Aborting..."
      exit 1
    else
        echo "Directory ${dir_path} found."
    fi
}

# Generic function to check that a file exists and exit if not
check_file_exists() {
    local file_path="$1"
    if [ ! -f "$file_path" ]; then
      echo "File $file_path does not exist. Aborting..."
      exit 1
    else
        echo "File $file_path found."
    fi
}

# Utility to extract initials of dataset name
extract_initials() {
    local input="$1"

    # Extract the middle part between the first and last hyphen
    local middle_part=$(echo "$input" | cut -d'-' -f2)

    # Extract the first letters of each word in the middle part
    IFS='_' read -ra words <<< "$middle_part"
    local initials=""
    for word in "${words[@]}"; do
        initials="${initials}${word:0:1}"
    done

    # Output the initials
    echo "$initials"
}

# List directories only function
list_dir_only() {
  local input="$1"

  for file in $(ls ${input}); do
    if [ -d "${file}" ]; then
      echo "${file}"
    fi
  done
}

# Initialize variables
dataset=""
participant_list=""
list_datasets=false
clean_uncompressed_dicom=false
check_content=false
list_uncompressed_dicom=false

# Parse command-line arguments
if [ $# -eq 0 ]; then
    usage
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dataset)
            shift
            dataset="$1"
            shift
            ;;
        --participant-list)
            # Shift past the --participant-list
            shift
            # Collect all subsequent arguments until the next option
            while [[ $# -gt 0 && $1 != --* ]]; do
                participant_list+=("$1")
                shift
            done
            ;;
        --list-datasets)
            shift
            list_datasets=true
            ;;
        --clean-uncompressed-dicom)
            shift
            clean_uncompressed_dicom=true
            ;;
        --check-content)
            shift
            check_content=true
            ;;
        --list-uncompressed-dicom)
            shift
            list_uncompressed_dicom=true
            ;;
        *)
            # Unknown option
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Initialize Python env
source $HOME/venv/ln2t_import_env/bin/activate

# Main script logic
echo "Dataset: ${dataset:-Not specified}"
echo "Participant list: ${participant_list[@]:-Not specified}"
echo "List datasets: ${list_datasets:-Not specified}"
echo "Clean uncompressed dicom: ${clean_uncompressed_dicom:-Not specified}"
echo "Check Content: ${check_content:-Not specified}"
echo "List uncompressed dicom: ${list_uncompressed_dicom:-Not specified}"

if [ ${list_datasets} = true ]; then
  echo "Listing available datasets..."
  echo "================== AVAILABLE DATASETS =================="
  ls "${DEFAULT_RAWDATA}" | grep rawdata | sed 's/-rawdata//g'
  echo "========================================================"
  exit 0
fi

# Build dataset-related paths
SOURCEDATA_DIR="${DEFAULT_SOURCEDATA}/${dataset}-sourcedata"
DICOM_DIR="${SOURCEDATA_DIR}/dicom"
DCM2BIDS_CONFIG="${SOURCEDATA_DIR}/dcm2bids/config.json"
RAWDATA_DIR="${DEFAULT_RAWDATA}/${dataset}-rawdata"

# Checks and set-up
check_dir_exists "${DICOM_DIR}"
check_file_exists "${DCM2BIDS_CONFIG}"
mkdir -p "${RAWDATA_DIR}"
DATASET_INITIALS=$(extract_initials ${dataset})
echo "Extracted dataset initials: ${DATASET_INITIALS}"

if [ "${list_uncompressed_dicom}" ]; then
  echo "Listing dicom directories in ${DICOM_DIR}"
  list_dir_only "${DICOM_DIR}"
  exit 0
fi

# Main loop over participants
for participant in "${participant_list[@]}"; do
  if [ ! -z "${participant}" ]; then
    dicom="${DICOM_DIR}/${DATASET_INITIALS}${participant}"
    if [ "${clean_uncompressed_dicom}" = false ]; then
      echo "Running for participant ${participant}"
      check_file_exists ${dicom}
      echo "Compressing ..."
      tar czf "${dicom}.tar.gz" "${dicom}"
      echo "Converting to BIDS ..."
      ${DCM2BIDS_CMD} -o "${RAWDATA_DIR}" -p "${participant}" -d "${dicom}" -c "${DCM2BIDS_CONFIG}"
    else
      echo "Deleting uncompressed dicoms, you have ${SLEEP_TIME} seconds to cancel (press CTRL+C) if this is a mistake!"
      sleep "${SLEEP_TIME}"
      if [ -f "${dicom}.tar.gz" ]; then
        rm -r "${dicom}"
      else
        echo "Compressed file ${dicom}.tar.gz not found, deletion of ${dicom} cancelled."
      fi
    fi

    if [ "${check_content}" = true ]; then
      check_dir_exists "${RAWDATA_DIR}/sub-${participant}"
      echo "Checking content of imported participant ${participant}"
      tree "${RAWDATA_DIR}/sub-${participant}"
    fi
  fi
done