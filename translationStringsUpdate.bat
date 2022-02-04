@ECHO off
SETLOCAL enabledelayedexpansion

SET py_files = ""
FOR /r %%f IN (*.py) DO (
    SET py_files=!py_files! "!%%f!"
)

FOR %%f IN (./languages/src/*.ts) DO ( 
    ECHO Updating %%f...
    pylupdate5 %py_files% -ts ./languages/src/%%f
)
