cd "c:\Users\pcn\Workspace\MusicalVideoPlayer_Player\"
git log -1 > VersionInfo.log
"c:\Program Files (x86)\Python27\python.exe" C:\development\pyinstaller\Makespec.py --paths gui;src -i graphics\TaktPlayer.ico PlayerMain.py
"c:\Program Files (x86)\Python27\python.exe" C:\development\pyinstaller\Build.py -y PlayerMain.spec
copy dist\PlayerMain\PlayerMain.exe documentation\Output\PlayerMain_debug.exe
"c:\Program Files (x86)\Python27\python.exe" C:\development\pyinstaller\Makespec.py --paths gui;src -i graphics\TaktPlayer.ico --windowed PlayerMain.py
"c:\Program Files (x86)\Python27\python.exe" C:\development\pyinstaller\Build.py -y PlayerMain.spec
