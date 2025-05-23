@echo off

echo "Building CL application..."
pyinstaller dd_cli.spec

echo "Building GUI application..."
pyinstaller main_gui.spec

echo "All applications built!"