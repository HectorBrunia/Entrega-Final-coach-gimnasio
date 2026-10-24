"""Modo demo sin Docker, sin red y sin clave de Gemini (`python scripts/demo.py`).

Usa el grafo LangGraph real, las reglas de seguridad reales y el catalogo real; solo se
sustituyen el LLM (salidas estructuradas guionadas), la persistencia (en memoria), Qdrant (en
memoria) y los codificadores de embeddings (deterministas, sin descargar modelos).
"""
