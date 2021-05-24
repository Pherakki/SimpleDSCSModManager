# SimpleDSCSModManager
A basic mod manager for Digimon Story: Cyber Sleuth.
Currently in an early release state, which means that not all desired features are complete and bugs are not completely unexpected. Although the source code should in principle be cross-platform, only Windows releases are currently supported. Other operating systems are untested and, therefore, may suffer from more bugs.

## Features
- Automatic patching of database and script edits
- Profile system for switching between sets of mods
- GUI for several tools that extract and re-pack most game files
- Caching of pre-built mod files to improve install times

## Future Plans and Ideas
- A "request" file that installs vanilla dependencies
- Improvements to database patching
- Softcoding database IDs to increase inter-mod compatibility
- Audio conversion support
- More powerful script editing
- Colour schemes (dark mode)
- List of installed plugins
- Graphing/reporting of mod conflicts

## Installation
1. Download the latest release of SimpleDSCSModManager. Extract it somewhere on your computer.

## Usage
A guide to usage can be found in the accompanying documentation in the file `user_guide.pdf`.

## Mod File Format
There are several options for creating a mod compatible with the mod manager, which are detailed in the accompanying user guide and CYMIS specification documents. The most basic format will consist of a zip file contain the folder "modfiles" and a JSON file called "METADATA.json", where "modfiles" contains the files to be installed and "METADATA.json" contains a JSON dictionary with entries for a "Name", "Version", "Author", "Category", and "Description".
```
|-- my_amazing_mod.zip
    |-- modfiles
    |   |-- pc001.name
    |   |-- pc001.geom
    |   |-- pc001.skel
    |   |-- images\
    |       |-- pc001ab01.img
    |   |-- shaders\
    |       |-- ... .shad
    |-- METADATA.json
```
These mod files can be installed by dragging-and-dropping them into the left pane of the GUI.

## Building from source
### Building dependencies
1. Download the latest release of [DSCSTools](https://github.com/SydMontague/DSCSTools) and move the `.pyd` file to `tools/dscstools/`. Move the `structures` folder to the same directory as the mod manager executable.
2. Build this [64-bit fork of NutCracker](https://github.com/SydMontague/NutCracker) and move the executable to `tools/nutcracker/`.
3. Build the 64-bit version of the [Squirrel 2.2.4 compiler](https://sourceforge.net/projects/squirrel/files/squirrel2/squirrel%202.2.4%20stable/) and move the executable to `tools/squirrel/`.
### Building PyInstaller
It is recommended to freeze the Python source into an executable with PyInstaller. However, the official distribution often triggers anti-virus protection software. Building PyInstaller yourself tends to alleviate this issue.
1. Clone the PyInstaller source with `git clone https://github.com/pyinstaller/pyinstaller`
2. In the `pyinstaller/bootloader` directory of the repository, run `python3 ./waf distclean all`. This will build PyInstaller.
3. In the `pyinstaller` directory of the repository, run `python3 setup.py install`. This will install PyInstaller to your system.
### Building the executable
1. Run `pyinstaller SimpleDSCSModManager.py`.
2. Note: **DO NOT** use the `--one-file` flag. This will completely break the mod manager, because it will be unable to find the files and programs it depends on.

## Contact
e-mail: pherakki@gmail.com

## Acknowledgements
1. [SydMontague](https://github.com/SydMontague) for creating [DSCSTools](https://github.com/SydMontague/DSCSTools), producing the Python API for it, and for having an endless patience..!
2. Releases are compiled with [Pyinstaller](https://www.pyinstaller.org/).
