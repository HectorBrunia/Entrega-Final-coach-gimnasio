# Levanta el coach de gimnasio con un solo comando (Windows): .\run.ps1
#
# 1. Si no existe .env, lo crea desde .env.example (y sigue).
# 2. Si faltan GOOGLE_API_KEY o GEMINI_MODEL, avisa y sigue: la API arranca sin el coach
#    conversacional (/chat y /hitl responden 503 explicando que falta configurar).
# 3. docker compose up -d --build: postgres, redis, qdrant, phoenix, init (migraciones de
#    Alembic + ingesta idempotente en Qdrant) y api. Equivale a `docker compose up -d`.
# 4. Espera a que GET /health responda 200 y muestra las URLs.
#
# Es seguro ejecutarlo varias veces: las migraciones y la ingesta no repiten trabajo hecho.
# $env:COACH_ENV_FILE permite usar otro archivo de entorno en lugar de .env; $env:API_PORT, otro puerto.
# 'Continue': docker escribe su progreso en stderr y con 'Stop' PowerShell 5.1 lo trataria como
# error terminante al redirigir la salida. Cada paso comprueba $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
Set-Location -Path $PSScriptRoot

$envFile = if ($env:COACH_ENV_FILE) { $env:COACH_ENV_FILE } else { '.env' }
$apiPort = if ($env:API_PORT) { $env:API_PORT } else { '8000' }
$phoenixPort = if ($env:PHOENIX_PORT) { $env:PHOENIX_PORT } else { '6006' }
$apiUrl = "http://localhost:$apiPort"
$timeoutSalud = if ($env:TIMEOUT_SALUD_SEG) { [int]$env:TIMEOUT_SALUD_SEG } else { 300 }

if (-not (Test-Path $envFile)) {
    if ($envFile -eq '.env') {
        Copy-Item .env.example .env
        Write-Host 'Se creo .env a partir de .env.example.'
    } else {
        Write-Host "ERROR: no existe el archivo de entorno '$envFile' (COACH_ENV_FILE)." -ForegroundColor Red
        exit 1
    }
}

# Solo se comprueba que las variables tengan valor; nunca se muestra su contenido.
$faltaLlm = $false
foreach ($var in 'GOOGLE_API_KEY', 'GEMINI_MODEL') {
    if (-not (Select-String -Path $envFile -Pattern "^\s*$var\s*=\s*[^\s#]" -Quiet)) {
        $faltaLlm = $true
    }
}
if ($faltaLlm) {
    Write-Host "AVISO: GOOGLE_API_KEY o GEMINI_MODEL vacias en $envFile." -ForegroundColor Yellow
    Write-Host '       El sistema arranca igual (salud, /docs, usuarios, perfil, entrenos y rutinas),'
    Write-Host '       pero /chat y /hitl responderan 503 hasta que las completes y vuelvas a ejecutar run.ps1.'
}

$env:COACH_ENV_FILE = $envFile

Write-Host '==> Construyendo y levantando los servicios (la primera vez tarda varios minutos:'
Write-Host '    imagenes, dependencias y descarga de los modelos de embeddings en el servicio init)'
docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: docker compose up fallo (codigo $LASTEXITCODE). Estado y log del servicio init:" -ForegroundColor Red
    docker compose ps -a
    docker compose logs --tail 40 init
    exit 1
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
    if ($codigo -eq 200) { Write-Host "Salud: $cuerpo"; break }
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
        docker compose ps -a
        Write-Host 'Ultimas lineas del log de init y de la API:'
        docker compose logs --tail 30 init api
        exit 1
    }
    Start-Sleep -Seconds 2
}

Write-Host ''
Write-Host 'Coach de gimnasio listo.'
Write-Host "  API (OpenAPI):     $apiUrl/docs"
Write-Host "  Salud:             $apiUrl/health"
Write-Host "  Trazas (Phoenix):  http://localhost:$phoenixPort"
if ($faltaLlm) {
    Write-Host "  Coach conversacional: SIN CONFIGURAR (completa GOOGLE_API_KEY y GEMINI_MODEL en $envFile)"
}
Write-Host 'Para detenerlo: docker compose stop'
