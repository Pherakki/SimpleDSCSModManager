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

        if len(self.flags):
            default_option = options.get("Default", options["Flags"][0]["Name"])
            self.flags[default_option].value = True
            
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
    source = os.path.join(path_prefix, 'modoptions', *source.split('/'))
    destination = os.path.join(path_prefix, 'modfiles', *destination.split('/'))
    if os.path.exists(source):
        os.makedirs(os.path.split(destination)[0], exist_ok=True)
        if os.path.isfile(source):
            shutil.copy2(source, destination)
        elif os.path.isdir(source):
            shutil.copytree(source, destination, dirs_exist_ok=True)
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
    return all(char == '.' for char in string) and len(string) > 1

##########################
# DEFINE CYMIS INSTALLER #
##########################
class CymisInstaller:
    def __init__(self):
        super().__init__()
        self.flag_table = {}
        self.wizard_pages = []
        self.installation_steps = []
        self.version = None
        self.enable_debug=None
        self.log = None
        
    @classmethod
    def init_from_script(cls, filepath, log):
        with open(filepath, 'r') as F:
            cymis = json.load(F)
        
        instance = cls()
        instance.version = cymis['Version']
        instance.enable_debug = cymis.get("DebugLog", False)
        if instance.enable_debug: 
            instance.log = log
        path_prefix = os.path.split(filepath)[0]
        
        for page in cymis["Wizard"]:
            wizard_page = CymisInstallerPage(page, instance.log)
            instance.wizard_pages.append(wizard_page)
            instance.flag_table.update(wizard_page.retrieve_flags())

        instance.installation_steps = [CymisInstallationStep(path_prefix, step_info, instance.flag_table, instance.log) for step_info in cymis["Install"]]
            
        return instance
    
    def install_mod(self):
        if self.log is not None:
            self.log("Checking flag table before install...")
            for flag_name, flag_status in self.flag_table.items():
                self.log(f"{flag_name} is {flag_status}.")
        for installer_step in self.installation_steps:
            if installer_step.check_should_execute():
                installer_step.execute_step()
            
class CymisInstallerPage:
    def __init__(self, page, log=None):
        self.title = page.get("Title", "No Title")
        self.contents = page.get("Contents")
        self.flags = [wizard_flags[flag_def["Type"]](flag_def) for flag_def in page.get("Flags", [])]
        self.log = log
        
        if log is not None:
            for flag in self.flags:
                for flag_name, _ in flag.get_flag_status().items():
                    self.log(f"Found flag: {flag.type} {flag_name}")
        
    def retrieve_flags(self):
        retval = {}
        for flag_def in self.flags:
            flag_status = flag_def.get_flag_status()
            retval.update(flag_status)
        return retval
    
class CymisInstallationStep:
    def __init__(self, path_prefix, step_info, flag_table, log):            
        execution_condition = step_info.get("if")
        if execution_condition is None:
            def check():   
                if log is not None:
                    log("Auto-pass: No 'if' statement.")
                return True
        elif type(execution_condition) == str:
            def check():
                result = flag_table[execution_condition]
                if log is not None:
                    log(f"Will {'' if result else 'not '}execute; {execution_condition} is {result}.")
                return result
        elif type(execution_condition) == dict:
            assert len(execution_condition) == 1, f"More than one boolean operator in dictionary: {execution_condition}."
            operator_name, operator_arguments = list(execution_condition.items())[0]
            def check():
                result = boolean_operators[operator_name](operator_arguments, boolean_operators, flag_table)
                if log is not None:
                    log(f"Will {'' if result else 'not '}execute; compound statement is {result}.")
                return result
        else:
            assert 0, f"Unrecognised installation condition type: {type(execution_condition)}. Should be a string, dict, or not present."
        
        self.check_should_execute = check
        self.instructions = step_info["then"]
        self.path_prefix = path_prefix
    
    def execute_step(self):
        for instruction in self.instructions:
            self.get_rule(instruction["rule"])(self.path_prefix, **instruction)

    def get_rule(self, rule):
        return installation_rules[rule]