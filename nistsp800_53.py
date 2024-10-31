from functions import parse_xml, add_options, format_statement_to_markdown, format_statement_to_text, extract_and_format_descriptions

class Control:
    def __init__(self) -> None:
        pass

class Baseline:
    def __init__(self, controls: dict = None, name: str = "custom", revision: int = 0) -> None:
        # Set self.controls to a new list if controls is None
        self.controls = controls if controls is not None else []
        self.name = name
        self.revision = revision
        
    def __str__(self) -> str:
        return f"NIST SP800-53_r{self.revision} {self.name} Baseline Object"
    
    __repr__ = __str__


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
            'related': None
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
            self.control_enhancements['number'] = (Nist_sp_800_53_control(self._control_enhancements))
        # Add options dict and replace sections with format string UIDs
        self.options = add_options(self._statement)
        
    def set_option(self, option: str, value: str) -> None:
        """Set an option for organisation assignment ot section.

        Args:
            option (str): optation UID to set
            value (str): value to write to option
        """
        self.options[option]['new_text'] = value
            
        
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
        

class Nist_sp800_53(Library):          
    def __init__(self, xml_path:str) -> None:
        self._xml_path = xml_path
        self._raw_controls = parse_xml(self._xml_path)['control']
        self.controls = {}
        self.revision = 0
        self._baseline_object = None
        self.baseline = 'All controls'
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
        
    

class Nist_sp_800_53_r4(Nist_sp800_53):
    def __init__(self) -> None:
        super().__init__(xml_path='etc/800-53-rev4-controls.xml')
        self.revision = 4

class Nist_sp_800_53_r5(Nist_sp800_53):
    def __init__(self) -> None:
         super().__init__(xml_path='etc/SP_800-53_v5_1_XML.xml')
         self.revision = 5

