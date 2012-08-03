@ECHO off

set taktRoot=%~dp0

IF DEFINED takt_paths_initialized (GOTO :runtakt)

ECHO Setting Environment Variables:
ECHO #################################

::Adding local ffmpeg to path
set PATH=%taktRoot%ffmpeg\bin;%PATH%

set PATH=%taktRoot%Python27;%PATH%
ECHO PATH:
ECHO %PATH%
ECHO ----------------------------------

copy %taktRoot%GuiMain.py %taktRoot%GuiMain.pyw
set PYTHONPATH=%taktRoot%gui;%taktRoot%src;%PYTHONPATH%

set PYTHONPATH=%kivy_portable_root%kivy;%PYTHONPATH%
ECHO PYTHONPATH:
ECHO %PYTHONPATH%
ECHO ----------------------------------

SET takt_paths_initialized=1
ECHO ##################################

:runtakt

start %taktRoot%GuiMain.pyw
IF %errorlevel% NEQ 0 (PAUSE)
exit
