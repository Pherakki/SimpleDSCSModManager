import os
import subprocess


class VGAudioHandler:
    def __init__(self, script_loc):
        self.exe_path = os.path.join(script_loc, "sdmmlib/vgaudio/VGAudioCLI.exe")
    
    def HCA_to_WAV(self, input_path, output_path):
        subprocess.run([self.exe_path, 
                        "-i", input_path, 
                        "-o", output_path,
                        "--out-format", "wav",
                        "--keycode", "2897314143465725881"])
        
    def HCAs_to_WAVs(self, input_path, output_path):
        print(" ".join([self.exe_path,
                        "-b",
                        "-i", input_path, 
                        "-o", output_path,
                        "--out-format", "wav",
                        "--keycode", "2897314143465725881"]))
        subprocess.run([self.exe_path,
                        "-b",
                        "-i", input_path, 
                        "-o", output_path,
                        "--out-format", "wav",
                        "--keycode", "2897314143465725881"])
    
    def WAV_to_HCA(self, input_path, output_path):
        subprocess.run([self.exe_path, 
                        "-i", input_path, 
                        "-o", output_path,
                        "--out-format", "hca",
                        "--keycode", "2897314143465725881"])
        
    def WAVs_to_HCAs(self, input_path, output_path):
        subprocess.run([self.exe_path, 
                        "-b",
                        "-i", input_path, 
                        "-o", output_path,
                        "--out-format", "hca",
                        "--keycode", "2897314143465725881"])
    
    def WAV_to_HCA_looped(self, input_path, output_path, start_sample, end_sample):
        subprocess.run([self.exe_path, 
                        "-i", input_path, 
                        "-o", output_path,
                        "-l", f"{start_sample}-{end_sample}",
                        "--out-format", "hca",
                        "--keycode", "2897314143465725881"])
