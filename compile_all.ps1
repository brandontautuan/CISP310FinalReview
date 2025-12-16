# PowerShell script to compile all LaTeX files
Write-Host "Compiling all LaTeX files to PDF..." -ForegroundColor Green
Write-Host ""

Get-ChildItem *.tex | ForEach-Object {
    Write-Host "Compiling $($_.Name)..." -ForegroundColor Cyan
    $output = pdflatex -interaction=nonstopmode $_.Name 2>&1 | Out-String
    $pdfName = $_.BaseName + ".pdf"
    
    if (Test-Path $pdfName) {
        $pdfSize = (Get-Item $pdfName).Length
        $sizeKB = [math]::Round($pdfSize / 1KB, 1)
        Write-Host "  SUCCESS: $pdfName created ($sizeKB KB)" -ForegroundColor Green
    } else {
        Write-Host "  ERROR: PDF not created" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Done! Check for .pdf files." -ForegroundColor Green

