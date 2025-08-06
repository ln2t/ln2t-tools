import os
import site
import shutil
from pathlib import Path

def install_completion():
    """Install bash completion script during package installation."""
    try:
        # Get the completion script from the package directory
        pkg_dir = Path(__file__).parent.parent
        completion_source = pkg_dir / 'completion/ln2t_tools_completion.bash'
        
        if not completion_source.exists():
            print(f"Warning: Completion script not found at {completion_source}")
            return

        # Create user completion directory
        user_completion_dir = Path.home() / '.local/share/bash-completion/completions'
        user_completion_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy completion script to user directory
        completion_dest = user_completion_dir / 'ln2t_tools'
        shutil.copy2(completion_source, completion_dest)
        
        # Make script executable
        os.chmod(completion_dest, 0o755)
        
        # Add sourcing to .bashrc if not already present
        bashrc = Path.home() / '.bashrc'
        source_line = f"\n# ln2t_tools completion\nsource {completion_dest}\n"
        
        if bashrc.exists():
            with open(bashrc, 'r') as f:
                if str(completion_dest) not in f.read():
                    with open(bashrc, 'a') as f:
                        f.write(source_line)
        
        print(f"Installed completion script to {completion_dest}")
        
    except Exception as e:
        print(f"Warning: Failed to install completion script: {e}")
        # Don't raise the exception - allow installation to continue

if __name__ == '__main__':
    install_completion()