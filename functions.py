import xml.etree.ElementTree as ET
import xmltodict
import re
import os

# Define a function to parse the XML to a dictionary recursively
def parse_element(element):
    parsed_data = {}
    
    # Collect attributes if any
    if element.attrib:
        parsed_data.update(element.attrib)
    
    # Initialize a text buffer for paragraphs and regular text content
    text_buffer = []
    text_content = ""
    
    # Process element's children
    for child in element:
        tag = child.tag.split('}', 1)[-1]  # Remove namespace
        
        if tag == 'p':  # For paragraph tags, just collect text
            if child.text:
                text_buffer.append(child.text.strip())
        else:
            # Add buffered paragraph text to text_content with double line breaks
            if text_buffer:
                text_content += '\n\n'.join(text_buffer) + '\n\n'
                text_buffer = []  # Reset buffer
            
            # Check if child has only text or is a simple tag like <baseline>
            if child.text and not list(child):  # No nested elements
                # Directly assign the text if the tag already doesn't exist
                if tag in parsed_data:
                    if isinstance(parsed_data[tag], list):
                        parsed_data[tag].append(child.text.strip())
                    else:
                        parsed_data[tag] = [parsed_data[tag], child.text.strip()]
                else:
                    parsed_data[tag] = child.text.strip()
            else:
                # Otherwise, recursively parse the child element
                child_data = parse_element(child)
                if child_data:
                    if tag in parsed_data:
                        if isinstance(parsed_data[tag], list):
                            parsed_data[tag].append(child_data)
                        else:
                            parsed_data[tag] = [parsed_data[tag], child_data]
                    else:
                        parsed_data[tag] = child_data

    # Final check if any paragraph text remains
    if text_buffer:
        text_content += '\n\n'.join(text_buffer)
    
    # If we have accumulated paragraph text, add it to parsed_data
    if text_content.strip():
        parsed_data['text'] = text_content.strip()
    
    return parsed_data


def parse_xml(file_path: str) -> dict:
    """
    Parses the XML file at the given file path and returns a dictionary representation,
    ensuring that specified elements are always treated as lists for consistency and
    ignoring <a> and <q> tags, preserving only their text content.

    Args:
        file_path (str): The path to the XML file to be parsed.

    Returns:
        dict: A dictionary representation of the XML file.
    """
    # Open and read the XML file
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    # Remove <a> and <q> tags but keep their text content
    xml_content = re.sub(r'</?(a|q)[^>]*>', '', xml_content)

    # Specify the elements that should always be treated as lists
    elements_to_force_as_list = (
        'controls:control',
        'control-enhancement',
        'baseline',
        'related',
        'discussion',
    )

    # Parse the XML content into a dictionary, forcing specified elements as lists
    parsed_dict = xmltodict.parse(
        xml_content,
        force_list=elements_to_force_as_list
    )

    return parsed_dict



def add_options(statements: dict, id: str = "") -> dict:
    # Initialize options_dict to collect all unique IDs and their matches
    options_dict = {}
    
    # Check if the input is a list of statements
    if isinstance(statements, list):
        for statement in statements:
            # Extract the statement number and statement content
            statement_number = statement.get("number", id).strip()
            statement_content = statement.get("description", "")

            # Extract all text within square brackets in the current statement's description

            matches = re.findall(r'\[(.*?)\]', statement_content)
            
            # Replace matches with unique IDs in the description
            for index, match in enumerate(matches):
                # Create a unique ID
                unique_id = f"{statement_number.replace('.', '')}_Option{index + 1}"
                # Store the match in options_dict with the required structure
                options_dict[unique_id] = {
                    "description": statement_content,  # Store the full description
                    "number": statement_number,
                    "original_text": '[' + match + ']',
                    "new_text": None,
                    "control_id": id,
                }
                # Replace the match in the description with curly brackets
                statement["description"] = statement["description"].replace(f'[{match}]', f'{{{unique_id}}}')

            # # Add the list of options to the current statement
            # statement["options"] = {uid: options_dict[uid] for uid in options_dict.keys()}

            # If there are nested statements, call the function recursively
            if "statement" in statement:
                nested_options_dict = add_options(statement["statement"], id)
                options_dict.update(nested_options_dict)

    # If statements is a single statement dictionary (not a list)
    elif isinstance(statements, dict):
        # Extract the statement number and statement content
        statement_number = statements.get("number", id).strip()
        statement_content = statements.get("description", "")
        if not statement_content:
            statement_content = ""
        # Extract all text within square brackets in the current statement's description
        matches = re.findall(r'\[(.*?)\]', statement_content)
        
        # Replace matches with unique IDs in the description
        for index, match in enumerate(matches):
            # Create a unique ID
            unique_id = f"{statement_number.replace('.', '')}_Option{index + 1}"
            # Store the match in options_dict with the required structure
            options_dict[unique_id] = {
                "description": statement_content,  # Store the full description
                "number": statement_number,
                "original_text": '[' + match + ']',
                "new_text": None,
                "control_id": id
            }
            # Replace the match in the description with curly brackets
            statements["description"] = statements["description"].replace(f'[{match}]', f'{{{unique_id}}}')

        # Add the list of options to the current statement
        statements["options"] = {uid: options_dict[uid] for uid in options_dict.keys()}

        # If there are nested statements, call the function recursively
        if "statement" in statements:
            nested_options_dict = add_options(statements["statement"], id)
            options_dict.update(nested_options_dict)

    return options_dict  # Return the options_dict when processing is complete



def format_statement_to_text(structure: dict, indent: int=0) -> str:
    """Formats the control statement to a raw string

    Args:
        structure (dict): The _statement form the Nist_sp800-53_control class
        indent (int, optional): amount to intent per paragraph. Defaults to 0.

    Returns:
        str: formatted single string
    """
    result = ""
    indent_space = "  " * indent  # Indentation for each level

    if isinstance(structure, dict):
        # Handle number if present
        if 'number' in structure:
            result += f"{indent_space*2}{structure['number']} "
        
        # Handle description if present
        if 'description' in structure:
            result += f"{indent_space}{structure['description']}\n"
        
        # Recursively process 'statement' key if present
        if 'statement' in structure:
            result += format_statement_to_text(structure['statement'], indent + 1)

    elif isinstance(structure, list):
        # Process each item in the list recursively
        for item in structure:
            result += format_statement_to_text(item, indent)

    return result

def format_statement_to_markdown(structure: dict, indent:int=0) -> str:
    """Formats the control statement to a markdown

    Args:
        structure (dict): The _statement form the Nist_sp800-53_control class
        indent (int, optional): amount to intent per paragraph. Defaults to 0.

    Returns:
        str: formatted single string
    """
    result = ""
    indent_space = "    " * indent  # Indentation for each level (4 spaces per level)

    if isinstance(structure, dict):
        # Handle number and description, making number bold in Markdown
        if 'number' in structure and 'description' in structure:
            result += f"{indent_space}- **{structure['number']}** {structure['description']}\n"
        
        # Recursively process 'statement' key if present
        if 'statement' in structure:
            result += format_statement_to_markdown(structure['statement'], indent + 1)

    elif isinstance(structure, list):
        # Process each item in the list recursively
        for item in structure:
            result += format_statement_to_markdown(item, indent)

    return result

def format_string(template: str, values: dict) -> str:
    """
    Formats a string by replacing placeholders with values from a dictionary.

    Args:
        template (str): The string template containing placeholders.
        values (dict): A dictionary containing keys and their corresponding values.

    Returns:
        str: The formatted string with placeholders replaced by values from the dictionary.
    """
    try:
        return template.format(**values)
    except KeyError as e:
        raise ValueError(f"Missing a required key in values: {e}")

def extract_and_format_descriptions(data, format_values):
    """
    Recursively extract and format all values associated with the key 'description' 
    from a nested dictionary or list structure, returning the modified structure.

    Args:
        data (dict or list): The nested dictionary or list to traverse.
        format_values (dict): A dictionary containing keys for formatting descriptions.

    Returns:
        dict or list: The same structure as `data`, with all 'description' values formatted.
    """
    if isinstance(data, dict):
        # Create a copy of the dictionary to avoid modifying the original data
        formatted_data = {}
        for key, value in data.items():
            # Format 'description' if it exists in the current dictionary level
            if key == 'description' and isinstance(value, str):
                formatted_data[key] = value.format(**format_values)
            # Recurse for nested dictionaries or lists
            elif isinstance(value, (dict, list)):
                formatted_data[key] = extract_and_format_descriptions(value, format_values)
            else:
                formatted_data[key] = value  # Keep other values unchanged

        return formatted_data

    elif isinstance(data, list):
        # Recurse through each item in the list
        return [extract_and_format_descriptions(item, format_values) if isinstance(item, (dict, list)) else item for item in data]

    return data  # If data is neither dict nor list, return it unchanged

def refactor_dict(input_dict: dict) -> dict:
    # Extract the top-level key and the nested dictionary
    if len(input_dict) != 1:
        raise ValueError("Input dictionary should have exactly one top-level key.")
    
    # Get the single key and value pair from the dictionary
    title, content = next(iter(input_dict.items()))
    
    # Combine the title with the contents of the nested dictionary
    refactored = {'id': title, **content}
    return refactored

def refactor_multiple_entries(input_dict):
    # Refactor each entry in the input dictionary
    return [
        {'id': title, **content} for title, content in input_dict.items()
    ]
    

# Functions for generating html pages


def generate_statement_html(control_data):
    """
    Generates HTML content from control statements.

    Args:
        control_data (dict): The control data containing statements.

    Returns:
        str: An HTML string representing the control statements.
    """
    def process_statements(statements_list):
        html_content = ''
        for statement in statements_list:
            number = statement.get('number', '').strip()
            description = statement.get('description', '').strip()

            # Replace placeholders in the description if necessary
            # (Assuming you have some placeholder replacement logic)
            # description = replace_placeholders(description)

            # Start with the statement number and description
            html_content += f"<p><strong>{number}</strong> {description}</p>\n"

            # If there are sub-statements, process them recursively
            if 'statement' in statement:
                sub_statements = statement['statement']
                html_content += "<ul>\n"
                for sub_statement in sub_statements:
                    html_content += "<li>\n"
                    # Recursive call to process sub-statements
                    html_content += process_statements([sub_statement])
                    html_content += "</li>\n"
                html_content += "</ul>\n"
        return html_content

    # Start processing from the top-level statements
    statements = control_data.get('statement', [])
    control_statements_html = process_statements(statements)
    
    return control_statements_html

def dict_to_html(data: dict) -> str:
    """
    Converts the dictionary structure into an HTML string.

    Args:
        data (dict): The dictionary containing the control data.

    Returns:
        str: An HTML string representing the control data.
    """
    # Initialize the HTML content
    html_content = ''

    # If there is a description, add it as a paragraph
    if data.get('description'):
        html_content += f"<p>{data['description']}</p>\n"

    # Process the 'statement' key if it exists
    if 'statement' in data:
        html_content += process_statements(data['statement'])

    return html_content

def process_statements(statements) -> str:
    """
    Processes a list or single statement and returns an HTML string.

    Args:
        statements (list or dict): The statement(s) to process.

    Returns:
        str: An HTML string representing the statements.
    """
    html = ''

    # Ensure statements is a list for consistent processing
    if isinstance(statements, dict):
        statements = [statements]

    # Start an ordered list
    html += '<ol>\n'
    for statement in statements:
        html += process_single_statement(statement)
    html += '</ol>\n'

    return html

def process_single_statement(statement) -> str:
    """
    Processes a single statement dictionary and returns an HTML string.

    Args:
        statement (dict): The statement to process.

    Returns:
        str: An HTML string representing the statement.
    """
    html = '<li>\n'

    # Extract number and description
    number = statement.get('number', '')
    description = statement.get('description', '')

    # Add number and description to the HTML
    if number:
        html += f"<strong>{number}</strong> "
    if description:
        html += f"{description}\n"

    # If there are nested statements, process them recursively
    if 'statement' in statement:
        html += process_statements(statement['statement'])

    html += '</li>\n'

    return html


def replace_placeholder(text, options):
    # Replace any placeholder in curly braces with values from options
    for key, value in options.items():
        text = text.replace(f"{{{key}}}", value)
    return text



# Generate the variable sections
def generate_sections(control):
    
    name = control.title
    
    control_identifier = control.number
    
    family = control.family
    
    statement_html = dict_to_html(control._statement)
    
    # Control Discussion Section
    discussion_section = ''
    if control.discussion:
        discussion_section = f"""
        <div class="section" id="discussion">
            <h2>Discussion</h2>
            <p>{control.discussion}</p>
        </div>
        """

    
    # Control Enhancements Section
    enhancements_section = ''

    if control.control_enhancements:
        enhancements_html_list = []
        for key in control.control_enhancements.keys():
            enhancement = control.control_enhancements.get(key)
            enhancement_options = {key: f'<span class="option" id="{key}"> {value["new_text"]}</span>' if value['new_text'] else f'<span class="option" id="{key}"> {value["original_text"]}</span>' for key, value in enhancement.options.items()}
            discussion_html = ""
            if enhancement.discussion:
                discussion_html = f"<h3>Discussion</h3><p>{enhancement.discussion}"
                
            # related_html = ""
            # if enhancement.related:
            #     related_links = [f'<a href="./{x}.html">{x}</a>' for x in enhancement.related if x]
            #     related_section = f"""
            #     <h3>Related Controls</h3>
            #     {", ".join(related_links)}
            #     """
            
            enhancements_html_list.append(f"<li><strong>{key} - {enhancement.title}</strong> <p>{replace_placeholder(dict_to_html(enhancement._statement), enhancement_options)}</p></li>")

        enhancements_section = f"""
        <div class="section" id="enhancements">
            <h2>Control Enhancements</h2>
            <ul>
                {" ".join(enhancements_html_list)}
            <ul>                
        </div>
        
        """
         

    # Supplemental Guidance Section
    supplemental_guidance_section = ''
    if control.supplemental_guidance:
        supplemental_guidance_section = f"""
        <div class="section" id="guidance">
            <h2>Supplemental Guidance</h2>
            <p>{control.supplemental_guidance}</p>
        </div>
        """
        
        
    # Related Controls Section
    related_section = ''
    if control.related:
        related_links = [f'<a href="./{x}.html">{x}</a>' for x in control.related if x]
        related_section = f"""
        <div class="section" id="related">
            <h2>Related Controls</h2>
            {", ".join(related_links)}
        </div>
        """
    # # References Section
    references_section = ''
    # if ac_2.references:
    #     references_section = f"""
    #     <div class="section">
    #         <h2>References</h2>
    #         <p>{data['references']}</p>
    #     </div>
    #     """

    # Baselines Section
    baselines_section = ''
    if control.baseline_impact:
        baselines = ', '.join(control.baseline_impact)
        baselines_section = f"""
        <div class="section" id="baselines">
            <h2>Baselines</h2>
            <p>{baselines}</p>
        </div>
        """


    control_data = {
        'name': name, 
        'control_identifier': control_identifier, 
        'family': family,
        'statement_html': statement_html,
        'supplemental_guidance_section': supplemental_guidance_section, 
        'related_section': related_section,
        'references_section': references_section,
        'baselines_section': baselines_section,
        'discussion_section': discussion_section,
        'enhancements_section': enhancements_section
    }
    return control_data


def get_control_html(control, stylesheet_path:str = "") -> str:
    
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

    options = {key: value['new_text'] if value['new_text'] else value['original_text']for key, value in control.options.items()}

    control_data = generate_sections(control)

    control_statements_html = replace_placeholder(control_data['statement_html'], options)
    # control_enhancement_html = replace_placeholder(control_data['enhancements_section'], options)

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

def generate_index_page(library, stylesheet_path: str = "") -> str:
    
    
    if stylesheet_path == "":
        style_section =  ""
    else:
        style_section = f'<link rel="stylesheet" href="{stylesheet_path}">'
        
        
        
    name = library.name
    
    def generate_family_html(library, family: str) -> str:
        controls_list = library.list_controls_from_family(family)
        family_html = f"""
        <div class=section id=family>
            <h2>{family}</h2>
        """
        for control_idx in controls_list:
            family_html += f"""\n\t<a href="./{control_idx}.html"><h3>{control_idx} - {library.controls.get(control_idx).title}</h3></a>"""
        
        family_html += "\n</div>"
        
        return family_html
    
    
    families_list = list(set([library.controls[x].family for x in library.controls]))
    families_list.sort()
    families_sections = [generate_family_html(library, x) for x in families_list]
    families_section = "\n".join(families_sections)
            
    template = """<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{name} - Control Index</title>
        {style_section}
    </head>
    <body>
        <h1>{name} - Control Index</h1> 
        
        {families_section}
        
    </body>
    </html>
    """
    
    html_output = template.format(
        name = name,
        style_section = style_section,
        families_section = families_section
    )
    
    return html_output