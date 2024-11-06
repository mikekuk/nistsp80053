# NIST SP800-53 Control Library

This Python library provides a structured framework for managing the controls specified in the NIST Special Publication 800-53. It allows for parsing, customization, and export of NIST controls from both Revision 4 and Revision 5 XML files. Users can tailor controls to organization-specific needs, apply baselines, set options, and output controls in various formats, including HTML.

## Overview

The library is designed around classes that handle NIST control data, baselines, and enhancements, offering flexibility in customizing control sets based on privacy, impact levels, and compliance requirements. Predefined baselines and an easy-to-use API simplify integrating this library into compliance workflows.

## Features

- **XML Parsing:** Parses SP800-53 Revision 4 and 5 XML files for easy control access and manipulation.
- **Control Customization:** Allows setting custom values for organization-specific variables within controls.
- **Baseline Support:** Supports predefined baselines for Privacy, Low, Moderate, and High impact levels across both Revision 4 and 5. Additionally, a JSIG baseline is available for SAP systems under Revision 4.
- **Output Formatting:** Outputs controls as plain text, Markdown, or HTML with optional CSS styling.
- **HTML Export:** Exports control sets as a fully structured HTML document set for web or internal documentation.

## Requirements

- Python 3.7+
- NIST SP800-53 XML files for Revision 4 (`etc/800-53-rev4-controls.xml`) or Revision 5 (`etc/SP_800-53_v5_1_XML.xml`). Both included in this repository.
- Optional: CSV for predefined baselines (`etc/sp800-53b-control-baselines.csv`). Included in this repository.
- Currently requires xmltodict library. Future releases will remove this dependency so that it runs on core python only.
  
## Usage

### Initializing Control Libraries

The library supports both SP800-53 Revision 4 and Revision 5. To get started, create an instance of `Nist_sp_800_53_r4` or `Nist_sp_800_53_r5`:

```python
from nistsp800_53 import Nist_sp_800_53_r4, Nist_sp_800_53_r5

# For Revision 4 controls
control_set_r4 = Nist_sp_800_53_r4()

# For Revision 5 controls
control_set_r5 = Nist_sp_800_53_r5()
```

### Applying Baselines

You can apply predefined or custom baselines to focus on specific control sets. Revision 4 and 5 support Privacy, Low, Moderate, and High impact level baselines. Revision 4 also includes a JSIG baseline for SAP systems.

```python
from baselines import baseline_jsig

# Load JSIG baseline for Revision 4
control_set_r4.load_baseline(baseline_jsig)
print(control_set_r4)
```

### Setting Custom Options

Controls can include placeholders for organization-specific values, known as "options." These can be set programmatically.

```python
# Set options for a control
next_option = control_set_r4.get_outstanding_options()[0]
control_set_r4.controls[next_option['control_id']].set_option(next_option['id'], "Custom Value")
```

### Exporting to HTML

You can export the control set as HTML, with optional CSS for styling. Each control will be saved as a separate HTML document.

```python
control_set_r4.export_html_docset(output_path="example_docs", stylesheet_path="styles.css")
```

## Library Classes

### `Control`

Base class for all control types, enabling shared functionality across control classes.

### `Baseline`

Defines a baseline with a specified set of controls. Baselines filter controls based on defined impact levels or organizational criteria.

### `Library`

Parent class for the control library. Initializes with an empty control set.

### `Nist_sp_800_53_control`

Represents an individual control, with fields parsed from XML. Supports setting custom options, exporting control data, and formatting enhancements.

### `Nist_sp800_53`, `Nist_sp_800_53_r4`, and `Nist_sp_800_53_r5`

Core classes that manage controls and apply baselines for SP800-53 Revision 4 and Revision 5 standards. Each initializes with the appropriate XML data path and revision-specific baselines.

## Example

Here's a full example of initializing, setting options, and exporting controls:

```python
from nistsp800_53 import Nist_sp_800_53_r4, Nist_sp_800_53_r5
from baselines import baseline_jsig

# Initialize library with Revision 4 controls
control_set = Nist_sp_800_53_r4()

# Apply JSIG baseline for SAP systems
control_set.load_baseline(baseline_jsig)

# Set a custom option
next_option = control_set.get_outstanding_options()[0]
control_set.controls[next_option['control_id']].set_option(next_option['id'], "Custom Value")

# View control as Markdown
print(control_set.controls['AC-1'].get_control_markdown())

# Export controls as HTML with styling
control_set.export_html_docset(output_path="html_docs", stylesheet_path="styles.css")
```

This example highlights the full process: initializing controls, applying baselines, customizing options, and exporting documents. With flexible baseline and formatting options, the library adapts easily to organization-specific security control workflows.
