# ln2t-tools
Useful tools for the LN2T

## Configuration-Based Processing

ln2t_tools supports configuration-based processing using a TSV file. Create a file named `processing_config.tsv` in your rawdata directory with the following format:

```
dataset	freesurfer	fmriprep	qsiprep
dataset1	7.3.2	25.1.4	0.24.0
dataset2		25.1.4	
dataset3	7.4.0		0.24.0
```

Each row represents a dataset, and each column (except 'dataset') represents a tool with its version. Empty cells mean the tool won't be run for that dataset.

### Usage Examples

```bash
# Process all datasets according to config
ln2t_tools

# Process specific dataset according to config  
ln2t_tools --dataset mydataset

# Override config and run specific tool for single participant
ln2t_tools freesurfer --dataset mydataset --participant-label 01

# Process multiple participants
ln2t_tools freesurfer --dataset mydataset --participant-label 01 02 42

# Run QSIPrep with required output resolution
ln2t_tools qsiprep --dataset mydataset --participant-label 01 --output-resolution 1.25

# Check currently running instances
ln2t_tools --list-instances

# Set custom maximum instances limit
ln2t_tools --max-instances 5 --dataset mydataset
```

## Instance Management

ln2t_tools includes built-in safeguards to prevent resource overload:

- **Default limit**: Maximum 10 parallel instances
- **Lock files**: Uses `/tmp/ln2t_tools_locks/` to track active instances
- **Automatic cleanup**: Removes stale lock files from terminated processes
- **Graceful handling**: Shows helpful messages when limits are reached

Use `--list-instances` to see currently running processes and `--max-instances` to adjust the limit.

## Command-line Completion

To enable command-line completion:

1. Install the package:
```bash
pip install -U .
```

2. Source the completion script:
```bash
source $HOME/.local/share/bash-completion/completions/ln2t_tools
```

3. Add to your ~/.bashrc to make it permanent:
```bash
echo "source $HOME/.local/share/bash-completion/completions/ln2t_tools" >> ~/.bashrc
```
