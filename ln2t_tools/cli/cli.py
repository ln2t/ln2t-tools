import argparse

from ln2t_tools.utils.defaults import DEFAULT_FS_LICENSE, DEFAULT_APPTAINER_DIR


def parse_args():
    parser = argparse.ArgumentParser(description="ln2t_tools CLI")

    parser.add_argument("tool", help="Tool to use: freesurfer, fmriprep")
    parser.add_argument("--list-datasets", action="store_true", help="List available datasets")
    parser.add_argument("--dataset", help="Dataset name")
    parser.add_argument("--output-label", help="Output label")
    parser.add_argument("--fs-license", default=DEFAULT_FS_LICENSE, help="Freesurfer license file path")
    parser.add_argument("--apptainer-dir", default=DEFAULT_APPTAINER_DIR, help="Apptainer directory")
    parser.add_argument("--version", help="Version of the tool")
    parser.add_argument("--participant-label", help="Participant label")
    parser.add_argument("--participant-list", nargs='+', help="List of participant labels")
    parser.add_argument("--list-missing", action="store_true", help="List missing runs")
    parser.add_argument("--more", help="More options")

    # Parse the arguments
    return parser.parse_args()


def setup_terminal_colors():
    import warnings
    import traceback
    import sys

    # ANSI escape codes for colors
    YELLOW = '\033[93m'
    RESET = '\033[0m'

    def custom_warning_format(message, category, filename, lineno, line=None):
        # Define the color for the warning message
        return f"{YELLOW}{filename}:{lineno}: {category.__name__}: {message}{RESET}\n"

    # Set the custom warning formatter
    warnings.formatwarning = custom_warning_format

    # ANSI escape codes for colors
    RED = '\033[91m'
    RESET = '\033[0m'

    def custom_exception_handler(exc_type, exc_value, exc_traceback):
        # Format the exception traceback with color
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"{RED}{tb_str}{RESET}", end="")

    # Set the custom exception handler
    sys.excepthook = custom_exception_handler

