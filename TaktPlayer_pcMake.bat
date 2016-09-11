cd "C:\Users\pcn\PycharmProjects\TaktPlayer\"
SET PATH=%PATH%;C:\Program Files (x86)\OpenCV\bin
echo 1
"c:\Program Files (x86)\Python27\python.exe" C:\Users\pcn\PycharmProjects\pyinstaller-1.5.1\Makespec.py --name=TaktPlayer --paths gui;src -i graphics\TaktPlayer.ico PlayerMain.py
echo 2
"c:\Program Files (x86)\Python27\python.exe" C:\Users\pcn\PycharmProjects\pyinstaller-1.5.1\Build.py -y TaktPlayer.spec
echo 3
copy dist\TaktPlayer\TaktPlayer.exe documentation\Output\TaktPlayer_debug.exe
echo 4
"c:\Program Files (x86)\Python27\python.exe" C:\Users\pcn\PycharmProjects\pyinstaller-1.5.1\Makespec.py --name=TaktPlayer --paths gui;src -i graphics\TaktPlayer.ico --windowed PlayerMain.py
echo 5
"c:\Program Files (x86)\Python27\python.exe" C:\Users\pcn\PycharmProjects\pyinstaller-1.5.1\Build.py -y TaktPlayer.spec
