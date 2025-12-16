@echo off
echo Compiling all LaTeX files to PDF...
echo.

for %%f in (*.tex) do (
    echo Compiling %%f...
    pdflatex -interaction=nonstopmode "%%f" >nul 2>&1
    if errorlevel 1 (
        echo   ERROR: Failed to compile %%f
    ) else (
        echo   SUCCESS: %%f compiled
    )
)

echo.
echo Done! Check for .pdf files.
pause

