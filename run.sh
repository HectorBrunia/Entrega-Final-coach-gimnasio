#!/usr/bin/env bash
# Levanta el coach de gimnasio con un solo comando: bash run.sh   (o ./run.sh)
#
# 1. Si no existe .env, lo crea desde .env.example (y sigue).
# 2. Si faltan GOOGLE_API_KEY o GEMINI_MODEL, avisa y sigue: la API arranca sin el coach
#    conversacional (/chat y /hitl responden 503 explicando que falta configurar).
# 3. docker compose up -d --build: postgres, redis, qdrant, phoenix, init (migraciones de
#    Alembic + ingesta idempotente en Qdrant) y api. Equivale a `docker compose up -d`.
# 4. Espera a que GET /health responda 200 y muestra las URLs.
#
# Es seguro ejecutarlo varias veces: las migraciones y la ingesta no repiten trabajo hecho.
# COACH_ENV_FILE permite usar otro archivo de entorno en lugar de .env; API_PORT, otro puerto.
set -euo pipefail

cd "$(dirname "$0")"

ENV_FILE="${COACH_ENV_FILE:-.env}"
API_URL="http://localhost:${API_PORT:-8000}"
TIMEOUT_SALUD_SEG="${TIMEOUT_SALUD_SEG:-300}"

if [ ! -f "$ENV_FILE" ]; then
  if [ "$ENV_FILE" = ".env" ]; then
    cp .env.example .env
    echo "Se creo .env a partir de .env.example."
  else
    echo "ERROR: no existe el archivo de entorno '$ENV_FILE' (COACH_ENV_FILE)." >&2
    exit 1
  fi
fi

# Solo se comprueba que las variables tengan valor; nunca se muestra su contenido.
falta_llm=0
for var in GOOGLE_API_KEY GEMINI_MODEL; do
  if ! grep -Eq "^[[:space:]]*${var}[[:space:]]*=[[:space:]]*[^[:space:]#]" "$ENV_FILE"; then
    falta_llm=1
  fi
done
if [ "$falta_llm" = "1" ]; then
  echo "AVISO: GOOGLE_API_KEY o GEMINI_MODEL vacias en $ENV_FILE."
  echo "       El sistema arranca igual (salud, /docs, usuarios, perfil, entrenos y rutinas),"
  echo "       pero /chat y /hitl responderan 503 hasta que las completes y vuelvas a ejecutar run.sh."
fi

export COACH_ENV_FILE="$ENV_FILE"

echo "==> Construyendo y levantando los servicios (la primera vez tarda varios minutos:"
echo "    imagenes, dependencias y descarga de los modelos de embeddings en el servicio init)"
if ! docker compose up -d --build; then
  echo "ERROR: docker compose up fallo. Estado y log del servicio init:" >&2
  docker compose ps -a >&2 || true
  docker compose logs --tail 40 init >&2 || true
  exit 1
fi

echo "==> Esperando a que la API responda en $API_URL/health"
inicio=$(date +%s)
cuerpo_tmp="$(mktemp 2>/dev/null || echo "/tmp/coach_health.$$")"
while true; do
  codigo=$(curl -s -o "$cuerpo_tmp" -w '%{http_code}' "$API_URL/health" || true)
  codigo="${codigo:-000}"
  if [ "$codigo" = "200" ]; then
    echo "Salud: $(cat "$cuerpo_tmp")"
    rm -f "$cuerpo_tmp"
    break
  fi
  if [ $(( $(date +%s) - inicio )) -ge "$TIMEOUT_SALUD_SEG" ]; then
    echo "ERROR: /health no respondio 200 en ${TIMEOUT_SALUD_SEG} s (ultimo codigo: $codigo)." >&2
    if [ -s "$cuerpo_tmp" ]; then
      echo "Respuesta: $(cat "$cuerpo_tmp")" >&2
      degradados=$(grep -o '"[a-z]*":"error"' "$cuerpo_tmp" | cut -d'"' -f2 | tr '\n' ' ' || true)
      [ -n "$degradados" ] && echo "Servicios degradados: $degradados" >&2
    fi
    rm -f "$cuerpo_tmp"
    docker compose ps -a >&2
    echo "Ultimas lineas del log de init y de la API:" >&2
    docker compose logs --tail 30 init api >&2
    exit 1
  fi
  sleep 2
done

echo
echo "Coach de gimnasio listo."
echo "  API (OpenAPI):     $API_URL/docs"
echo "  Salud:             $API_URL/health"
echo "  Trazas (Phoenix):  http://localhost:${PHOENIX_PORT:-6006}"
if [ "$falta_llm" = "1" ]; then
  echo "  Coach conversacional: SIN CONFIGURAR (completa GOOGLE_API_KEY y GEMINI_MODEL en $ENV_FILE)"
fi
echo "Para detenerlo: docker compose stop"
