# CFM Toolbox Editor

[![Versions][versions-image]][versions-url]
[![PyPI][pypi-image]][pypi-url]
[![License][license-image]][license-url]

[versions-image]: https://img.shields.io/pypi/pyversions/cfmtoolbox

[versions-url]: https://github.com/KIT-TVA/cfmtoolbox-editor/blob/main/pyproject.toml

[pypi-image]: https://img.shields.io/pypi/v/cfmtoolbox

[pypi-url]: https://pypi.org/project/cfmtoolbox/

[license-image]: https://img.shields.io/pypi/l/cfmtoolbox

[license-url]: https://github.com/KIT-TVA/cfmtoolbox-editor/blob/main/LICENSE

The CFM Toolbox Editor is a core component of the CFM Toolbox (see [CFM Toolbox Documentation](https://kit-tva.github.io/cfmtoolbox/)), providing a graphical interface for creating, editing, and visualizing cardinality-based feature models. It is designed to simplify the complexity of working with feature models while offering an intuitive and user-friendly experience. The editor is particularly tailored to handle the intricacies of cardinality-based feature models, making it a powerful tool for researchers, developers, and practitioners in software product line engineering.

## Key Features of the CFM Toolbox Editor

- **Graphical Creation of Feature Models**: Users can visually design feature models.
- **Intuitive User Interface**: The editor provides a clean and easy-to-navigate interface, making it accessible for
  both beginners ans advanced users.

## Use Cases for the CFM Toolbox Editor

- Research and Education: Researchers and students can use the editor to experiment with cardinality-based feature
  modeling and explore advanced concepts in software engineering.
- Software Product Line Engineering: The editor is ideal for designing and managing feature models for software product
  lines, where variability and commonality need to be explicitly defined.
- Industrial Applications: The editor can be used in industrial settings to model complex systems and manage product
  variability in large-scale projects.

[Read the documentation](https://kit-tva.github.io/cfmtoolbox-editor/) to learn more.

# Getting Started

The CFM Toolbox editor, it's dependencies, and core plugins can easily be installed from the Python Package Index (PyPI)
using the following command:

```bash
pip3 install cfmtoolbox
```

## Running the CFM Toolbox Editor

After the installation, the CFM Toolbox can be run from the command line using the following command:

```shell
python3 -m cfmtoolbox --import example.uvl --export example.uvl edit
```
