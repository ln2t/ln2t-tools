import os
import site
import shutil
from pathlib import Path

def install_completion():
    """Install bash completion script during package installation."""
    # Get the package installation directory
    site_packages = site.getsitepackages()[0]
    completion_source = Path(site_packages) / 'ln2t_tools/completion/ln2t_tools_completion.bash'
    
    # Define possible completion directories
    completion_dirs = [
        Path.home() / '.local/share/bash-completion/completions',  # User directory
        Path('/usr/local/share/bash-completion/completions'),      # Local system directory
        Path('/usr/share/bash-completion/completions'),           # System directory
    ]

    # Create user completion directory if it doesn't exist
    user_completion_dir = completion_dirs[0]
    user_completion_dir.parent.mkdir(parents=True, exist_ok=True)
    
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

if __name__ == '__main__':
    install_completion()