#!/bin/bash

_ln2t_tools_completion() {
    local cur prev words cword
    _init_completion || return

    # List of tools
    local tools="freesurfer fmriprep qsiprep"
    
    # Function to get dataset name from command line
    _get_dataset_name() {
        local words=("${COMP_WORDS[@]}")
        for ((i=1; i<${#words[@]}-1; i++)); do
            if [[ "${words[i]}" == "--dataset" ]]; then
                echo "${words[i+1]}"
                return 0
            fi
        done
        return 1
    }

    # Function to check if we're completing participant labels
    _completing_participants() {
        local words=("${COMP_WORDS[@]}")
        for ((i=1; i<${#words[@]}; i++)); do
            if [[ "${words[i]}" == "--participant-label" ]]; then
                # Check if current position is after --participant-label
                if [[ $cword -gt $i ]]; then
                    return 0
                fi
            fi
        done
        return 1
    }

    # Handle basic commands
    if [ $cword -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${tools}" -- "$cur") )
        return 0
    fi

    # Check if we're completing participant labels (can be multiple)
    if _completing_participants; then
        local dataset=$(_get_dataset_name)
        if [ -n "$dataset" ]; then
            local subjects=$(find ~/rawdata/"$dataset"-rawdata -maxdepth 1 -name "sub-*" -type d -printf "%f\n" 2>/dev/null | sed 's/^sub-//')
            COMPREPLY=( $(compgen -W "${subjects}" -- "$cur") )
            return 0
        fi
    fi

    # Handle options
    case $prev in
        freesurfer|fmriprep|qsiprep)
            COMPREPLY=( $(compgen -W "--dataset" -- "$cur") )
            return 0
            ;;
        --dataset)
            # Get available datasets from rawdata directory
            local datasets=$(find ~/rawdata -maxdepth 1 -name "*-rawdata" -type d -printf "%f\n" | sed 's/-rawdata$//')
            COMPREPLY=( $(compgen -W "${datasets}" -- "$cur") )
            return 0
            ;;
        --participant-label)
            # Get dataset name from command line
            local dataset=$(_get_dataset_name)
            if [ -n "$dataset" ]; then
                # Get available subjects from the specific dataset directory
                local subjects=$(find ~/rawdata/"$dataset"-rawdata -maxdepth 1 -name "sub-*" -type d -printf "%f\n" 2>/dev/null | sed 's/^sub-//')
                COMPREPLY=( $(compgen -W "${subjects}" -- "$cur") )
                return 0
            fi
            ;;
        *)
            # Other options based on context
            local opts="--participant-label --output-label --fs-license --apptainer-dir --version --list-datasets --list-missing --list-instances --max-instances"
            
            # Add fMRIPrep specific options
            if [[ ${words[1]} == "fmriprep" ]]; then
                opts+=" --fs-no-reconall --output-spaces --nprocs --omp-nthreads"
            fi
            
            # Add QSIPrep specific options
            if [[ ${words[1]} == "qsiprep" ]]; then
                opts+=" --output-resolution --denoise-method --dwi-only --anat-only --nprocs --omp-nthreads"
            fi
            
            COMPREPLY=( $(compgen -W "${opts}" -- "$cur") )
            return 0
            ;;
    esac
}

complete -F _ln2t_tools_completion ln2t_tools