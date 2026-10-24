# API del coach de gimnasio (FastAPI + LangGraph). Se usa desde docker-compose.yml (servicios
# api e init: init aplica las migraciones e ingiere el corpus antes de que arranque la api).
FROM python:3.12.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # caches de modelos (sentence-transformers y fastembed) en un volumen con nombre
    HF_HOME=/cache/huggingface \
    FASTEMBED_CACHE_PATH=/cache/fastembed

WORKDIR /srv/coach

# 1) Dependencias (capa cacheada mientras requirements.txt no cambie). requirements.txt fija
#    las mismas versiones que pyproject.toml y torch en su build CPU (indice extra de PyTorch):
#    la build por defecto de Linux trae CUDA (varios GB).
COPY requirements.txt ./
RUN pip install -r requirements.txt

# 2) Codigo de la aplicacion, migraciones, scripts y datos (catalogo y guias)
COPY pyproject.toml ./
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts
COPY data ./data
RUN pip install --no-deps . && rm -rf build *.egg-info

# Usuario sin privilegios; el cache de modelos le pertenece (el volumen hereda el propietario)
RUN useradd --create-home --uid 10001 coach \
    && mkdir -p /cache/huggingface /cache/fastembed \
    && chown -R coach:coach /cache
USER coach

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
