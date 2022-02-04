@ECHO off

FOR %%f IN (./languages/src/*.ts) DO ( 
    ECHO Compiling %%f...
    qt5-tools lrelease ./languages/src/%%f -qm ./languages/%%~nf.qm
)
