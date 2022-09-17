# SimpleDSCSModManager
**If you have difficulties installing mods or if using mods causes the game to crash or behave unexpectedly, run the mod manager as an administrator or install the game in a location outside of Program Files on Windows.** 

**Executables can be found in the "Releases" tab on the right-hand side of this page.**

A poorly-named mod manager for the PC release of Digimon Story: Cyber Sleuth Complete Edition. Windows binaries are provided, and you will have to build the mod manager yourself if you are running a different operating system. Instructions on how to do this are provided in [Building Dependencies](#building-dependencies). Note that, since the mod manager uses [VGAudio](https://github.com/Thealexbarney/VGAudio) for its WAV->HCA conversion utility for mod authors, this feature is unavailable on non-Windows platforms.

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
1. Windows users can download the latest release of SimpleDSCSModManager. Extract it somewhere on your computer and run `SimpleDSCSModManager.exe`.
2. You can also build the mod manager from source, which will be required for non-Windows systems. Although the mod manager is mostly written in Python, it has several dependencies written in C++ that first require compilation.
   1. Follow the instructions in the [Building Dependencies](#building-dependencies) section of the readme to build the mod manager C++ extensions.
   2. You can then do one of two things:
      1. Create a text file in the source code folder and type `python SimpleDSCSModManager.py` into the file. If you are on Windows, rename the file so that it has a `.bat` extension; for Linux this should have a `.sh` extension. You can run SimpleDSCSModManager by running the `.bat`/`.sh` file. You can also create a shortcut to this file and run that instead, as long as the working directory is set to the SimpleDSCSModManager.
      2. Compile the Python code to an executable file, using PyInstaller or Nuitka. Nuitka instructions are being worked on, but you can see how to create a PyInstaller executable in the [Building PyInstaller](#building-pyinstaller) and [Building The Executable](#building-the-executable) sections.
      

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
1. You will require a C++ compiler. 
   - On Windows, MSVC is recommended, which you can obtain by installing [Visual Studio](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2017) on your system with the Visual C++ submodules. 
   - On Linux, compilation has been tested with GCC 9.
2. Install [Python 3.8 or greater](https://www.python.org/) for your system. Many people use [Anaconda](https://www.anaconda.com/) alongside or in addition to a system Python install since the `conda` system allows multiple versions of Python to be installed simultaneously, which you are free to do as an alternative.
3. Install Cython via `pip` with `pip install cython` from a terminal/command prompt. Anaconda users can use `conda install cython`.
4. Install PyQt5 via `pip` with `pip install PyQt5` from a terminal/command prompt. Anaconda users can use `conda install PyQt5`.
5. In the root directory of the SimpleDSCSModManager source, open a terminal and execute `python setup.py`. It will do the following:
    - Download and compile [Boost](https://www.boost.org/) [1.78.0](https://www.boost.org/users/history/version_1_78_0.html), a dependency of DSCSTools. **This will take a significant amount of time**.
    - Compile Python bindings for [DSCSTools](https://github.com/SydMontague/DSCSTools)
    - Compile Python bindings for the [Squirrel](http://www.squirrel-lang.org/) [2.2.4](https://sourceforge.net/projects/squirrel/files/squirrel2/squirrel%202.2.4%20stable/) compiler; the scripting language used by Cyber Sleuth
    - Compile Python bindings for SydMontague's fork of 64-bit [NutCracker](https://github.com/SydMontague/NutCracker), a decompiler for Squirrel scripts so that the original game scripts can be edited
    - Move the DSCSTools Structure files to the SimpleDSCSModManager root directory, so that DSCSTools can find them when the mod manager tries to unpack and repack the game data

You can now run the mod manager from the source code root directory with `python SimpleDSCSModManager.py`.

### Building PyInstaller
You may also want to freeze the program into an executable with a tool such as PyInstaller. However, the official distribution of PyInstaller often triggers anti-virus protection software because some viruses are packaged with PyInstaller, causing anti-virus software to falsely flag PyInstaller itself as a virus. Building PyInstaller yourself tends to alleviate this issue.
1. Clone the PyInstaller source with `git clone https://github.com/pyinstaller/pyinstaller`, or download the source code from the webpage using your browser.
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
