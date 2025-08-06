from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
import os

# Function to read the contents of the requirements file
def read_requirements():
    with open('requirements.txt') as req:
        return req.read().splitlines()

class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        # Import and run the install script
        from ln2t_tools.install.post_install import install_completion
        install_completion()

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        # Import and run the install script
        from ln2t_tools.install.post_install import install_completion
        install_completion()

setup(
    name="ln2t_tools",
    version="1.0.0",
    url='https://github.com/ln2t/ln2t_tools',
    author='Antonin Rovai',
    author_email='antonin.rovai@hubruxelles.be',
    description='Tools to manage, preprocess and process data at the LN2T',
    packages=find_packages(),
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'ln2t_tools = ln2t_tools.ln2t_tools:main',
        ]},
    include_package_data=True,
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    package_data={
        'ln2t_tools': ['completion/*'],
    },
    data_files=[],  # Remove data_files as we handle it in post_install
)
