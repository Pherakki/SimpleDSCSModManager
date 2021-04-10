import csv
import os
import shutil

from PyQt5 import QtCore

from .ScriptPatching import patch_scripts
from Utils.Path import splitpath

class PoolChain(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    
    def __init__(self, *pools):
        super().__init__()
        self.pools = pools
        for pool_1, pool_2 in zip(pools, pools[1:]):
        for pool_1, pool_2 in zip(self.pools, self.pools[1:]):
            pool_1.finished.connect(pool_2.run)
        pools[-1].finished.connect(self.finished.emit)
        self.pools[-1].finished.connect(self.finished.emit)
        
    def run(self):
        pools[0].run()
        self.pools[0].run()
    

class generate_patch_mt(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    
    def __init__(self, working_dir, resources_dir, threadpool, 
                 lockGuiFunc, releaseGuiFunc, messageLogFunc, updateMessageLogFunc):
        super().__init__()
        self.indices = None
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.threadpool = threadpool

        self.lockGuiFunc = lockGuiFunc
        self.releaseGuiFunc = releaseGuiFunc
        self.messageLogFunc = messageLogFunc
        self.updateMessageLogFunc = updateMessageLogFunc
        
        
        self.mbe_runners = []
        self.script_runners = []
        self.other_runners = []
        
    def run(self):
        # Replace with an iteration through plugged-in patching rules
        # Should probably collect files by rule, and then apply all the rules in one go
        # for probable optimisations
        
        self.messageLogFunc("Generating patch...")
        self.messageLogFunc("")
        cul_jobs = 0
        for index in self.indices:
            if 'mbe' in index:
                n_jobs = sum([len(index['mbe']) for index in self.indices if 'mbe' in index])
                subindex = index['mbe']
                n_subjobs = len(subindex)
                runner = patch_pool_runner(subindex, self.working_dir, self.resources_dir,
                                           mbe_patcher, self.threadpool, cul_jobs, n_jobs,
                                           self.lockGuiFunc, self.releaseGuiFunc,
                                           self.messageLogFunc, self.updateMessageLogFunc,
                                           "patching MBE", "patching MBEs")
                cul_jobs += n_subjobs
                self.mbe_runners.append(runner)
            
        cul_jobs = 0
        for index in self.indices:
            if 'script_src' in index:
                n_jobs = sum([len(index['script_src']) for index in self.indices if 'script_src' in index])
                subindex = index['script_src']
                n_subjobs = len(subindex)
                runner = patch_pool_runner(subindex, self.working_dir, self.resources_dir,
                                           patch_script_src, self.threadpool, cul_jobs, n_jobs,
                                           self.lockGuiFunc, self.releaseGuiFunc,
                                           self.messageLogFunc, self.updateMessageLogFunc,
                                           "patching script", "patching scripts")
                cul_jobs += n_subjobs
                self.script_runners.append(runner)
            
        cul_jobs = 0
        for index in self.indices:
            if 'other' in index:
                n_jobs = sum([len(index['other']) for index in self.indices if 'other' in index])
                subindex = index['other']
                n_subjobs = len(subindex)
                runner = patch_pool_runner(subindex, self.working_dir, self.resources_dir,
                                           patch_others, self.threadpool, cul_jobs, n_jobs,
                                           self.lockGuiFunc, self.releaseGuiFunc,
                                           self.messageLogFunc, self.updateMessageLogFunc,
                                           "copying file", "copying files")
                cul_jobs += n_subjobs
                self.other_runners.append(runner)
            
        for pool_1, pool_2 in zip(self.mbe_runners, self.mbe_runners[1:]):
            pool_1.finished.connect(pool_2.run)
        for pool_1, pool_2 in zip(self.script_runners, self.script_runners[1:]):
            pool_1.finished.connect(pool_2.run)
        for pool_1, pool_2 in zip(self.other_runners, self.other_runners[1:]):
            pool_1.finished.connect(pool_2.run)
            
        if len(self.mbe_runners):
            if len(self.script_runners):
                self.mbe_runners[-1].finished.connect(self.script_runners[0].run)
            elif len(self.other_runners):
                self.mbe_runners[-1].finished.connect(self.other_runners[0].run)
            else:
                self.mbe_runners[-1].finished.connect(self.finished.emit)
        if len(self.script_runners):
            if len(self.other_runners):    
                self.script_runners[-1].finished.connect(self.other_runners[0].run)
            else:
                self.script_runners[-1].finished.connect(self.finished.emit)
        if len(self.other_runners):
            self.other_runners[-1].finished.connect(self.finished.emit)
        
        if len(self.mbe_runners):
            self.mbe_runners[0].run()
        elif len(self.script_runners):
            self.script_runners[0].run()
        elif len(self.other_runners):
            self.other_runners[0].run()
            
                    
class patch_pool_runner(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    
    def __init__(self, subindex, working_dir, resources_dir, 
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
        
        self.ncomplete = 0
        self.njobs = 0
        
        
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
                job = self.patcher(self.working_dir, self.resources_dir, filepath, rules,
                self.update_messagelog, self.update_finished, self.raise_exception)
                self.threadpool.start(job)
        except Exception as e:
            self.raise_exception(e)
            
                
    def update_finished(self):
        if self.ncomplete == self.njobs:
            self.finished.emit()
                
    def update_messagelog(self, message):
        self.ncomplete += 1
        self.updateMessageLogFunc(f">>> {self.capsingmessage} {self.cml_job_count + self.ncomplete}/{self.total_jobs} [{message}]")
        
    def raise_exception(self, exception):
        try:
            raise exception
        except ScriptHandlerError as e:
            self.threadpool.clear()
            self.threadpool.waitForDone()
            self.messageLogFunc(f"The following exception occured when {self.singmessage} {e.args[1]}: {e.args[0]}")
            raise e.args[0]
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
    def __init__(self, working_dir, resources_dir, mbe_table_filepath, mbe_rules,
                 update_messagelog, update_finished, raise_exception):
        super().__init__()
        
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.mbe_table_filepath = mbe_table_filepath
        self.mbe_rules = mbe_rules
        
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        
    def run(self):
        try:
            mbe_table_filepath = os.path.relpath(mbe_table_filepath)
            # E.g. data/mbe_folder/table.csv
            mbe_table_datapath = os.path.join(*splitpath(mbe_table_filepath)[-3:])
            working_mbe_filepath = os.path.join(working_dir, mbe_table_datapath)
    
            if not os.path.exists(working_mbe_filepath):
                working_mbe_path = os.path.split(working_mbe_filepath)[0] + os.path.sep
                os.makedirs(working_mbe_path, exist_ok=True)
                resource_filepath = os.path.join(resources_dir, 'base_mbes', mbe_table_datapath)
                resource_path = os.path.split(resource_filepath)[0]
                for file in os.listdir(resource_path):
                    shutil.copy2(os.path.join(resource_path, file), os.path.join(working_mbe_path, file))
            
            # Join the records of the two tables
            header, mbe_data = mbetable_to_dict(working_mbe_filepath)
            _, mod_mbe_data = mbetable_to_dict(mbe_table_filepath)
            for record_id, record_rule in mbe_rules.items():
                # record_rule(record_id, mbe_data)
                mbe_data[record_id] = mod_mbe_data[record_id]
            dict_to_mbetable(working_mbe_filepath, header, mbe_data)
            self.update_messagelog(self.filepath)
                    
            self.update_finished()
        except Exception as e:
            self.exception.emit(ScriptHandlerError(e, self.archive))
        
##########
# SCRIPT # 
##########   
class patch_script_src(QtCore.QRunnable):
    def __init__(self, working_dir, resources_dir, script_filepath, script_rules,
                 update_messagelog, update_finished, raise_exception):
        super().__init__()
        
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.script_filepath = script_filepath
        self.script_rules = script_rules
        
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        
    def run(self):
        try:
            working_dir = self.working_dir
            resources_dir = self.resources_dir
            script_filepath = self.script_filepath
            script_rules = self.script_rules
            
            script_filepath = os.path.relpath(script_filepath)
            local_filepath = os.path.join(*splitpath(script_filepath)[3:])
            
            working_script_filepath = os.path.join(working_dir, local_filepath)
            wsd, wdf = os.path.split(working_script_filepath)
            patch_filepath = os.path.join(wsd, '_' + wdf)
            
            if not os.path.exists(working_script_filepath):
                working_script_path = os.path.split(working_script_filepath)[0] + os.path.sep
                os.makedirs(working_script_path, exist_ok=True)
                resource_path = os.path.join(resources_dir, 'base_scripts', 'script64')
                for file in os.listdir(resource_path):
                    shutil.copy2(os.path.join(resource_path, file), os.path.join(working_script_path, file))
                    
                    
            patch_scripts(working_script_filepath, script_filepath, patch_filepath)
            os.remove(working_script_filepath)
            os.rename(patch_filepath, working_script_filepath)
            self.update_messagelog(file)
            self.update_finished()
        except Exception as e:
            self.exception.emit(ScriptHandlerError(e, self.archive))


########
# ELSE # 
########      
class patch_others(QtCore.QRunnable):
    def __init__(self, working_dir, resources_dir, other_filepath, other_rules,
                 update_messagelog, update_finished, raise_exception):
        super().__init__()
        
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.other_filepath = other_filepath
        self.other_rules = other_rules
        
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        
    def run(self):
        try:
            working_dir = self.working_dir
            resources_dir = self.resources_dir
            other_filepath = self.script_filepath
            other_rules = self.other_rules
            
            local_filepath = os.path.join(*splitpath(other_filepath)[3:])
            working_filepath = os.path.join(working_dir, local_filepath)
            working_path = os.path.join(*splitpath(working_filepath)[:-1]) + os.path.sep
            if not os.path.exists(working_path):
                os.makedirs(working_path, exist_ok=True)
            # Only if 'overwrite' rule...
            shutil.copy2(other_filepath, working_filepath)
            self.update_messagelog(os.path.split(working_filepath)[-1])
            self.update_finished()
        except Exception as e:
            self.exception.emit(ScriptHandlerError(e, self.archive))
            
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
