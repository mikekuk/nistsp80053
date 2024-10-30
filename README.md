
# NIST SP800-53 Control Library

This library provides a structured representation of the NIST Special Publication 800-53 controls. It enables parsing, manipulation, and formatted output of controls as defined in SP800-53 Revision 4 and Revision 5 XML files. The library is designed to help organizations handle, customize, and export NIST controls and their associated metadata in both plain text and Markdown formats.

## Overview

The library is organized into classes that parse and manage NIST control data, baselines, and control enhancements, supporting the creation of custom control sets based on organization-specific requirements.

## Features

- Parse XML representations of NIST SP800-53 control sets.
- Define custom baselines by selecting specific controls.
- Format controls as plain text or Markdown.
- Set organization-specific options for control customization.

## Requirements

- Python 3.7+
- XML files for SP800-53 Revision 4 or Revision 5 controls (`etc/800-53-rev4-controls.xml` and `etc/SP_800-53_v5_1_XML.xml`)

## Installation

To use this library, clone this repository and ensure the required XML files are placed in the correct directory (`etc/`).

## Usage

### Initializing Control Libraries

The library supports both Revision 4 and Revision 5 control sets. Initialize by creating an instance of `Nist_sp_800_53_r4` or `Nist_sp_800_53_r5`, depending on the desired revision.

```python
from your_module import Nist_sp_800_53_r4, Nist_sp_800_53_r5

# For Revision 4 controls
control_set_r4 = Nist_sp_800_53_r4()

# For Revision 5 controls
control_set_r5 = Nist_sp_800_53_r5()
```

### Accessing Controls

Controls are parsed and stored as instances of `Nist_sp_800_53_control`, and each control's information can be printed or accessed programmatically.

```python
# Print control details
print(control_set_r4.controls['AC-1'])
```

### Formatting Controls

Controls can be output in plain text or Markdown formats for easy documentation.

```python
# Get control text
text_output = control_set_r4.controls['AC-1'].get_control_text()

# Get control markdown
markdown_output = control_set_r4.controls['AC-1'].get_control_markdown()
```

### Working with Baselines

Create a custom baseline by defining a set of controls and applying it to a control library instance.

```python
from your_module import Baseline

# Define a baseline with specific controls
custom_baseline = Baseline(controls={'AC-1': {}, 'AC-2': {}}, name="Custom Baseline", revision=4)
control_set_r4.load_baseline(custom_baseline)
```

### Predefined Baselines

The `baselines` directory contains predefined baseline objects for both SP800-53 Revision 4 and Revision 5, with varying impact levels:

- **Revision 4**: `Privacy`, `Low`, `Moderate`, `High`
- **Revision 5**: `Privacy`, `Low`, `Moderate`, `High`

These baseline objects can be directly imported and applied to control libraries for convenience.

## Classes

### `Control`

Base class for all control types. Currently a placeholder for future shared functionality among control classes.

### `Baseline`

Defines a control baseline with a specified set of controls and metadata. Used to filter controls in a library based on the baseline's requirements.

### `Library`

Base class for the control library, initializing with an empty control set. Extended by the NIST control classes.

### `Nist_sp_800_53_control`

Represents an individual control, with fields parsed from the XML representation. Provides methods to set custom options, output control data in text or Markdown, and track control enhancements.

### `Nist_sp800_53`

Parent class for all NIST SP800-53 libraries, handling XML parsing, control loading, and baseline filtering.

### `Nist_sp_800_53_r4` and `Nist_sp_800_53_r5`

Subclasses of `Nist_sp800_53` tailored to Revision 4 and Revision 5 of the SP800-53 standard, respectively. Each initializes with the appropriate XML data path.

## Example

```python
# Initialize the library
nist_controls = Nist_sp_800_53_r5()

# Print control details in Markdown
print(nist_controls.controls['AC-1'].get_control_markdown())

# Load a baseline
baseline = Baseline(controls={'AC-1': {}, 'AC-2': {}}, name="Minimal Baseline", revision=5)
nist_controls.load_baseline(baseline)
```

## License

MIT License. See `LICENSE` file for details.

---
