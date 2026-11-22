# Eksport prezentacji do PDF przez PowerPoint (Windows): powershell -File prezentacja/eksport_pdf.ps1
$ErrorActionPreference = "Stop"
$pptx = Join-Path $PSScriptRoot "dane_przezycie_prezentacja.pptx"
$pdf = Join-Path $PSScriptRoot "dane_przezycie_prezentacja.pdf"
$app = New-Object -ComObject PowerPoint.Application
$p = $app.Presentations.Open($pptx, $true, $false, $false)
$p.SaveAs($pdf, 32)  # 32 = ppSaveAsPDF
$p.Close()
$app.Quit()
Write-Output "OK: $pdf"
