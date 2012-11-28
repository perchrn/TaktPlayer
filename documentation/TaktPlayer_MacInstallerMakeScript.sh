cd /Users/pcn/Workspace/MusicalVideoPlayer_Player

./TaktPlayer.macMake
mv dist/TaktPlayer.app .
./TaktGui.macMake
mv TaktPlayer.app dist/

cp -R /Users/pcn/Documents/TaktAudioUnitPlugin/build/Debug/TaktAudioUnitPlugin.component dist/
ln -s /Applications dist/
ln -s /Library/Audio/Plug-Ins/Components dist/GlobalAudioUnitsFolder
ln -s /Library/Audio/Plug-Ins/VST dist/GlobalVSTFolder

echo ""
echo ""
read -p "Fix folderlayout and press [enter] to continiue... "
echo ""

VERSION_STRING=`python src/taktVersion.py | tr "." "_"`

if [ -f TaktPlayer_V$VERSION_STRING.dmg ] ; then
    mv TaktPlayer_V$VERSION_STRING.dmg TaktPlayer_V$VERSION_STRING.dmg.old
fi
echo "Making TaktPlayer_V$VERSION_STRING.dmg ..."
hdiutil create TaktPlayer_V$VERSION_STRING.dmg -volname "Takt Player" -fs HFS+ -srcfolder "dist"
echo ""
echo ""
echo "All done."
echo ""

