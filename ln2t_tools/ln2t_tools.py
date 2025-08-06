import os
import logging
from typing import Optional, List, Dict
from pathlib import Path
from bids import BIDSLayout

from ln2t_tools.cli.cli import parse_args, setup_terminal_colors
from ln2t_tools.utils.utils import (
    list_available_datasets,
    list_missing_subjects,
    check_apptainer_is_installed,
    ensure_image_exists,
    check_file_exists,
    check_participants_exist,
    get_flair_list,
    launch_apptainer,
    build_apptainer_cmd
)
from ln2t_tools.utils.defaults import (
    DEFAULT_RAWDATA,
    DEFAULT_DERIVATIVES,
    DEFAULT_FS_VERSION,
    DEFAULT_FMRIPREP_VERSION
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_available_datasets(rawdata_dir: str) -> List[str]:
    """Get list of available BIDS datasets in the rawdata directory."""
    return [name[:-8] for name in os.listdir(rawdata_dir) 
            if name.endswith("-rawdata")]

def setup_directories(args) -> tuple[Path, Path, Path]:
    """Setup and validate directory structure for processing.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Tuple of (rawdata_dir, derivatives_dir, output_dir)
        
    Raises:
        FileNotFoundError: If dataset directory doesn't exist
    """
    dataset_rawdata = Path(DEFAULT_RAWDATA) / f"{args.dataset}-rawdata"
    if not dataset_rawdata.exists():
        available = get_available_datasets(DEFAULT_RAWDATA)
        datasets_str = "\n  - ".join(available) if available else "No datasets found"
        raise FileNotFoundError(
            f"Dataset '{args.dataset}' not found in {DEFAULT_RAWDATA}\n"
            f"Available datasets:\n  - {datasets_str}"
        )

    dataset_derivatives = Path(DEFAULT_DERIVATIVES) / f"{args.dataset}-derivatives"
    version = (DEFAULT_FS_VERSION if args.tool == 'freesurfer' 
              else DEFAULT_FMRIPREP_VERSION)
    output_dir = dataset_derivatives / (args.output_label or 
                                      f"{args.tool}_{args.version or version}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    return dataset_rawdata, dataset_derivatives, output_dir

def process_freesurfer_subject(
    layout: BIDSLayout,
    participant_label: str,
    args,
    dataset_rawdata: Path,
    dataset_derivatives: Path,
    apptainer_img: str
) -> None:
    """Process a single subject with FreeSurfer."""
    t1w_files = layout.get(
        subject=participant_label,
        scope="raw",
        suffix="T1w",
        extension=".nii.gz",
        return_type="filename"
    )
    
    if not t1w_files:
        logger.warning(f"No T1w images found for participant {participant_label}")
        return

    _ = get_flair_list(layout, participant_label)

    for t1w in t1w_files:
        process_single_t1w(
            t1w=t1w,
            layout=layout,
            participant_label=participant_label,
            args=args,
            dataset_rawdata=dataset_rawdata,
            dataset_derivatives=dataset_derivatives,
            apptainer_img=apptainer_img
        )

def process_single_t1w(
    t1w: str,
    layout: BIDSLayout,
    participant_label: str,
    args,
    dataset_rawdata: Path,
    dataset_derivatives: Path,
    apptainer_img: str
) -> None:
    """Process a single T1w image with FreeSurfer."""
    entities = layout.parse_file_entities(t1w)
    output_subdir = build_bids_subdir(
        participant_label, 
        entities.get('session'), 
        entities.get('run')
    )
    
    output_participant_dir = dataset_derivatives / (
        args.output_label or 
        f"freesurfer_{args.version or DEFAULT_FS_VERSION}"
    ) / output_subdir

    if output_participant_dir.exists():
        logger.info(f"Output exists, skipping: {output_participant_dir}")
        return

    apptainer_cmd = build_apptainer_cmd(
        tool="freesurfer",
        fs_license=args.fs_license,
        rawdata=str(dataset_rawdata),
        derivatives=str(dataset_derivatives),
        participant_label=participant_label,
        t1w=t1w,
        apptainer_img=apptainer_img,
        output_label=args.output_label or f"freesurfer_{args.version or DEFAULT_FS_VERSION}",
        session=entities.get('session'),
        run=entities.get('run')
    )
    launch_apptainer(apptainer_cmd=apptainer_cmd)

def build_bids_subdir(
    participant_label: str,
    session: Optional[str] = None,
    run: Optional[str] = None
) -> str:
    """Build BIDS-compliant subject directory name."""
    parts = [f"sub-{participant_label}"]
    if session:
        parts.append(f"ses-{session}")
    if run:
        parts.append(f"run-{run}")
    return "_".join(parts)

def process_fmriprep_subject(
    layout: BIDSLayout,
    participant_label: str,
    args,
    dataset_rawdata: Path,
    dataset_derivatives: Path,
    apptainer_img: str
) -> None:
    """Process a single subject with fMRIPrep."""
    # Check for required files
    t1w_files = layout.get(
        subject=participant_label,
        scope="raw",
        suffix="T1w",
        extension=".nii.gz",
        return_type="filename"
    )
    
    if not t1w_files:
        logger.warning(f"No T1w images found for participant {participant_label}")
        return

    # Check for functional data
    func_files = layout.get(
        subject=participant_label,
        scope="raw",
        suffix="bold",
        extension=".nii.gz",
        return_type="filename"
    )
    
    if not func_files:
        logger.warning(f"No functional data found for participant {participant_label}")
        return

    # Check for existing FreeSurfer output
    entities = layout.parse_file_entities(t1w_files[0])
    fs_output_dir = get_freesurfer_output(
        derivatives_dir=dataset_derivatives,
        participant_label=participant_label,
        version=DEFAULT_FS_VERSION,
        session=entities.get('session'),
        run=entities.get('run')
    )

    # Build output directory path
    output_subdir = build_bids_subdir(participant_label)
    output_participant_dir = dataset_derivatives / (
        args.output_label or 
        f"fmriprep_{args.version or DEFAULT_FMRIPREP_VERSION}"
    ) / output_subdir

    if output_participant_dir.exists():
        logger.info(f"Output exists, skipping: {output_participant_dir}")
        return

    # If FreeSurfer output exists, use it
    if fs_output_dir and not args.fs_no_reconall:
        logger.info(f"Using existing FreeSurfer output: {fs_output_dir}")
        fs_no_reconall = "--fs-no-reconall"
    else:
        logger.info("No existing FreeSurfer output found, will run reconstruction")
        fs_no_reconall = ""
        fs_output_dir = None

    # Build and launch fMRIPrep command
    apptainer_cmd = build_apptainer_cmd(
        tool="fmriprep",
        fs_license=args.fs_license,
        rawdata=str(dataset_rawdata),
        derivatives=str(dataset_derivatives),
        participant_label=participant_label,
        apptainer_img=apptainer_img,
        output_label=args.output_label or f"fmriprep_{args.version or DEFAULT_FMRIPREP_VERSION}",
        fs_no_reconall=fs_no_reconall,
        output_spaces=getattr(args, 'output_spaces', "MNI152NLin2009cAsym:res-2"),
        nprocs=getattr(args, 'nprocs', 8),
        omp_nthreads=getattr(args, 'omp_nthreads', 8),
        fs_subjects_dir=fs_output_dir
    )
    launch_apptainer(apptainer_cmd=apptainer_cmd)

def main(args=None) -> None:
    """Main entry point for ln2t_tools."""
    if args is None:
        args = parse_args()
        setup_terminal_colors()

    try:
        if args.list_datasets:
            list_available_datasets()
            return

        if not args.dataset:
            available = get_available_datasets(DEFAULT_RAWDATA)
            datasets_str = "\n  - ".join(available) if available else "No datasets found"
            logger.error(
                "No dataset specified.\n"
                f"Available datasets:\n  - {datasets_str}\n\n"
                "Usage example:\n"
                "  ln2t_tools freesurfer --dataset <dataset_name> --participant-label 01"
            )
            return

        dataset_rawdata, dataset_derivatives, output_dir = setup_directories(args)

        if args.list_missing:
            list_missing_subjects(dataset_rawdata, output_dir)
            return

        if args.tool in ["freesurfer", "fmriprep"]:
            check_apptainer_is_installed("/usr/bin/apptainer")
            apptainer_img = ensure_image_exists(
                args.apptainer_dir, 
                args.tool, 
                args.version or (DEFAULT_FS_VERSION if args.tool == "freesurfer" 
                               else DEFAULT_FMRIPREP_VERSION)
            )
            check_file_exists(args.fs_license)

        participant_list = (args.participant_list or 
                          [args.participant_label] if args.participant_label else [])

        layout = BIDSLayout(dataset_rawdata)
        participant_list = check_participants_exist(layout, participant_list)

        for participant_label in participant_list:
            if args.tool == "freesurfer":
                process_freesurfer_subject(
                    layout=layout,
                    participant_label=participant_label,
                    args=args,
                    dataset_rawdata=dataset_rawdata,
                    dataset_derivatives=dataset_derivatives,
                    apptainer_img=apptainer_img
                )
            elif args.tool == "fmriprep":
                process_fmriprep_subject(
                    layout=layout,
                    participant_label=participant_label,
                    args=args,
                    dataset_rawdata=dataset_rawdata,
                    dataset_derivatives=dataset_derivatives,
                    apptainer_img=apptainer_img
                )
            else:
                logger.error(f"Unsupported tool: {args.tool}")
                return

    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()