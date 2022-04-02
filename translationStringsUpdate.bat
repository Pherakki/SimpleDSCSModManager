@ECHO off
SETLOCAL enabledelayedexpansion

TYPE NUL >pyfiles.txt

FOR /r %%f IN (*.py) DO (
    ECHO | SET /p=%%f>>pyfiles.txt
    ECHO | SET /p= >>pyfiles.txt
)

FOR %%f IN (./languages/src/*.ts) DO ( 
    ECHO Updating %%f...
    pylupdate5 <pyfiles.txt -ts ./languages/src/%%f
)

DEL pyfiles.txt
