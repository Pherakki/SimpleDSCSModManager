@ECHO off

FOR %%f IN (./languages/src/*.ts) DO ( 
    ECHO Compiling %%f...
    lrelease ./languages/src/%%f -qm ./languages/%%~nf.qm
)
