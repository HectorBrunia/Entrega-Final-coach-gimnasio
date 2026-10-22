#!/usr/bin/env bash
# Levanta el coach de gimnasio con un solo comando: bash run.sh
#
# 1. Comprueba que exista .env (si no, lo crea desde .env.example y se detiene).
# 2. docker compose up -d --build (api, postgres, redis, qdrant, phoenix).
# 3. Migraciones de Alembic e ingesta del catalogo y las guias en Qdrant (idempotente).
# 4. Espera a que GET /health responda 200 y muestra las URLs.
#
# Es seguro ejecutarlo varias veces: las migraciones y la ingesta no repiten trabajo hecho.
# COACH_ENV_FILE permite usar otro archivo de entorno en lugar de .env.
set -euo pipefail

cd "$(dirname "$0")"

ENV_FILE="${COACH_ENV_FILE:-.env}"
API_URL="http://localhost:8000"
TIMEOUT_SALUD_SEG="${TIMEOUT_SALUD_SEG:-180}"

if [ ! -f "$ENV_FILE" ]; then
  if [ "$ENV_FILE" = ".env" ]; then
    cp .env.example .env
    echo "Se creo .env a partir de .env.example."
    echo "Completa GOOGLE_API_KEY y GEMINI_MODEL en .env y vuelve a ejecutar: bash run.sh"
  else
    echo "ERROR: no existe el archivo de entorno '$ENV_FILE' (COACH_ENV_FILE)." >&2
  fi
  exit 1
fi

# Solo se comprueba que las variables tengan valor; nunca se muestra su contenido.
for var in GOOGLE_API_KEY GEMINI_MODEL; do
  if ! grep -Eq "^[[:space:]]*${var}[[:space:]]*=[[:space:]]*[^[:space:]#]" "$ENV_FILE"; then
    echo "ERROR: $var esta vacia en $ENV_FILE. Completala y vuelve a ejecutar: bash run.sh" >&2
    exit 1
  fi
done

export COACH_ENV_FILE="$ENV_FILE"

echo "==> Construyendo y levantando los servicios (la primera vez tarda varios minutos)"
docker compose up -d --build --wait --wait-timeout 300

echo "==> Migraciones de Alembic"
docker compose exec -T api alembic upgrade head

echo "==> Ingesta del catalogo y las guias en Qdrant (la primera vez descarga los modelos)"
docker compose exec -T api python scripts/ingerir.py

echo "==> Esperando a que la API responda en $API_URL/health"
inicio=$(date +%s)
while true; do
  codigo=$(curl -s -o /tmp/coach_health.$$ -w '%{http_code}' "$API_URL/health" || echo "000")
  if [ "$codigo" = "200" ]; then
    rm -f /tmp/coach_health.$$
    break
  fi
  if [ $(( $(date +%s) - inicio )) -ge "$TIMEOUT_SALUD_SEG" ]; then
    echo "ERROR: /health no respondio 200 en ${TIMEOUT_SALUD_SEG} s (ultimo codigo: $codigo)." >&2
    if [ -s /tmp/coach_health.$$ ]; then
      echo "Respuesta: $(cat /tmp/coach_health.$$)" >&2
      degradados=$(grep -o '"[a-z]*":"error"' /tmp/coach_health.$$ | cut -d'"' -f2 | tr '\n' ' ' || true)
      [ -n "$degradados" ] && echo "Servicios degradados: $degradados" >&2
    fi
    rm -f /tmp/coach_health.$$
    docker compose ps >&2
    echo "Ultimas lineas del log de la API:" >&2
    docker compose logs --tail 30 api >&2
    exit 1
  fi
  sleep 2
done

echo
echo "Coach de gimnasio listo."
echo "  API (OpenAPI):     $API_URL/docs"
echo "  Salud:             $API_URL/health"
echo "  Trazas (Phoenix):  http://localhost:6006"
echo "Para detenerlo: docker compose stop"
