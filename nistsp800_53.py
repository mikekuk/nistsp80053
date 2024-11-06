import json
import csv
import os
import shutil
import pickle
from functions import parse_xml, add_options, format_statement_to_markdown, format_statement_to_text, extract_and_format_descriptions, refactor_multiple_entries, generate_sections, replace_placeholder, generate_index_page


class Control:
    def __init__(self) -> None:
        pass

class Baseline:
    def __init__(self, controls: dict = None, name: str = "custom", revision: int = 0) -> None:
        # Set self.controls to a new list if controls is None
        self.controls = controls if controls is not None else []
        self.name = name
        self.revision = revision
        self.options = {}
        
    def __str__(self) -> str:
        return f"NIST SP800-53_r{self.revision} {self.name} Baseline Object"
    
    __repr__ = __str__
    
    def load_json(self, file_path: str) -> None:
        """Loads controls from json. Json should be formatted as:
        {
            'AC-2': {
                'Control Enhancement: ['AC-1 (2)' 'AC-2 (3)']
                },
            AC-3: {'Control Enhancement': []}
        }

        Args:
            file_path (str): path to json file
        """
        with open(file_path, 'r') as file:
            baseline_dict = json.load(file)
        self.controls = baseline_dict


class Library:
    def __init__(self) -> None:
        self._raw_controls = []

class Nist_sp_800_53_control(Control):
    def __init__(self, control_dict: dict) -> None:
        super().__init__()
        fields = {
            'family': None,
            'number': None,
            'title': None,
            'baseline-impact': None,
            'baseline': None, # syntax changed from baseline-impact for R5
            'statement': None,
            'supplemental-guidance': None,
            'control-enhancements': [],
            'related': None,
            'discussion': None,
            'references': None,
        }
        for key in fields.keys():
            if key not in control_dict:
                fields[key] = None
            else:
                try:
                    fields[key] = control_dict[key]
                except KeyError:
                    pass
        self.family = fields['family']
        self.number = fields['number']
        self.title = fields['title']
        if fields['baseline-impact']:
            self.baseline_impact = fields['baseline-impact']
        else:
            self.baseline_impact = fields['baseline']
        self._statement = fields['statement']
        self.supplemental_guidance = fields['supplemental-guidance']
        self._control_enhancements = fields['control-enhancements']
        self.related = fields['related']
        self._discussion_raw = fields['discussion']
        self.discussion = None
        if self._discussion_raw:
            self.discussion = self._discussion_raw[0]['description']['p']
            # Handel some instances where discussion parses as a list
            if isinstance(self.discussion, list):
                self.discussion = " ".join(self.discussion)
        self.references = fields['references']
        self.control_enhancements = {}
        if self._control_enhancements:
            record_type = type(self._control_enhancements['control-enhancement'])
        if self._control_enhancements and record_type == list:
            for control in self._control_enhancements['control-enhancement']:
                if record_type == list:
                    try:
                        self.control_enhancements[control['number']] = Nist_sp_800_53_control(control)
                    except:
                        raise BaseException(f"{self.number}\n\n{control}\n\n{self._control_enhancements}")
        # Needed to handel cases where the control enchantment is only a single item, when it is a dict not list
        elif self._control_enhancements and record_type == dict and len(self._control_enhancements) > 0:
            self.control_enhancements['control-enhancement']['number'] = (Nist_sp_800_53_control(self._control_enhancements))
        # Add options dict and replace sections with format string UIDs

        self.options = add_options(self._statement, self.number)
        
    def set_option(self, option_id: str, value: str) -> None:
        """Set an option for organisation assignment ot section.

        Args:
            option (str): optation UID to set
            value (str): value to write to option
        """
        if option_id in self.options:
            self.options[option_id]['new_text'] = value
        elif option_id in self.get_options():
            enhancement_number = self.get_options()[option_id]['number']
            self.control_enhancements[enhancement_number].options[option_id]['new_text'] = value
            
            
    def get_options(self) -> list[dict]:
        """Returns a dict of options, including for control enhancements.
        
        Returns:
            list[dict]: List of dict options.
        """
 
        # Get options for enhancements
        enhancement_options = {}
        for enhancement_idx in self.control_enhancements.keys():
            enhancement_options = enhancement_options | self.control_enhancements[enhancement_idx].options
        
        
        return self.options | enhancement_options
    
    def get_outstanding_options(self) -> list[dict]:
        """Returns a list of options that have no new text value assigned.
        Returns:
            list[dict]: List of dict options.
        """
            
        # Get options for enhancements
        enhancement_options = {}
        for enhancement_idx in self.control_enhancements.keys():
            enhancement_options = enhancement_options | self.control_enhancements[enhancement_idx].options
        
        refactored_options = refactor_multiple_entries(self.options | enhancement_options)
        outstanding_options = [x for x in refactored_options if not x['new_text']]
        
        
        return outstanding_options

        
    def __str__(self):
        return (
            f"family: {self.family}\n"
            f"number: {self.number}\n"
            f"title: {self.title}\n"
            f"baseline-impact: {self.baseline_impact}\n"
            f"statement: {self._statement}\n"
            f"supplemental-guidance: {self.supplemental_guidance}\n"
            f"control-enhancements: {self.control_enhancements}\n"
            f"related: {self.related}"
        )
        
    __repr__ = __str__

    def get_control_text(self) -> str:
        """Returns raw test fo the control text

        Returns:
            str: string in raw text
        """
        completed_statement = extract_and_format_descriptions(self._statement, {key: value['new_text'] if value['new_text'] else value['original_text']for key, value in self.options.items()})
        return format_statement_to_text(completed_statement)

    def get_control_markdown(self) -> str:
        """Get control as markdown formatted string

        Returns:
            str: string in markdown format
        """
        completed_statement = extract_and_format_descriptions(self._statement, {key: value['new_text'] if value['new_text'] else value['original_text']for key, value in self.options.items()})
        return format_statement_to_markdown(completed_statement)

    def get_control_html(self, stylesheet_path:str = "") -> str:
        """
        Generates an HTML page for a specific control, formatted with a title, description, and other sections,
        optionally including a linked stylesheet.

        Parameters:
        - control (object): An object containing details about the control, including identifier, name, and sections
                            such as control statements, discussion, related sections, enhancements, and baselines.
                            Each section is formatted with specific options and placeholders.
        - stylesheet_path (str): A string path to an optional CSS stylesheet for styling the HTML page.
                                Defaults to an empty string, which omits the stylesheet link in the HTML.

        Returns:
        - str: A string containing the fully formatted HTML page as a template, filled with content from the
            control object. If a stylesheet path is provided, includes a `<link>` tag in the `<head>` section
            for CSS styling.

        Functionality:
        - If `stylesheet_path` is provided, the function includes it in the HTML `<head>` section as a link to
        external CSS.
        - Extracts `options` from the `control` object, replacing placeholders in control text with the appropriate
        values.
        - Retrieves control data sections (e.g., statements, discussion, related items, enhancements) from the
        `generate_sections` function.
        - Uses `replace_placeholder` to substitute any placeholder values within the control text.
        - Constructs the final HTML document with a structured layout including a title, main heading, and various
        sections specific to the control.

        Example Usage:
        ```
        html_output = get_control_html(au_4, "styles.css")
        print(html_output)
        ```

        The function is ideal for dynamically generating HTML representations of control documents, useful for 
        applications needing a web-based presentation of control data.

        """
        
        if stylesheet_path == "":
            style_section =  ""
        else:
            style_section = f'<link rel="stylesheet" href="{stylesheet_path}">'

        options = {key: f'<span class="option" id="{key}"> {value["new_text"]}</span>' if value['new_text'] else f'<span class="option" id="{key}"> {value["original_text"]}</span>' for key, value in self.options.items()}

        control_data = generate_sections(self)

        control_statements_html = replace_placeholder(control_data['statement_html'], options)

        # Example HTML template with placeholders
        template = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{control_identifier} - {control_name}</title>
            {style_section}
        </head>
        <body>
            <h1>{control_identifier}: {control_name}</h1> 
            <div class="section" id="description">
                <h2>Control Description</h2>
                {control_statements_html}
            </div>
            {discussion_section}
            
            {related_section}
            
            {enhancements_section}
            
            {baselines_section}
        </body>
        </html>
        """

        # Populate the template
        html_output = template.format(
            style_section=style_section,
            control_identifier=control_data['control_identifier'],
            control_name=control_data['name'],
            control_statements_html=control_statements_html,
            discussion_section = control_data['discussion_section'],
            related_section = control_data['related_section'],
            enhancements_section=control_data['enhancements_section'],
            # supplemental_guidance_section=control_data['supplemental_guidance_section'],
            # references_section=control_data['references_section'],
            baselines_section=control_data['baselines_section']
        )
        
        return html_output        


class Nist_sp800_53(Library):          
    def __init__(self, xml_path:str) -> None:
        self._xml_path = xml_path
        self._raw_controls = parse_xml(self._xml_path)['controls:controls']['controls:control']
        self.controls = {}
        self.revision = 0
        self._baseline_object = None
        self.baseline = 'All controls'
        self.name = None
        for control in self._raw_controls:
            control_object = Nist_sp_800_53_control(control)
            key = control_object.number
            self.controls[key] = control_object
    
    def __str__(self) -> str:
        control_enhancement_count = 0
        for control in self.controls:
            control_enhancement_count += len(self.controls[control].control_enhancements)
        return f"NIST SP800-53 r{self.revision} Control set with {self.baseline} baseline.\n Containing {len(self.controls)} controls and {control_enhancement_count} control enhancements."
    
    __repr__ = __str__
    
    def load_baseline(self, baseline: Baseline) -> None:
        if baseline.revision != self.revision:
            raise BaseException(f"Incompatible revisions. Library is r{self.revision} and baseline is r{baseline.revision}")
        self.controls = {key: self.controls[key] for key in self.controls if key in baseline.controls}
        for control_id, control_body in self.controls.items():
            control_body.control_enhancements = {key: control_body.control_enhancements[key] for key in control_body.control_enhancements if key in baseline.controls[control_id]['Control Enhancement']}
        self._baseline_object = baseline
        self.baseline = baseline.name
    
    def get_outstanding_options(self) -> list[dict]:
        """Gets a list of all options where the default values have not been changed.

        Returns:
            list[dict]: A list of the outstanding tasks as dicts with. Example of dict format:
                {'id': 'AC-2c_Option1',
                'description': 'Require [Assignment: organization-defined prerequisites and criteria] for group and role membership;',
                'number': 'AC-2c.',
                'original_text': '[Assignment: organization-defined prerequisites and criteria]',
                'new_text': None,
                'control_id': 'AC-2'}
        """
        outstanding_options = []
        for control_id in self.controls.keys():
            outstanding_options += self.controls[control_id].get_outstanding_options()
        return outstanding_options

    def list_controls_from_family(self, family: str) -> list:
        """Gets a lists of the control IDs for a family name.

        Args:
            family (str): Control family name in all caps.

        Returns:
            list: list of control IDs.
        """
        output_list = []
        for key, control in self.controls.items():
            if control.family == family:
                output_list.append(key)
        return output_list


    def export_html_docset(self, output_path: str, stylesheet_path: str = "") -> None:
        """Creates an html document set for the library.

        Args:
            output_path (str): The location of the director to save the document set.
            stylesheet_path (str, optional): Filepath to a css stylesheet.

        """
        # Create the path if it does not already exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        if stylesheet_path != "":
            # Copy css file to output dir
            # Extract the file name from the source file path
            stylesheet_file_name = os.path.basename(stylesheet_path)
            # Create the full destination path
            stylesheet_dest_path = os.path.join(output_path, stylesheet_file_name)
            # Copy the file to the destination directory
            shutil.copy(stylesheet_path, stylesheet_dest_path)
            new_style_sheet_path = stylesheet_file_name
        else:
            new_style_sheet_path = ""

        
        #  Generate control documents
        controls_key_list = self.controls.keys()
        
        for key in controls_key_list:
            file_name = f"{key}.html"
            file_path = os.path.join(output_path, file_name)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.controls.get(key).get_control_html(stylesheet_path = new_style_sheet_path))
                

        file_name = "index.html"
        file_path = os.path.join(output_path, file_name)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(generate_index_page(self, stylesheet_path=new_style_sheet_path))
            
    def save(self, file_name: str = "control_set_export.plk") -> None:
        """Saves object with pickle
   
        Args:
            file_name (str, optional): Name to save file as. Defaults to "control_set_export.plk" Self.name is prepended if it is defined.

        """
        
        if file_name == "control_set_export.plk" and self.name:
            file_name = self.name + "_" + file_name
        
        with open(file_name, 'wb') as f:
            pickle.dump(self, f) 
    
    @classmethod
    def load(cls, filename):
        """Load an instance of the class from a pickle file."""
        with open(filename, 'rb') as f:
            return pickle.load(f)
            
            

class Nist_sp_800_53_r4(Nist_sp800_53):
    def __init__(self) -> None:
        super().__init__(xml_path='etc/800-53-rev4-controls.xml')
        self.revision = 4

class Nist_sp_800_53_r5(Nist_sp800_53):
    def __init__(self) -> None:
        super().__init__(xml_path='etc/SP_800-53_v5_1_XML.xml')
        self.revision = 5
        
        # Initialize an empty list to hold each row as a dictionary
        csv_data = []

        # Open and read the CSV file
        with open('etc/sp800-53b-control-baselines.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            
            # Iterate over each row and add it to the list
            for row in csv_reader:
                csv_data.append(dict(row))  # Convert OrderedDict to regular dict (optional)

         
        #  Below code needed to fix issue where r5 XML files does not contain baselines for control enhancements.
        r5_baselines = {
        row['Control Identifier']: {
            'baselines': [
                level for level, key in {
                    'LOW': 'Security Control Baseline - Low',
                    'MODERATE': 'Security Control Baseline - Moderate',
                    'HIGH': 'Security Control Baseline - High',
                    'PRIVACY': 'Privacy Baseline'
                }.items() if row.get(key, '').strip()  # Include baseline if non-empty
            ]
        }
        for row in csv_data
        }
    
        for control_id in self.controls.keys():
            for enhancement_id in self.controls[control_id].control_enhancements.keys():
                try:
                    self.controls[control_id].control_enhancements[enhancement_id].baseline_impact = r5_baselines[enhancement_id]['baselines']
                except:
                    raise BaseException(f"{control_id} {enhancement_id}")