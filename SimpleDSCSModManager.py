import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import zipfile
import os
import shutil
import subprocess
import platform


default_steam_installs = {'Windows': 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Digimon Story Cyber Sleuth Complete Edition\\resources'}

main = tk.Tk()
main.title('SimpleDSCSModManager')
main.dscstools_dir = 'DSCSTools'
main.dscs_dir = ''
main.load_order = []

plain_archive_name = 'DSDBP'
archive_name = plain_archive_name + '.steam.mvgl'
archive_name_decrypted = 'DSDBP_decrypted'
archive_name_extracted = 'DSDBP'
main_archive_name = 'DSDB.steam.mvgl'
main_archive_name_decrypted = 'DSDB_decrypted'
main_archive_name_extracted = 'DSDB'
script_loc = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))
resource_loc = os.path.join(script_loc, 'resources')
mods_loc = os.path.join(script_loc, 'mods')
working_loc = os.path.join(script_loc, 'output')
config_loc = os.path.join(script_loc, 'config')
config_file_loc = os.path.join(config_loc, 'config.txt')
debug_file_loc = os.path.join(config_loc, 'debug_log.txt')
lo_file_loc = os.path.join(config_loc, 'load_order.txt')

os.makedirs(resource_loc, exist_ok=True)
os.makedirs(mods_loc, exist_ok=True)
os.makedirs(working_loc, exist_ok=True)
os.makedirs(config_loc, exist_ok=True)

local_archive = os.path.join(resource_loc, archive_name)
local_archive_decrypted = os.path.join(resource_loc, archive_name_decrypted)
local_archive_unpacked = os.path.join(resource_loc, archive_name_extracted)
output_archive = os.path.join(working_loc, archive_name)
output_archive_decrypted = os.path.join(working_loc, archive_name_decrypted)
output_archive_unpacked = os.path.join(working_loc, archive_name_extracted)
local_main_archive = os.path.join(resource_loc, main_archive_name)
local_main_archive_decrypted = os.path.join(resource_loc, main_archive_name_decrypted)
local_main_archive_unpacked = os.path.join(resource_loc, main_archive_name_extracted)

def check_config_file():
    if os.path.exists(config_file_loc):
        with open(config_file_loc, 'r') as F:
            data = F.read().splitlines()
            try:
                main.dscstools_dir = data[0]
                main.dscs_dir = data[1]
            except IndexError:
                with open(debug_file_loc, 'a') as dblog:
                    dblog.write(">> Exception when checking config file: IndexError")
                main.dscstools_dir = ''
                main.dscs_dir = ''
            change_textbox_text(dscstools_location_textbox, main.dscstools_dir)
            change_textbox_text(dscs_location_textbox, main.dscs_dir)
            update_paths()
    else:
        with open(config_file_loc, 'w') as F:
            pass
    if main.dscs_dir == '':
        main.dscs_dir = default_steam_installs.get(platform.system(), '')
    if main.dscstools_dir == '':
        main.dscs_dir = 'DSCSTools'
        
def write_config():
    with open(config_file_loc, 'w') as F:
        write_vars = [main.dscstools_dir, main.dscs_dir]
        F.writelines('\n'.join(write_vars))
        
        
def write_loadorder():
    with open(lo_file_loc, 'w') as F:
        F.writelines('\n'.join(main.load_order))
        
        
def read_loadorder():
    if os.path.exists(lo_file_loc):
        with open(lo_file_loc, 'r') as F:
            main.load_order = F.read().splitlines()
        
        
def find_mods():
    mod_filepaths = []
    for file in os.listdir(mods_loc):
        filename, ext = os.path.splitext(file)
        if ext == '.zip':
            mod_filepaths.append(filename)
    return mod_filepaths
        

def loc_in_loadorder(filename):
    return main.load_order.index(filename) if filename in main.load_order else len(main.load_order)


def populate_modlist_box():
    read_loadorder()
    mod_names = find_mods()
    mod_names = sorted(mod_names, key=lambda x: loc_in_loadorder(x))
    main.load_order = mod_names
    mods_list.delete(0,tk.END)
    mods_list.insert(tk.END, *main.load_order)
    write_loadorder()
    
            
def init_resources(num_steps):
    update_progbar("Copying DSDBP...", 0, num_steps)
    shutil.copy2(main.overwrite_archive, local_archive)
    update_progbar("Decrypting DSDBP...", 1, num_steps)
    subprocess.call([main.dscstools_dir, '--crypt', local_archive, archive_name_decrypted], creationflags=subprocess.CREATE_NO_WINDOW) # cwd = resource_loc?
    os.remove(local_archive)
    shutil.move(archive_name_decrypted, local_archive_decrypted)
    update_progbar("Extracting DSDBP...", 2, num_steps)
    subprocess.call([main.dscstools_dir, '--extract', local_archive_decrypted, archive_name_extracted], creationflags=subprocess.CREATE_NO_WINDOW)
    os.remove(local_archive_decrypted)
    shutil.move(archive_name_extracted, local_archive_unpacked)
    
    
def init_main_resources():
    yesno = tk.messagebox.askquestion("Extract DSDB", "The DSDB archive is ~2.6 GiB in size, and the extracted contents are around ~ 12.7 GiB. It will take a significant amount of time to unpack. It is only worth doing this if you intend to use the contents to make mods; it is not necessary to extract this in order to use or install mods. The extracted files will be located in the resources folder. Do you wish to proceed?", icon='warning')
    if yesno == 'yes':
        update_progbar("Decrypting DSDB [this will probably take more than 5 minutes in total, don't panic]...", 0, 2)
        subprocess.call([main.dscstools_dir, '--crypt', os.path.join(main.dscs_dir, main_archive_name), main_archive_name_decrypted], creationflags=subprocess.CREATE_NO_WINDOW) # cwd = resource_loc?
        update_progbar("Extracting DSDB [this will probably take more than 5 minutes in total, don't panic]...", 1, 2)
        subprocess.call([main.dscstools_dir, '--extract', main_archive_name_decrypted, main_archive_name_extracted], creationflags=subprocess.CREATE_NO_WINDOW)
        os.remove(main_archive_name_decrypted)
        update_progbar("Copying DSDB [this will probably take more than 5 minutes in total, don't panic]...", 1, 2)
        shutil.move(main_archive_name_extracted, local_main_archive_unpacked)
        update_progbar("DSDB copied successfully", 2, 2)


def pack_mods(num_steps):    
    shutil.copytree(local_archive_unpacked, output_archive_unpacked)
    populate_modlist_box()
    update_progbar("Copying mod files...", 3, num_steps)
    for mod_file in main.load_order:
        mod_path = os.path.join(mods_loc, mod_file) + '.zip'
        with zipfile.ZipFile(mod_path, 'r') as zipreader:
            zipreader.extractall(output_archive_unpacked)
                
    update_progbar("Packing modpack [this could take a few minutes, don't panic]...", 4, num_steps)
    subprocess.call([main.dscstools_dir, '--pack', output_archive_unpacked, archive_name_decrypted], creationflags=subprocess.CREATE_NO_WINDOW)
    
    shutil.rmtree(output_archive_unpacked)
    shutil.move(archive_name_decrypted, output_archive_decrypted)

    update_progbar("Encrypting modpack...", 5, num_steps)
    subprocess.call([main.dscstools_dir, '--crypt', output_archive_decrypted, plain_archive_name], creationflags=subprocess.CREATE_NO_WINDOW) # cwd = resource_loc?
    os.remove(output_archive_decrypted)
    shutil.move(plain_archive_name, output_archive)



def install_mods(num_steps):
    update_progbar("Installing modpack...", 6, num_steps)
    if not os.path.exists(main.backup_archive):
        os.makedirs(main.backup_dir, exist_ok=True)
        shutil.copy2(main.overwrite_archive, main.backup_archive)
    shutil.copy2(output_archive, main.overwrite_archive )
    update_progbar("Mods installed", 7, num_steps)


def all_in_one():
    num_steps = 4
    if not os.path.exists(local_archive_unpacked):
        num_steps += 3
        init_resources(num_steps)
    pack_mods(num_steps)
    install_mods(num_steps)
    

def restore_backup():
    update_progbar("Restoring backup...", 0, 1)
    shutil.copy2(main.backup_archive, main.overwrite_archive )
    update_progbar("Backup restored", 1, 1)
    
    
# Mod interaction buttons
button_frame = tk.Frame(main)
full_install_button = tk.Button(button_frame, width=12, text="Install Mods", command=all_in_one)
full_install_button.grid(row=0, column=0, padx=5, pady=10)
modlist_refresh_button = tk.Button(button_frame, width=12, text="Refresh Modlist", command=populate_modlist_box)
modlist_refresh_button.grid(row=0, column=1, padx=5, pady=10)
backup_restore_button = tk.Button(button_frame, width=12, text="Restore Backup", command=restore_backup)
backup_restore_button.grid(row=0, column=2, padx=5, pady=10)
button_frame.grid(row=4, column=0, columnspan=3)

dsdb_button = tk.Button(button_frame, width=30, text="Extract DSDB [For Mod Creators]", command=init_main_resources)
dsdb_button.grid(row=1, column=0, pady=10, columnspan=3)


# Progress bar
progress_bar_label = tk.Label(main, text='')
progress_bar_label.grid(row=5, column=0, columnspan=3, sticky='ew')

progress_bar = ttk.Progressbar(main, orient='horizontal', mode='determinate', value=0)
progress_bar.grid(row=6, column=0, columnspan=3, sticky='ew')


def update_progbar(msg, stage, num_steps):
    offset = 3 if num_steps == 4 else 0
    progress_bar_label.config(text=msg)
    progress_bar.config(value=(100*(stage-offset))//num_steps)
    progress_bar.update_idletasks()


def toggle_buttons():
    state = main.dscs_dir == '' or main.dscstools_dir == ''
    state = 'disabled' if state else 'normal'
    full_install_button.config(state=state)
    modlist_refresh_button.config(state=state)
    backup_restore_button.config(state=state)
    dsdb_button.config(state=state)

def update_paths():
    main.overwrite_archive = os.path.join(main.dscs_dir, archive_name)
    main.backup_dir = os.path.join(main.dscs_dir, 'backup')
    main.backup_archive = os.path.join(main.backup_dir, archive_name)
    toggle_buttons()


def change_textbox_text(textbox, input_string):
    textbox.config(state='normal')
    textbox.delete('1.0', tk.END)
    textbox.insert(tk.END, input_string)
    textbox.config(state='disabled')
    

def open_dscstools():
    retry = True
    exit_loop = retry
    while exit_loop:
        dscstools_dir = os.path.normpath(filedialog.askdirectory())
        if not os.path.exists(os.path.join(dscstools_dir, "DSCSTools.exe")):
            retry = messagebox.askretrycancel("DSCSTools.exe not found", message="DSCSTools.exe does not appear to be in the selected folder.")
            exit_loop = retry
        else:
            exit_loop = False
            main.dscstools_dir = os.path.join(dscstools_dir, "DSCSTools")
            change_textbox_text(dscstools_location_textbox, main.dscstools_dir)
            write_config()
            update_paths()
        if not retry:
            main.dscstools_dir = 'DSCSTools'
            
            
def open_dscs():
    retry = True
    exit_loop = retry
    while exit_loop:
        dscs_dir = os.path.normpath(filedialog.askdirectory())
        if not os.path.exists(os.path.join(dscs_dir, "app_digister", "Digimon Story CS.exe")):
            retry = messagebox.askretrycancel("Digimon Story CS.exe not found", message="This does not appear to be the Digimon Story: Cyber Sleuth folder. It should contain the folders 'app_digister' and 'resources'.")
            exit_loop = retry
        else:
            exit_loop = False
            main.dscs_dir = os.path.join(dscs_dir, 'resources')
            change_textbox_text(dscs_location_textbox, main.dscs_dir)
            write_config()
            update_paths()
        if not retry:
            main.dscs_dir = ''

    
# Cheerfully nicked from: https://stackoverflow.com/questions/14459993/tkinter-listbox-drag-and-drop-with-python
# Editted only to interact with the load order
class DragDropListbox(tk.Listbox):
    """ A Tkinter listbox with drag'n'drop reordering of entries. """
    def __init__(self, master, **kw):
        kw['selectmode'] = tk.SINGLE
        tk.Listbox.__init__(self, master, kw)
        self.bind('<Button-1>', self.setCurrent)
        self.bind('<B1-Motion>', self.shiftSelection)
        self.bind('<ButtonRelease-1>', self.edit_loadorder)
        self.curIndex = None
    
    def setCurrent(self, event):
        self.curIndex = self.nearest(event.y)
    
    def shiftSelection(self, event):
        i = self.nearest(event.y)
        if i < self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i+1, x)
            self.curIndex = i
        elif i > self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i-1, x)
            self.curIndex = i
            
    def edit_loadorder(self, event):
        main.load_order = self.get(0, tk.END)
        write_loadorder()

# DSCSTools location widget
dscstools_location_label=tk.Label(main, height=1, width=20, text='DSCSTools location: ')
dscstools_location_label.grid(row=0, column=0)
dscstools_location_textbox=tk.Text(main, height=1, width=50, state='disabled', wrap='none')
dscstools_location_textbox.grid(row=0, column=1)
dscstools_location_button = tk.Button(main, text="...", command=open_dscstools, height=1)
dscstools_location_button.grid(row=0, column=2)


# DSCSTools location widget
dscs_location_label=tk.Label(main, height=1, width=20, text='Game directory: ')
dscs_location_label.grid(row=1, column=0)
dscs_location_textbox=tk.Text(main, height=1, width=50, state='disabled', wrap='none')
dscs_location_textbox.grid(row=1, column=1)
dscs_location_button = tk.Button(main, text="...", command=open_dscs, height=1)
dscs_location_button.grid(row=1, column=2)

# Mods listbox
# Scrollbar code nicked from https://stackoverflow.com/questions/24656138/python-tkinter-attach-scrollbar-to-listbox-as-opposed-to-window
mods_label = tk.Label(main, height=1, width=20, text='Detected mods')
mods_label.grid(row=2, column=0, columnspan=3)
listbox_frame = tk.Frame(main)
listbox_frame.grid(row=3, column=0, columnspan=3)
mods_list = DragDropListbox(listbox_frame, height=20, width=50)
mods_list.pack(side="left", fill="y")
scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
scrollbar.config(command=mods_list.yview)
scrollbar.pack(side="right", fill="y")
        

check_config_file()
populate_modlist_box()
update_paths()

main.resizable(0, 0)
if not os.path.exists(os.path.join(*os.path.split(main.dscs_dir)[:-1], "app_digister", "Digimon Story CS.exe")):
    okcancel = messagebox.askokcancel("Digimon Story CS.exe not found", message="Digimon Story: Cyber Sleuth was not auto-detected on your computer. Please select the game location (containing the folders 'app_digister' and 'resources').")
    if okcancel:
        open_dscs()
    else:
        main.dscs_dir = ''
        change_textbox_text(dscs_location_textbox, main.dscs_dir)
        write_config()
        update_paths()
        
print(main.dscstools_dir + ".exe")
if not os.path.exists(main.dscstools_dir + ".exe"):
    okcancel = messagebox.askokcancel("DSCSTools.exe not found", message="DSCSTools was not found. Please select the folder containing the DSCSTools execuable.")
    if okcancel:
        open_dscstools()
    else:
        main.dscstools_dir = ''
        change_textbox_text(dscstools_location_textbox, 'DSCSTools')
        write_config()
        update_paths()
main.mainloop()
