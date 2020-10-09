# SimpleDSCSModManager
A very simple mod manager for Digimon Story: Cyber Sleuth.

This is a very quick-and-dirty GUI application that acts as a driver for [DSCSTools](https://github.com/SydMontague/DSCSTools) so that those who aren't comfortable with using the command line can easily install mods. Expect bugs. It uses the routines of DSCSTools to extract and re-build a (potentially) modded version of the DSDBA.steam.mvgl archive, which is an overwrite archive used by the game.

## Installation
1. Download the latest release of [DSCSTools](https://github.com/SydMontague/DSCSTools) and extract it somewhere on your computer.
2. Download the latest release of SimpleDSCSModManager. Extract it somewhere on your computer.

## Mod File Format
Mods should take the form of zip archives (zip extension) with the same file structure as the extracted DSDB(A) archives. In practice, this means that name, skel, geom, and anim files are on the top level, editted images should go in a folder called 'images', etc. An example mod might look like:

```
|-- my_amazing_mod.zip
    |-- pc001.name
    |-- pc001.geom
    |-- pc001.skel
    |-- images\
        |-- pc001ab01.img
```

**Even if you do not edit all three name, skel, and geom files for a particular mod, please put all three into the mod archive.** The game will hang (presumably searching for the missing files) if you do not include all three.

**Place these zip archives into the `mods\` directory in order to let SimpleDSCSModManager know about them.**

## Usage
1. SimpleDSCSModManager cannot do anything unless you tell it where Digimon Story: Cyber Sleuth and DSCSTools are installed. Set the two file paths at the top of the window in order to unlock the rest of the GUI.
    * DSCSTools: Select the folder containing DSCSTools.exe.
    * DSCS: Select the folder named "Digimon Story Cyber Sleuth Complete Edition" in your Steam games install directory. It should contain the two folders "app_digister" and "resources", with the DSCS executable inside "app_digister".
2. SimpleDSCSModManager generates four folders when it runs for the first time:
    * config: This is where the DSCSTools and DSCS locations are remembered in a plaintext file, along with the mod load order and a debug log.
    * mods: A blank folder to put your mods into.
    * output: A folder that will contain a copy of your modded DSDBA.steam.mvgl file, incase you want/need to manually install it.
    * resources: DO NOT EDIT THE CONTENTS OF THIS FOLDER. It will contain a backup of the original DSDBA archive that is used as a template to build mods out of; as well as a copy of the much larger DSDB archive, incase you wish to use the game files to create mods. You can copy data *out* of this folder, but do not *change* what exists in it, because its contents are used to build the modded DSDBA archive.
3. SimpleDSCSManager provides four core functions (well, DSCSTools provides most of them, but now you can click shiny buttons!)
    * 'Install Mods': This button will copy the DSDBA archive from your game if it has not done so already, place any mods in your `mods\` folder into the archive, re-pack it, and install it for you. If it has not done so already, it will also create a backup of the original DSDBA archive in your game files in `resources\backups`.
    * 'Refresh Modlist': Makes the GUI check for updates in the mods folder, and displays them. This is done automatically if you click 'Install Mods', and is only useful to check if SimpleDSCSModManager has recognised your mods.
    * 'Restore Backup': Overwrites the modded DSDBA archive with that stored in `Digimon Story Cyber Sleuth Complete Edition\resources\backups`, which should be the original DSDBA archive.
    * 'Extract DSDB': Extracts the main game data to SimpleDSCSModManager's `resources\` directory. Only useful if you plan to make mods. This will require ~15 GiB of hard disk space available, with 12.7 GiB remaining after the operation is complete.
4. You can change your *load order* by dragging-and-dropping the names of mods in the central list. Mods at the top have the lowest priority, and those at the bottom have the highest, meaning that if two mods change the same file then the lowest mod will take precedence.

## Contact
e-mail: pherakki@gmail.com

## Acknowledgements
[SydMontague](https://github.com/SydMontague) for creating [DSCSTools](https://github.com/SydMontague/DSCSTools), which does all the hard work - this program is just a crappy shell around it..!
