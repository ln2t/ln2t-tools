from setuptools import setup, find_packages

# Function to read the contents of the requirements file
def read_requirements():
    with open('requirements.txt') as req:
        return req.read().splitlines()

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
    package_data={},
    data_files=[
        ('share/bash-completion/completions', ['ln2t_tools/completion/ln2t_tools_completion.bash']),
    ],
)
