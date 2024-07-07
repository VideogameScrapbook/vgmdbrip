@REM This batch script is for allowing dragging files/folders onto the file's icon to easily use them as input for the Python script.

@REM Rather than using this batch file, can open python script from a file's right-click menu using Types.exe (https://ystr.github.io/types/) and action similar to following:
@REM "C:\PortableApps\WPy\python-3.7.1.amd64\pythonw.exe" "C:\scripts\foobar2000.py" "%1"%*

@REM Turn on displaying of commands.
@ECHO OFF

@REM SETLOCAL


@REM WARNING: %~dp0 seems to return first parameter's folder instead of script's folder when the batch file is called by a different script.
SET "scriptDrive=%~d0"
SET "scriptFolder=%~dp0"
SET "scriptName=%~n0"

@REM %scriptDrive%
@REM CD "%scriptFolder%"

@REM https://stackoverflow.com/a/16144756
python.exe "%scriptFolder%%scriptName%.py" %*

@REM PAUSE
