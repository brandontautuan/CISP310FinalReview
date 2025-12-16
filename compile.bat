@echo off
REM Simple batch file to compile LaTeX
REM Usage: compile.bat

echo Compiling template.tex...
echo.

"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe" template.tex

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo Compilation successful! 
    echo PDF created: template.pdf
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Compilation failed. 
    echo Check the error messages above.
    echo ========================================
)
echo.
pause

