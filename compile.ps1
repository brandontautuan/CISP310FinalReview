# PowerShell script to compile LaTeX file
# Usage: .\compile.ps1

$texFile = "template.tex"
$pdfFile = "template.pdf"
$pdflatex = "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"

Write-Host "Compiling $texFile..." -ForegroundColor Cyan
Write-Host ""

if (Test-Path $pdflatex) {
    & $pdflatex $texFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Compilation successful!" -ForegroundColor Green
        Write-Host "PDF created: $pdfFile" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        
        # Open PDF if it exists
        if (Test-Path $pdfFile) {
            Write-Host ""
            Write-Host "Opening PDF..." -ForegroundColor Yellow
            Start-Process $pdfFile
        }
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Compilation failed!" -ForegroundColor Red
        Write-Host "Check the error messages above." -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
    }
} else {
    Write-Host "Error: pdflatex not found at $pdflatex" -ForegroundColor Red
    Write-Host "Make sure MiKTeX is installed." -ForegroundColor Red
}

