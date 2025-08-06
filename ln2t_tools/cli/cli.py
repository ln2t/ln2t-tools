import argparse
import warnings
import traceback
import sys
from pathlib import Path
from typing import Optional
from types import TracebackType  # Add this import

from ln2t_tools.utils.defaults import (
    DEFAULT_FS_LICENSE,
    DEFAULT_APPTAINER_DIR
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="LN2T Tools - Neuroimaging Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "tool",
        choices=["freesurfer", "fmriprep"],
        help="Neuroimaging tool to use"
    )

    parser.add_argument(
        "--dataset",
        help="BIDS dataset name (without -rawdata suffix)"
    )

    parser.add_argument(
        "--participant-label",
        help="Single participant label (without 'sub-' prefix)"
    )

    parser.add_argument(
        "--participant-list",
        nargs="+",
        help="List of participant labels to process"
    )

    parser.add_argument(
        "--output-label",
        help="Custom label for output directory"
    )

    parser.add_argument(
        "--fs-license",
        type=Path,
        default=DEFAULT_FS_LICENSE,
        help="Path to FreeSurfer license file"
    )

    parser.add_argument(
        "--apptainer-dir",
        type=Path,
        default=DEFAULT_APPTAINER_DIR,
        help="Path to Apptainer images directory"
    )

    parser.add_argument(
        "--version",
        help="Tool version to use"
    )

    parser.add_argument(
        "--list-datasets",
        action="store_true",
        help="List available BIDS datasets"
    )

    parser.add_argument(
        "--list-missing",
        action="store_true",
        help="List subjects missing from output"
    )

    return parser.parse_args()


def setup_terminal_colors() -> None:
    """Configure colored output for warnings and errors."""
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

    def warning_formatter(
        message: str,
        category: Warning,
        filename: str,
        lineno: int,
        line: Optional[str] = None
    ) -> str:
        """Format warning messages with color."""
        return f"{YELLOW}{filename}:{lineno}: {category.__name__}: {message}{RESET}\n"

    def exception_handler(
        exc_type: type,
        exc_value: Exception,
        exc_traceback: TracebackType  # Now TracebackType is properly imported
    ) -> None:
        """Format exception messages with color."""
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"{RED}{tb_str}{RESET}", file=sys.stderr)

    warnings.formatwarning = warning_formatter
    sys.excepthook = exception_handler

