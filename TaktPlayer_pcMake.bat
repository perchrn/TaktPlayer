cd "c:\Users\pcn\Workspace\MusicalVideoPlayer_Player\"
"c:\Program Files (x86)\Python27\python.exe" C:\development\pyinstaller\Makespec.py --name=TaktPlayer --paths gui;src -i graphics\TaktPlayer.ico PlayerMain.py
"c:\Program Files (x86)\Python27\python.exe" C:\development\pyinstaller\Build.py -y TaktPlayer.spec
copy dist\TaktPlayer\TaktPlayer.exe documentation\Output\TaktPlayer_debug.exe
"c:\Program Files (x86)\Python27\python.exe" C:\development\pyinstaller\Makespec.py --name=TaktPlayer --paths gui;src -i graphics\TaktPlayer.ico --windowed PlayerMain.py
"c:\Program Files (x86)\Python27\python.exe" C:\development\pyinstaller\Build.py -y TaktPlayer.spec
