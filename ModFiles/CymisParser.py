import json
import os
import shutil

from Utils.Path import splitpath


#####################
# DEFINE FLAG TYPES #
#####################
class HiddenFlag:
    def __init__(self, options):
        self.name = options['Name']
        self.type = options['Type']
        self.value = options['Default']
        
    def get_flag_status(self):
        return {self.name: self.value}
        
class Flag:
    def __init__(self, options):
        self.name = options['Name']
        self.type = options['Type']
        self.description = options.get("Description", "No description.")
        self.value = options.get("Default", False)
    
    def get_flag_status(self):
        return {self.name: self.value}
    
class ChooseOne:
    def __init__(self, options):
        self.type = options['Type']
        self.description = options.get("Description", "No description.")
        self.flags = {flag_def['Name']: Flag({**flag_def, 'Type': 'Flag'}) for flag_def in options.get("Flags", [])}
        for flag in self.flags.values():
            flag.value = False
        if "Default" in options:
            self.flags[options["Default"]] = True
            
    def get_flag_status(self):
        return {flag_name: flag.value for flag_name, flag in self.flags.items()}
        

wizard_flags = {class_.__name__: class_ for class_ in [HiddenFlag, Flag, ChooseOne]}

############################
# DEFINE BOOLEAN OPERATORS #
############################
def and_operator(arguments, operator_list, flag_list):
    parsed_flags = []
    for item in arguments:
        if type(item) == dict:
            assert len(item) == 1, f"More than one boolean operator in dictionary: {item}."
            operator_name, operator_arguments = list(item.items())[0]
            parsed_flags.append(operator_list[operator_name](operator_arguments, operator_list, flag_list))
        else:
            parsed_flags.append(flag_list[item])
    return all(parsed_flags)

def or_operator(arguments, operator_list, flag_list):
    parsed_flags = []
    for item in arguments:
        if type(item) == dict:
            assert len(item) == 1, f"More than one boolean operator in dictionary: {item}."
            operator_name, operator_arguments = list(item.items())[0]
            parsed_flags.append(operator_list[operator_name](operator_arguments, operator_list, flag_list))
        else:
            parsed_flags.append(flag_list[item])
    return any(parsed_flags)

def not_operator(arguments, operator_list, flag_list):
    to_flip = None
    
    if type(arguments) == dict:
        assert len(arguments) == 1, f"More than one boolean operator in dictionary: {arguments}."
        operator_name, operator_arguments = list(arguments.items())[0]
        to_flip = operator_list[operator_name](operator_arguments, operator_list, flag_list)
    else:
        to_flip = flag_list[arguments]
        
    return not(to_flip)

boolean_operators = {'and': and_operator, 
                     'or': or_operator, 
                     'not': not_operator}

#############################
# DEFINE INSTALLATION RULES #
#############################
def copy_rule(path_prefix, rule, source, destination):
    validate_path(source)
    validate_path(destination)
    source = os.path.join(path_prefix, *source.split('/'))
    destination = os.path.join(path_prefix, 'modfiles', *destination.split('/'))
    if os.path.exists(source):
        os.makedirs(os.path.split(destination)[0], exist_ok=True)
        if os.path.isfile(source):
            shutil.copy2(source, destination)
        elif os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            assert 0, f"{source} is neither a file nor a directory."

installation_rules = {'copy': copy_rule}

################
# SAFETY UTILS #
################
def validate_path(path):
    path_directories = splitpath(path)
    assert not(any([check_if_only_periods(item) for item in path_directories])), "Paths may not contain relative references."

def check_if_only_periods(string):
    return all(char == '.' for char in string)

##########################
# DEFINE CYMIS INSTALLER #
##########################

class CymisInstaller:
    def __init__(self):
        self.flag_table = {}
        self.wizard_pages = []
        self.installation_steps = []
        
    @classmethod
    def init_from_script(cls, filepath):
        with open(filepath, 'r') as F:
            cymis = json.load(F)
        
        instance = cls()
        path_prefix = os.path.split(filepath)[0]
        
        for page in cymis["Wizard"]:
            wizard_page = CymisInstallerPage(page)
            instance.wizard_pages.append(wizard_page)
            instance.flag_table.update(wizard_page.retrieve_flags())
        instance.installation_steps = [CymisInstallationStep(path_prefix, step_info, instance.flag_table) for step_info in cymis["Install"]]
            
        return instance
    
    def install_mod(self):
        for installer_step in self.installation_steps:
            if installer_step.check_should_execute():
                installer_step.execute_step()
            
class CymisInstallerPage:
    def __init__(self, page):
        self.title = page.get("Title", "No Title")
        self.contents = page.get("Contents")
        self.flags = [wizard_flags[flag_def["Type"]](flag_def) for flag_def in page.get("Flags", [])]
        
    def retrieve_flags(self):
        retval = {}
        for flag_def in self.flags:
            retval.update(flag_def.get_flag_status())
        return retval
    
class CymisInstallationStep:
    def __init__(self, path_prefix, step_info, flag_table):
        execution_condition = step_info.get("if")
        if execution_condition is None:
            self.check_should_execute = lambda: True
        elif type(execution_condition) == str:
            self.check_should_execute = lambda: flag_table[execution_condition]
        elif type(execution_condition) == dict:
            assert len(execution_condition) == 1, f"More than one boolean operator in dictionary: {execution_condition}."
            operator_name, operator_arguments = list(execution_condition.items())[0]
            self.check_should_execute = lambda: boolean_operators[operator_name](operator_arguments, boolean_operators, flag_table)
        else:
            assert 0, f"Unrecognised installation condition type: {type(execution_condition)}. Should be a string, dict, or not present."
        
        self.execute_step = [lambda: installation_rules[kwargs["rule"]](path_prefix, **kwargs) for kwargs in step_info["then"]]
