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
TIMEOUT_SALUD_SEG="${TIMEOUT_SALUD_SEG:-300}"

# Herramientas necesarias: sin ellas no se puede levantar el stack con este script.
falta_herramienta() {
  echo "ERROR: $1" >&2
  echo "       Sin Docker puedes ver el sistema funcionando igual: README.md, seccion" >&2
  echo "       'Guia rapida para la correccion', camino A (python scripts/demo.py y pytest)." >&2
  exit 1
}
command -v docker >/dev/null 2>&1 || falta_herramienta "no se encontro 'docker' en el PATH."
docker compose version >/dev/null 2>&1 || falta_herramienta "no esta disponible 'docker compose' (Compose v2)."
command -v curl >/dev/null 2>&1 || falta_herramienta "no se encontro 'curl' en el PATH (se usa para esperar a /health)."

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

# Puertos: compose los interpola desde el entorno o desde el .env del proyecto; aqui se leen
# igual para sondear el mismo puerto (el entorno tiene prioridad).
valor_en_env() {
  [ -f .env ] || return 0
  sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*\([0-9][0-9]*\)[[:space:]]*\(#.*\)\{0,1\}$/\1/p" .env | tr -d '\r' | tail -n 1
}
API_PORT="${API_PORT:-$(valor_en_env API_PORT)}"
PHOENIX_PORT="${PHOENIX_PORT:-$(valor_en_env PHOENIX_PORT)}"
API_URL="http://localhost:${API_PORT:-8000}"

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
echo "  Chat web:          $API_URL/"
echo "  API (OpenAPI):     $API_URL/docs"
echo "  Salud:             $API_URL/health"
echo "  Trazas (Phoenix):  http://localhost:${PHOENIX_PORT:-6006}"
if [ "$falta_llm" = "1" ]; then
  echo "  Coach conversacional: SIN CONFIGURAR (completa GOOGLE_API_KEY y GEMINI_MODEL en $ENV_FILE)"
fi
echo "Para detenerlo: docker compose stop"
