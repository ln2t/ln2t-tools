_ln2t_tools_completion() {
    local cur prev words cword
    _init_completion || return

    # List of tools
    local tools="freesurfer fmriprep"
    
    # Handle basic commands
    if [ $cword -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${tools}" -- "$cur") )
        return 0
    fi

    # Handle options
    case $prev in
        freesurfer|fmriprep)
            COMPREPLY=( $(compgen -W "--dataset" -- "$cur") )
            return 0
            ;;
        --dataset)
            # Get available datasets from rawdata directory
            local datasets=$(find ~/rawdata -maxdepth 1 -name "*-rawdata" -type d -printf "%f\n" | sed 's/-rawdata$//')
            COMPREPLY=( $(compgen -W "${datasets}" -- "$cur") )
            return 0
            ;;
        --participant-label|--participant-list)
            # Get available subjects from the dataset directory
            if [[ "${words[@]}" =~ "--dataset" ]]; then
                local dataset_idx=$(echo "${words[@]}" | grep -o "\--dataset" -n | cut -d: -f1)
                local dataset=${words[$dataset_idx + 1]}
                local subjects=$(find ~/rawdata/"$dataset"-rawdata -maxdepth 1 -name "sub-*" -type d -printf "%f\n" | sed 's/^sub-//')
                COMPREPLY=( $(compgen -W "${subjects}" -- "$cur") )
                return 0
            fi
            ;;
        *)
            # Other options based on context
            local opts="--participant-label --participant-list --output-label --fs-license --apptainer-dir --version --list-datasets --list-missing"
            
            # Add fMRIPrep specific options
            if [[ ${words[1]} == "fmriprep" ]]; then
                opts+=" --fs-no-reconall --output-spaces --nprocs --omp-nthreads"
            fi
            
            COMPREPLY=( $(compgen -W "${opts}" -- "$cur") )
            return 0
            ;;
    esac
}

complete -F _ln2t_tools_completion ln2t_tools