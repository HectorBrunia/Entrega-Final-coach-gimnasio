# API del coach de gimnasio (FastAPI + LangGraph). Se usa desde docker-compose.yml (servicio api).
FROM python:3.12.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # caches de modelos (sentence-transformers y fastembed) en un volumen con nombre
    HF_HOME=/cache/huggingface \
    FASTEMBED_CACHE_PATH=/cache/fastembed

WORKDIR /srv/coach

# 1) Dependencias (capa cacheada mientras pyproject.toml no cambie).
#    torch en su build CPU: sentence-transformers lo necesita y la build por defecto trae CUDA (varios GB).
COPY pyproject.toml ./
RUN mkdir app && touch app/__init__.py \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.0 \
    && pip install . \
    && pip uninstall -y coach-gimnasio \
    && rm -rf app build *.egg-info

# 2) Codigo de la aplicacion, migraciones, scripts y datos (catalogo y guias)
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
