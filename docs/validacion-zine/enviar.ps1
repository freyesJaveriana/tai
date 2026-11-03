# Validación US14.1: copia por scp los trabajos de esta carpeta y las 10 entrevistas del piloto (los .json reducidos)
# a /zine/HPC02S1/freyes/tg4L/validacion/{trabajos,entrevistas,logs}. No lanza ningún trabajo: los sbatch los lanza
# el humano (AUTONOMIA-01). Las entrevistas van solo al clúster, nunca a Git; la copia temporal local se borra al final.
#   .\enviar.ps1 -Piloto <repo del TG>\02-procedimientos\03-Corpus\salida\piloto [-Servidor javeriana]
param([Parameter(Mandatory)][string]$Piloto, [string]$Servidor = 'javeriana')
$ErrorActionPreference = 'Stop'
$aqui = $PSScriptRoot
$base = '/zine/HPC02S1/freyes/tg4L'
$tmp = Join-Path ([IO.Path]::GetTempPath()) "validacion-zine-$PID"
$val = Join-Path $tmp 'validacion'
$trabajos = Join-Path $val 'trabajos'
New-Item -ItemType Directory -Force $trabajos, (Join-Path $val 'entrevistas'), (Join-Path $val 'logs') | Out-Null
try {
    Copy-Item (Join-Path $aqui '*.sbatch'), (Join-Path $aqui 'comun.sh'), (Join-Path $aqui '*.py') -Destination $trabajos
    Copy-Item -Recurse (Join-Path $aqui 'paquete_prueba') $trabajos
    # Los scripts deben llegar con fin de línea LF aunque Git los haya sacado con CRLF.
    $utf8 = New-Object Text.UTF8Encoding $false
    Get-ChildItem -Recurse -File $trabajos | ForEach-Object {
        [IO.File]::WriteAllText($_.FullName, ([IO.File]::ReadAllText($_.FullName) -replace "`r`n", "`n"), $utf8)
    }
    $entrevistas = @(Get-ChildItem (Join-Path $Piloto '*.json'))
    if ($entrevistas.Count -ne 10) { Write-Warning "Se esperaban las 10 entrevistas del piloto; hay $($entrevistas.Count)" }
    Copy-Item $entrevistas -Destination (Join-Path $val 'entrevistas')
    Set-Content (Join-Path $val 'logs\LEEME.txt') 'Logs de los trabajos de validación US14.1.'
    scp -r -q $val "${Servidor}:$base/"
    if ($LASTEXITCODE) { throw 'scp falló' }
    Write-Host "Copiados $((Get-ChildItem -File $trabajos).Count) trabajos y $($entrevistas.Count) entrevistas a $base/validacion"
}
finally {
    Remove-Item -Recurse -Force $tmp
}
