import xml.etree.ElementTree as ET
import re

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

def parse_xml(file_path:str) -> dict:
    # Define the namespaces used in your XML file
    namespaces = {
        'controls': 'http://scap.nist.gov/schema/sp800-53/feed/2.0',
        'xhtml': 'http://www.w3.org/1999/xhtml',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }

    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    # Convert the root element to a dictionary
    parsed_dict = parse_element(root)
    
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