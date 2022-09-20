import os
import shutil


class BackupsManager:
    
    @property
    def default_MDB1s(self):
        return {"DSDB", "DSDBA", "DSDBS", "DSDBSP", "DSDBP", "DSDBse", "DSDBPse"}
    
    @property
    def default_AFS2s(self):
        return {"DSDBbgm", "DSDBPDSEbgm", "DSDBvo", "DSDBPvo", "DSDBPvous"}
    
    @property
    def default_misc_files(self):
        return {
                  "d1001_bg.usm",
                  "d12801_bg01.usm",
                  "d12801_bg02.usm",
                  "d12801_bg03.usm",
                  "d12801_bg04.usm",
                  "d12801_bg05.usm",
                  "d12801_bg06.usm",
                  "d12801_bg07.usm",
                  "d12801_bg08.usm",
                  "d12801_bg09.usm",
                  "d12801_bg10.usm",
                  "d12801_bg11.usm",
                  "d12801_bg12.usm",
                  "d12902_bg.usm",
                  "d2401_bg.usm",
                  "S01_A.usm",
                  "S01_B.usm",
                  "S02_A.usm",
                  "S02_B.usm",
                  "S03.usm",
                  "S04.usm",
                  "S05.usm",
                  "S06.usm",
                  "S07.usm",
                  "S08_A.usm",
                  "S08_B.usm",
                  "S11.usm",
                  "S12.usm",
                  "S14.usm",
                  "S21_as.usm",
                  "S21_de.usm",
                  "S21_en.usm",
                  "S21_kr.usm",
                  "S23_as.usm",
                  "S23_de.usm",
                  "S23_en.usm",
                  "S23_kr.usm",
                  "S24.usm",
                  "S51_as.usm",
                  "S51_de.usm",
                  "S51_en.usm",
                  "S51_kr.usm",
                  "S52.usm",
                  "S53.usm",
                  "S54.usm",
                  "S55.usm",
                  "S56.usm",
                  "S57.usm",
                  "S58.usm",
                  "S59.usm",
                  "S60.usm",
                  "S61_as.usm",
                  "S61_de.usm",
                  "S61_en.usm",
                  "S61_kr.usm",
                  "S62.usm",
                  "S63.usm",
                  "S64.usm",
                  "S65.usm",
                  "S66_as.usm",
                  "S66_de.usm",
                  "S66_en.usm",
                  "S66_kr.usm",
                  "t2405_bg.usm",
                  "media/M100.mvgl",
                  "media/M101.mvgl",
                  "media/M102.mvgl",
                  "media/M103.mvgl",
                  "media/M104.mvgl",
                  "text/authorization/as/data_analytics.txt",
                  "text/authorization/as/privacy_policy.txt",
                  "text/authorization/de/data_analytics.txt",
                  "text/authorization/de/privacy_policy.txt",
                  "text/authorization/kr/data_analytics.txt",
                  "text/authorization/kr/privacy_policy.txt",
                  "text/authorization/us/data_analytics.txt",
                  "text/authorization/us/privacy_policy.txt"
                }
    
    @staticmethod
    def replace_backed_up_file(src, dst, dst_folder, backup_folder):
        if os.path.exists(dst):
            rel_filepath = os.path.relpath(dst, dst_folder)
            backup_dst = os.path.normpath(os.path.join(backup_folder, rel_filepath))
            if not os.path.exists(backup_dst):
                os.makedirs(os.path.split(backup_dst)[0], exist_ok=True)
                shutil.copy2(dst, backup_dst)
        shutil.copy2(src, dst)
        
    @staticmethod
    def try_back_up_file(dst, dst_folder, backup_folder):
        rel_filepath = os.path.relpath(dst, dst_folder)
        backup_dst = os.path.normpath(os.path.join(backup_folder, rel_filepath))
        if not os.path.exists(backup_dst):
            os.makedirs(os.path.split(backup_dst)[0], exist_ok=True)
            shutil.copy2(dst, backup_dst)
    
        
    @staticmethod
    def restore_backed_up_file(dst, dst_folder, backup_folder):
        rel_filepath = os.path.relpath(dst, dst_folder)
        backup_dst = os.path.normpath(os.path.join(backup_folder, rel_filepath))
        if os.path.exists(backup_dst):
            shutil.copy2(backup_dst, dst)
            
    @staticmethod
    def get_backed_up_filepath_if_exists(dst, dst_folder, backup_folder):
        rel_filepath = os.path.relpath(dst, dst_folder)
        backup_dst = os.path.normpath(os.path.join(backup_folder, rel_filepath))
        if os.path.exists(backup_dst):
            return backup_dst
        else:
            return dst
