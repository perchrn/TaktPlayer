@echo off
ECHO ====================================================================
ECHO This will create shortcuts to the application in the current folder.
ECHO You can move or copy the links anywhere you want."
ECHO ====================================================================
pause
set linkDirectory=%~dp0


set linkName=TaktPlayer
if exist %linkName%.lnk del %linkName%.lnk
if exist %linkDirectory%\myshortcut.vbs del %linkDirectory%\myshortcut.vbs

:: CREATE %linkDirectory%\myshortcut.vbs FILE CONTAINING ALL COMMANDS for the vb script to create a shortcut of your file
FOR /F "tokens=1* delims=;" %%B IN ("Set oWS = WScript.CreateObject("WScript.Shell")") do echo %%B>>%linkDirectory%\myshortcut.vbs   
FOR /F "tokens=1* delims=;" %%B IN ("sLinkFile = "%linkDirectory%%linkName%.lnk"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("Set oLink = oWS.CreateShortcut(sLinkFile)") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   oLink.TargetPath = "%linkDirectory%%linkName%.bat"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   '	oLink.Arguments = """) do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   	oLink.Description = "%linkName%"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   '	oLink.HotKey = """) do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   	oLink.IconLocation = "%linkDirectory%graphics\%linkName%.ico"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   '	oLink.WindowStyle = "1"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   	oLink.WorkingDirectory = "%linkDirectory%"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   oLink.Save") do echo %%B>>%linkDirectory%\myshortcut.vbs

:: EXECUTE myshortcut.vbs
	CSCRIPT myshortcut.vbs

set linkName=TaktPlayerNoGUI
if exist %linkName%.lnk del %linkName%.lnk
if exist %linkDirectory%\myshortcut.vbs del %linkDirectory%\myshortcut.vbs

:: CREATE %linkDirectory%\myshortcut.vbs FILE CONTAINING ALL COMMANDS for the vb script to create a shortcut of your file
FOR /F "tokens=1* delims=;" %%B IN ("Set oWS = WScript.CreateObject("WScript.Shell")") do echo %%B>>%linkDirectory%\myshortcut.vbs   
FOR /F "tokens=1* delims=;" %%B IN ("sLinkFile = "%linkDirectory%%linkName%.lnk"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("Set oLink = oWS.CreateShortcut(sLinkFile)") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   oLink.TargetPath = "%linkDirectory%%linkName%.bat"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   '	oLink.Arguments = """) do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   	oLink.Description = "%linkName%"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   '	oLink.HotKey = """) do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   	oLink.IconLocation = "%linkDirectory%graphics\%linkName%.ico"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   '	oLink.WindowStyle = "1"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   	oLink.WorkingDirectory = "%linkDirectory%"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   oLink.Save") do echo %%B>>%linkDirectory%\myshortcut.vbs

:: EXECUTE myshortcut.vbs
	CSCRIPT myshortcut.vbs

set linkName=TaktGui
if exist %linkName%.lnk del %linkName%.lnk
if exist %linkDirectory%\myshortcut.vbs del %linkDirectory%\myshortcut.vbs

:: CREATE %linkDirectory%\myshortcut.vbs FILE CONTAINING ALL COMMANDS for the vb script to create a shortcut of your file
FOR /F "tokens=1* delims=;" %%B IN ("Set oWS = WScript.CreateObject("WScript.Shell")") do echo %%B>>%linkDirectory%\myshortcut.vbs   
FOR /F "tokens=1* delims=;" %%B IN ("sLinkFile = "%linkDirectory%%linkName%.lnk"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("Set oLink = oWS.CreateShortcut(sLinkFile)") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   oLink.TargetPath = "%linkDirectory%%linkName%.bat"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   '	oLink.Arguments = """) do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   	oLink.Description = "%linkName%"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   '	oLink.HotKey = """) do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   	oLink.IconLocation = "%linkDirectory%graphics\%linkName%.ico"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   '	oLink.WindowStyle = "0"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   	oLink.WorkingDirectory = "%linkDirectory%"") do echo %%B>>%linkDirectory%\myshortcut.vbs
FOR /F "tokens=1* delims=;" %%B IN ("   oLink.Save") do echo %%B>>%linkDirectory%\myshortcut.vbs

:: EXECUTE myshortcut.vbs
	CSCRIPT myshortcut.vbs

::ECHO Your shortcut should now be created
::pause
:: Delete vbs script
	del %linkDirectory%\myshortcut.vbs
