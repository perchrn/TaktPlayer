@ECHO off

set taktRoot=%~dp0


IF DEFINED takt_paths_initialized (GOTO :runtakt)

ECHO Setting Environment Variables:
ECHO #################################

::Adding local ffmpeg to path
set PATH=%taktRoot%ffmpeg\bin;%PATH%

set PATH=%taktRoot%OpenCV\bin;%PATH%

set PATH=%taktRoot%Python27;%PATH%
ECHO PATH:
ECHO %PATH%
ECHO ----------------------------------

set PYTHONPATH=%taktRoot%src;%taktRoot%gui;%PYTHONPATH%

set PYTHONPATH=%takt_portable_root%takt;%PYTHONPATH%
ECHO PYTHONPATH:
ECHO %PYTHONPATH%
ECHO ----------------------------------

SET takt_paths_initialized=1
ECHO ##################################

:runtakt


python.exe  %taktRoot%PlayerMain.py --nogui
IF %errorlevel% NEQ 0 (PAUSE)
