# SimpleDSCSModManager
**If you have difficulties installing mods or if using mods causes the game to crash or behave unexpectedly, run the mod manager as an administrator or install the game in a location outside of Program Files on Windows.** 

**Executables can be found in the "Releases" tab on the right-hand side of this page.**

A poorly-named mod manager for the PC release of Digimon Story: Cyber Sleuth Complete Edition. Windows binaries are provided, and you will have to build the mod manager yourself if you are running a different operating system. Instructions on how to do this are provided in [Building Dependencies](#building_dependencies). Note that, since the mod manager uses [VGAudio](https://github.com/Thealexbarney/VGAudio) for its WAV->HCA conversion utility for mod authors, this feature is unavailable on non-Windows platforms.

## Features
- Automatic patching of database and script edits
- Profile system for switching between sets of mods
- GUI for several tools that extract and re-pack most game files
- Caching of pre-built mod files to improve install times
- A "request" file that installs vanilla dependencies
- Softcoding database IDs to increase inter-mod compatibility
- Language options for the GUI

## Future Plans and Ideas
- Improvements to database patching
- More powerful script editing
- Colour schemes (dark mode)
- List of installed plugins
- Graphing/reporting of mod conflicts

## Installation
You can run the mod manager in one of two ways:
1. The foolproof way of running SimpleDSCSModManager is to install Python 3.8.10 on your system and run the source code directly.
   1. Install [Python 3.8.10](https://www.python.org/downloads/release/python-3810/). Windows users should select the appropriate installer (one of the final two links in the table  at the bottom of the page).
   2. Open a Command Prompt and type `pip install PyQt5` to install the dependency of PyQt5. (If you ever want to remove this package from your system, use `pip uninstall PyQt5`)
   3. Download the SimpleDSCSModManager source code and unzip it. Create a text file in the downloaded folder and type `python SimpleDSCSModManager.py` into the file. If you are on Windows, rename the file so that it has a `.bat` extension.
   4. In the SimpleDSCSModManager directory, create a folder called "tools". Copy and paste the contents of the "tools" folder from the latest SimpleDSCSModManager release into this folder.
   5. You can run SimpleDSCSModManager by running the `.bat` file. You can also create a shortcut to this `.bat` file and run that instead.
2. Alternatively, Windows users can download the latest release of SimpleDSCSModManager. Extract it somewhere on your computer and run `SimpleDSCSModManager.exe`. This may or may not work on your particular system.

## Usage
A guide to usage can be found in the accompanying documentation in the file `user_guide.pdf`. Detailed guidance on creating mods for SimpleDSCSModManager is found in `modders_guide.pdf`.

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
1. Install [Boost](https://www.boost.org/) for your operating system. In the SimpleDSCSModManager source code, edit `sdmmlib/dscstools/setup.py` such that the `include_dirs` and `library_dirs` point to the include dir and library dirs of your Boost install. If you are using Windows, these might be automatically detected for you.
2. Install [Python 3.8 or greater](https://www.python.org/).
3. Install Cython via `pip` with `pip install cython`.
4. Install PyQt5 via `pip` with `pip install PyQt5`
5. In the root directory of the SimpleDSCSModManager source, open a terminal and execute `python setup.py`.

You can now run the mod manager from the source code root directory with `python SimpleDSCSModManager.py`.

### Building PyInstaller
You may also want to freeze the program into an executable with a tool such as PyInstaller. However, the official distribution of PyInstaller often triggers anti-virus protection software. Building PyInstaller yourself tends to alleviate this issue.
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
2. Thanks to SydMontague, KiroAkashima, and A Heroic Panda for their patience and assistance debugging critical issues with the alpha builds.
3. Releases are compiled with [Pyinstaller](https://www.pyinstaller.org/).
