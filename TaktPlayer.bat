@ECHO off

set taktRoot=%~dp0

set kivy_portable_root=%taktRoot%Kivy-1.0.9-w32\
ECHO botstrapping Kivy @ %kivy_portable_root%


IF DEFINED kivy_paths_initialized (GOTO :runkivy)

ECHO Setting Environment Variables:
ECHO #################################

set GST_REGISTRY=%kivy_portable_root%gstreamer\registry.bin
ECHO GST_REGISTRY
ECHO %GST_REGISTRY%
ECHO ---------------

set GST_PLUGIN_PATH=%kivy_portable_root%gstreamer\lib\gstreamer-0.10
ECHO GST_PLUGIN_PATH:
ECHO %GST_PLUGIN_PATH%
ECHO ---------------

set PATH=%kivy_portable_root%;%kivy_portable_root%Python;%kivy_portable_root%gstreamer\bin;%kivy_portable_root%MinGW\bin;%PATH%
ECHO PATH:
ECHO %PATH%
ECHO ----------------------------------

set PYTHONPATH=%kivy_portable_root%kivy;%PYTHONPATH%
ECHO PYTHONPATH:
ECHO %PYTHONPATH%
ECHO ----------------------------------

SET kivy_paths_initialized=1
ECHO ##################################


:runkivy

ECHO done bootstraping kivy...\n

::Adding local ffmpeg to path
set PATH=%taktRoot%ffmpeg\bin;%PATH%

set PATH=%taktRoot%OpenCV\bin;%PATH%

set PYTHONPATH=%taktRoot%src;%taktRoot%gui;%PYTHONPATH%

python.exe  %taktRoot%PlayerMain.py
IF %errorlevel% NEQ 0 (PAUSE)
