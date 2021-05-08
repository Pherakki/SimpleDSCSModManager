import csv
import os
import shutil

from PyQt5 import QtCore

from .ScriptPatching import patch_scripts
from Utils.Multithreading import PoolChain
from Utils.Path import splitpath
    

class generate_patch_mt(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    
    def __init__(self, rules_dictionary, patchers, working_dir, resources_dir, threadpool, 
                 lockGuiFunc, releaseGuiFunc, messageLogFunc, updateMessageLogFunc):
        super().__init__()
        self.rules_dictionary = rules_dictionary
        self.patchers = patchers
        
        self.indices = None
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.threadpool = threadpool

        self.lockGuiFunc = lockGuiFunc
        self.releaseGuiFunc = releaseGuiFunc
        self.messageLogFunc = messageLogFunc
        self.updateMessageLogFunc = updateMessageLogFunc
        
        self.runners = []
        
    def run(self):
        self.messageLogFunc("Generating patch...")
        for patcher in self.patchers:
            cul_jobs = 0
            for index in self.indices:
                group = patcher.group
                if group in index:
                    n_jobs = sum([len(index[group]) for index in self.indices if group in index])
                    subindex = index[group]
                    n_subjobs = len(subindex)
                    runner = patch_pool_runner(self.rules_dictionary, subindex, self.working_dir, self.resources_dir,
                                               patcher, self.threadpool, cul_jobs, n_jobs,
                                               self.lockGuiFunc, self.releaseGuiFunc,
                                               self.messageLogFunc, self.updateMessageLogFunc,
                                               patcher.singular_msg, patcher.plural_msg)
                    cul_jobs += n_subjobs
                    self.runners.append(runner)
            
        self.poolchain = PoolChain(*self.runners)
        self.poolchain.finished.connect(self.finished.emit)
        self.poolchain.run()

            
                    
class patch_pool_runner(QtCore.QObject):
    updateMessageLog = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    
    def __init__(self, rules_dictionary, subindex, working_dir, resources_dir, 
                 patcher,
                 threadpool, cml_job_count, total_jobs,
                 lockGuiFunc, releaseGuiFunc,
                 messageLogFunc, updateMessageLogFunc,
                 singmessage, plurmessage):
        super().__init__()
        self.subindex = subindex
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.patcher = patcher
        self.threadpool = threadpool
        self.cml_job_count = cml_job_count
        self.total_jobs=total_jobs
        self.plurmessage = plurmessage
        self.singmessage = singmessage
        self.capsingmessage = singmessage[0].upper() + singmessage[1:]
        
        self.lockGuiFunc = lockGuiFunc
        self.releaseGuiFunc = releaseGuiFunc
        self.messageLogFunc = messageLogFunc
        self.updateMessageLogFunc = updateMessageLogFunc
        
        self.updateMessageLog.connect(self.updateMessageLogFunc)
        
        self.ncomplete = 0
        self.njobs = 0
        
        self.rules_dictionary = rules_dictionary
        
        
    @QtCore.pyqtSlot()   
    def run(self):
        try:
            self.lockGuiFunc()
            self.ncomplete = 0
            self.njobs = len(self.subindex)
            if not self.cml_job_count and self.njobs:
                self.messageLogFunc("")
            
            if not self.njobs:
                self.finished.emit()
                return
            
            for filepath, rules in self.subindex.items():
                job = self.patcher(self.rules_dictionary, self.working_dir, self.resources_dir, filepath, rules,
                self.update_messagelog, self.update_finished, self.raise_exception)
                self.threadpool.start(job)
        except Exception as e:
            self.raise_exception(e)
            
                
    def update_finished(self):
        if self.ncomplete == self.njobs:
            self.finished.emit()
                
    def update_messagelog(self, message):
        self.ncomplete += 1
        self.updateMessageLog.emit(f">>> {self.capsingmessage} {self.cml_job_count + self.ncomplete}/{self.total_jobs} [{message}]")
        
    def raise_exception(self, exception):
        try:
            raise exception
        # except ScriptHandlerError as e:
        #     self.threadpool.clear()
        #     self.threadpool.waitForDone()
        #     self.messageLogFunc(f"The following exception occured when {self.singmessage} {e.args[1]}: {e.args[0]}")
        #     raise e.args[0]
        except Exception as e:
            self.threadpool.clear()
            self.threadpool.waitForDone()
            self.messageLogFunc(f"The following exception occured when {self.plurmessage}: {e}")
            raise e
        finally:
            self.releaseGuiFunc()
########
# MBES # 
########           
                
class mbe_patcher(QtCore.QRunnable):
    def __init__(self, rules_dictionary, working_dir, resources_dir, mbe_table_filepath, mbe_rules,
                 update_messagelog, update_finished, raise_exception):
        super().__init__()
        
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.mbe_table_filepath = mbe_table_filepath
        self.mbe_rules = mbe_rules
        
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        
        self.rules_dictionary = rules_dictionary
        
    def run(self):
        try:
            mbe_table_filepath = self.mbe_table_filepath
            working_dir = self.working_dir
            resources_dir = self.resources_dir
            mbe_rules = self.mbe_rules
            
            mbe_table_filepath = os.path.relpath(mbe_table_filepath)
            local_filepath = os.path.join(*splitpath(mbe_table_filepath)[3:])
            # E.g. data/mbe_folder/table.csv
            mbe_table_datapath = os.path.join(*splitpath(mbe_table_filepath)[-3:])
            working_mbe_filepath = os.path.join(working_dir, mbe_table_datapath)
    
            if not os.path.exists(working_mbe_filepath):
                working_mbe_path = os.path.split(working_mbe_filepath)[0] + os.path.sep
                os.makedirs(working_mbe_path, exist_ok=True)
                resource_filepath = os.path.join(resources_dir, 'base_mbes', mbe_table_datapath)
                # Need to copy every table inside the MBE
                resource_path = os.path.split(resource_filepath)[0]
                for file in os.listdir(resource_path):
                    shutil.copy2(os.path.join(resource_path, file), os.path.join(working_mbe_path, file))
            
            # Join the records of the two tables
            header, mbe_data = mbetable_to_dict(working_mbe_filepath)
            _, mod_mbe_data = mbetable_to_dict(mbe_table_filepath)
            for record_id, record_rule in mbe_rules.items():
                self.rules_dictionary[record_rule](record_id, mbe_data, mod_mbe_data)
            dict_to_mbetable(working_mbe_filepath, header, mbe_data)
            
            self.update_messagelog(local_filepath)
            self.update_finished()
        except Exception as e:
            self.raise_exception(ScriptHandlerError(e, self.archive))
        
##########
# SCRIPT # 
##########   
class patch_script_src(QtCore.QRunnable):
    def __init__(self, rules_dictionary, working_dir, resources_dir, script_filepath, script_rules,
                 update_messagelog, update_finished, raise_exception):
        super().__init__()
        
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.script_filepath = script_filepath
        self.script_rules = script_rules
        
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        
        self.rules_dictionary = rules_dictionary
        
    def run(self):
        try:
            working_dir = self.working_dir
            resources_dir = self.resources_dir
            script_filepath = self.script_filepath
            script_rules = self.script_rules
            
            script_filepath = os.path.relpath(script_filepath)
            local_filepath = os.path.join(*splitpath(script_filepath)[3:])
            
            working_script_filepath = os.path.join(working_dir, local_filepath)
            
            if not os.path.exists(working_script_filepath):
                working_script_path = os.path.split(working_script_filepath)[0] + os.path.sep
                os.makedirs(working_script_path, exist_ok=True)
                resource_path = os.path.join(resources_dir, 'base_scripts', local_filepath)
                shutil.copy2(resource_path, working_script_filepath)
                    
            # I.e. execute rule
            assert len(script_rules) == 1, f"More than one rule: {script_rules}"
            rule_name = list(script_rules.values())[0]
            self.rules_dictionary[rule_name](working_script_filepath, script_filepath)
            
            self.update_messagelog(local_filepath)
            self.update_finished()
        except Exception as e:
            self.raise_exception(ScriptHandlerError(e, self.archive))


########
# ELSE # 
########      
class patch_others(QtCore.QRunnable):
    def __init__(self, rules_dictionary, working_dir, resources_dir, other_filepath, other_rules,
                 update_messagelog, update_finished, raise_exception):
        super().__init__()
        
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.other_filepath = other_filepath
        self.other_rules = other_rules
        
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        
        self.rules_dictionary = rules_dictionary
        
    def run(self):
        try:
            working_dir = self.working_dir
            resources_dir = self.resources_dir
            other_filepath = self.other_filepath
            other_rules = self.other_rules
            
            local_filepath = os.path.join(*splitpath(other_filepath)[3:])
            working_filepath = os.path.join(working_dir, local_filepath)
            working_path = os.path.join(*splitpath(working_filepath)[:-1]) + os.path.sep
            if not os.path.exists(working_path):
                os.makedirs(working_path, exist_ok=True)

            assert len(other_rules) == 1, f"More than one rule: {other_rules}"
            rule_name = list(other_rules.values())[0]
            self.rules_dictionary[rule_name](working_filepath, other_filepath)
            
            self.update_messagelog(local_filepath)
            self.update_finished()
        except Exception as e:
            self.raise_exception(ScriptHandlerError(e, self.archive))
            
id_lengths = {'mon_design_para.mbe\Monster.csv': 2}
known_duplicates = [(('107', '1'), 'mon_design_para.mbe\Monster.csv')]            

def mbetable_to_dict(filepath):
    header = None
    result = {}
    with open(filepath, 'r', encoding='utf8') as F:
        header = F.readline()
        csvreader = csv.reader(F, delimiter=',', quotechar='"')
        for line in csvreader:
            data = line
            id_length_key = '\\'.join(splitpath(filepath)[-2:])
            id_size = id_lengths.get(id_length_key, 1)
            record_id = tuple(data[:id_size])
            if record_id not in result:
                result[record_id] = data[id_size:]
            elif (record_id, id_length_key) in known_duplicates:
                pass
            else:
                assert 0, f"Duplicate ID {record_id} in {filepath}, mod manager not ready to handle this situation yet. Please raise an issue on the GitHub page."
    return header, result

def dict_to_mbetable(filepath, header, result):
    with open(filepath, 'w', newline='', encoding='utf8') as F:
        F.write(header)
        csvwriter = csv.writer(F, delimiter=',', quotechar='"')
        for key, value in result.items():
            csvwriter.writerow(([*key, *value]))
            
