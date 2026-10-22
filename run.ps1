# Levanta el coach de gimnasio con un solo comando (Windows): .\run.ps1
#
# 1. Comprueba que exista .env (si no, lo crea desde .env.example y se detiene).
# 2. docker compose up -d --build (api, postgres, redis, qdrant, phoenix).
# 3. Migraciones de Alembic e ingesta del catalogo y las guias en Qdrant (idempotente).
# 4. Espera a que GET /health responda 200 y muestra las URLs.
#
# Es seguro ejecutarlo varias veces: las migraciones y la ingesta no repiten trabajo hecho.
# $env:COACH_ENV_FILE permite usar otro archivo de entorno en lugar de .env.
# 'Continue': docker escribe su progreso en stderr y con 'Stop' PowerShell 5.1 lo trataria como
# error terminante al redirigir la salida. Cada paso comprueba $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
Set-Location -Path $PSScriptRoot

$envFile = if ($env:COACH_ENV_FILE) { $env:COACH_ENV_FILE } else { '.env' }
$apiUrl = 'http://localhost:8000'
$timeoutSalud = if ($env:TIMEOUT_SALUD_SEG) { [int]$env:TIMEOUT_SALUD_SEG } else { 180 }

function Invoke-Paso([string]$titulo, [scriptblock]$accion) {
    Write-Host "==> $titulo"
    & $accion
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: fallo el paso '$titulo' (codigo $LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path $envFile)) {
    if ($envFile -eq '.env') {
        Copy-Item .env.example .env
        Write-Host 'Se creo .env a partir de .env.example.'
        Write-Host 'Completa GOOGLE_API_KEY y GEMINI_MODEL en .env y vuelve a ejecutar: .\run.ps1'
    } else {
        Write-Host "ERROR: no existe el archivo de entorno '$envFile' (COACH_ENV_FILE)." -ForegroundColor Red
    }
    exit 1
}

# Solo se comprueba que las variables tengan valor; nunca se muestra su contenido.
foreach ($var in 'GOOGLE_API_KEY', 'GEMINI_MODEL') {
    if (-not (Select-String -Path $envFile -Pattern "^\s*$var\s*=\s*[^\s#]" -Quiet)) {
        Write-Host "ERROR: $var esta vacia en $envFile. Completala y vuelve a ejecutar: .\run.ps1" -ForegroundColor Red
        exit 1
    }
}

$env:COACH_ENV_FILE = $envFile

Invoke-Paso 'Construyendo y levantando los servicios (la primera vez tarda varios minutos)' {
    docker compose up -d --build --wait --wait-timeout 300
}
Invoke-Paso 'Migraciones de Alembic' { docker compose exec -T api alembic upgrade head }
Invoke-Paso 'Ingesta del catalogo y las guias en Qdrant (la primera vez descarga los modelos)' {
    docker compose exec -T api python scripts/ingerir.py
}

Write-Host "==> Esperando a que la API responda en $apiUrl/health"
$inicio = Get-Date
$codigo = 0
$cuerpo = ''
while ($true) {
    try {
        $r = Invoke-WebRequest -Uri "$apiUrl/health" -UseBasicParsing -TimeoutSec 5
        $codigo = [int]$r.StatusCode
        $cuerpo = $r.Content
    } catch {
        $resp = $_.Exception.Response
        if ($resp) {
            $codigo = [int]$resp.StatusCode
            $lector = New-Object System.IO.StreamReader($resp.GetResponseStream())
            $cuerpo = $lector.ReadToEnd()
        } else {
            $codigo = 0
            $cuerpo = ''
        }
    }
    if ($codigo -eq 200) { break }
    if (((Get-Date) - $inicio).TotalSeconds -ge $timeoutSalud) {
        Write-Host "ERROR: /health no respondio 200 en $timeoutSalud s (ultimo codigo: $codigo)." -ForegroundColor Red
        if ($cuerpo) {
            Write-Host "Respuesta: $cuerpo"
            try {
                $servicios = ($cuerpo | ConvertFrom-Json).servicios
                $degradados = $servicios.PSObject.Properties | Where-Object { $_.Value -ne 'ok' } | ForEach-Object { $_.Name }
                if ($degradados) { Write-Host "Servicios degradados: $($degradados -join ', ')" }
            } catch {}
        }
        docker compose ps
        Write-Host 'Ultimas lineas del log de la API:'
        docker compose logs --tail 30 api
        exit 1
    }
    Start-Sleep -Seconds 2
}

Write-Host ''
Write-Host 'Coach de gimnasio listo.'
Write-Host "  API (OpenAPI):     $apiUrl/docs"
Write-Host "  Salud:             $apiUrl/health"
Write-Host '  Trazas (Phoenix):  http://localhost:6006'
Write-Host 'Para detenerlo: docker compose stop'
