import os
from bids import BIDSLayout

from ln2t_tools.cli.cli import parse_args
from ln2t_tools.cli.cli import setup_terminal_colors
from ln2t_tools.utils.utils import (list_available_datasets,
                                    list_missing_subjects,
                                    check_apptainer_is_installed,
                                    ensure_image_exists,
                                    check_file_exists,
                                    check_participants_exist,
                                    get_t1w_list,
                                    get_flair_list,
                                    launch_apptainer,
                                    build_apptainer_cmd)
from ln2t_tools.utils.defaults import (DEFAULT_RAWDATA,
                                       DEFAULT_DERIVATIVES,
                                       DEFAULT_FS_VERSION,
                                       DEFAULT_FMRIPREP_VERSION)

setup_terminal_colors()

def main(args=None):
    if args is None:
        args = parse_args()

    if args.list_datasets:
        list_available_datasets()
        return

    if not args.dataset:
        print("Error: No dataset specified.")
        print("\nAvailable datasets:")
        available_datasets = [name[:-8] for name in os.listdir(DEFAULT_RAWDATA) if name.endswith("-rawdata")]
        if available_datasets:
            for dataset in available_datasets:
                print(f"  - {dataset}")
        else:
            print("  No datasets found in", DEFAULT_RAWDATA)
            
        print("\nUsage example:")
        print(f"  ln2t_tools freesurfer --dataset <dataset_name> --participant-label 01")
        return

    dataset_rawdata = os.path.join(DEFAULT_RAWDATA, f"{args.dataset}-rawdata")
    if not os.path.exists(dataset_rawdata):
        print(f"Error: Dataset '{args.dataset}' not found in {DEFAULT_RAWDATA}")
        print("\nAvailable datasets:")
        available_datasets = [name[:-8] for name in os.listdir(DEFAULT_RAWDATA) if name.endswith("-rawdata")]
        for dataset in available_datasets:
            print(f"  - {dataset}")
        return

    dataset_derivatives = os.path.join(DEFAULT_DERIVATIVES, f"{args.dataset}-derivatives")
    output_dir = os.path.join(dataset_derivatives, args.output_label or f"{args.tool}_{args.version or DEFAULT_FS_VERSION if args.tool == 'freesurfer' else DEFAULT_FMRIPREP_VERSION}")

    os.makedirs(output_dir, exist_ok=True)

    if args.list_missing:
        list_missing_subjects(dataset_rawdata, output_dir)
        return

    if args.tool in ["freesurfer", "fmriprep"]:  # Changed from args.tools to args.tool
        check_apptainer_is_installed("/usr/bin/apptainer")
        apptainer_img = ensure_image_exists(args.apptainer_dir, args.tool, args.version or DEFAULT_FS_VERSION if args.tool == "freesurfer" else DEFAULT_FMRIPREP_VERSION)
        check_file_exists(args.fs_license)

    participant_list = args.participant_list or [args.participant_label] if args.participant_label else []

    layout = BIDSLayout(dataset_rawdata)

    participant_list = check_participants_exist(layout, participant_list)

    for participant_label in participant_list:
        if args.tool == "freesurfer":
            # Get T1w files with metadata as objects first
            t1w_files = layout.get(
                sub=participant_label,
                scope="rawdata",
                suffix="T1w",
                extension=".nii.gz",
                return_type="object"  # Changed from "tuple" to "object"
            )
            
            if not t1w_files:
                print(f"No T1w images found for participant {participant_label}, skipping")
                continue

            _ = get_flair_list(layout, participant_label)

            # Process each T1w image with its session/run info
            for t1w in t1w_files:
                # Extract session and run from the BIDSFile object
                session = t1w.entities.get('session', None)
                run = t1w.entities.get('run', None)
                
                # Build output directory path including session/run
                output_subdir = f"sub-{participant_label}"
                if session:
                    output_subdir += f"_ses-{session}"
                if run:
                    output_subdir += f"_run-{run}"
                
                output_participant_dir = os.path.join(
                    dataset_derivatives,
                    args.output_label or f"freesurfer_{args.version or DEFAULT_FS_VERSION}",
                    output_subdir
                )

                if os.path.isdir(output_participant_dir):
                    print(f"Output directory ({output_participant_dir}) already exists, skipping")
                    continue

                # Get the actual file path
                t1w_path = t1w.path  # BIDSFile object has a path attribute

                apptainer_cmd = build_apptainer_cmd(
                    tool="freesurfer",
                    fs_license=args.fs_license,
                    rawdata=dataset_rawdata,
                    derivatives=dataset_derivatives,
                    participant_label=participant_label,
                    t1w=t1w_path,
                    apptainer_img=apptainer_img,
                    output_label=args.output_label or f"freesurfer_{args.version or DEFAULT_FS_VERSION}",
                    session=session,
                    run=run
                )
                launch_apptainer(apptainer_cmd=apptainer_cmd)

if __name__ == "__main__":
    main()