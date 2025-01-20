# CFM Toolbox Editor

The Editor is a command plugin for the CFM Toolbox framework
(see [CFM Toolbox Documentation](https://kit-tva.github.io/cfmtoolbox/)). It adds the `edit` command which enables the
visual editing of a CFM Model.

## Installation and Usage
If you have not installed the CFM Toolbox yet, you can do so by running the following command (possibly without the 3):
```shell
pip3 install cfmtoolbox
```
### Local usage
To use the Editor locally, clone the repository and run the following commands in the root directory:
```shell
poetry install
poetry run pip install -e .
```
Now you are ready to edit your CFM. For example for a model in the UVL file format, run (again possibly without the 3):
```shell
poetry run python3 -m cfmtoolbox --import example.uvl --export example.uvl edit
```
For more information on how to use the Toolbox, also refer to the
[CFM Toolbox Documentation](https://kit-tva.github.io/cfmtoolbox/).