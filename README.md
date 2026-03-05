# DocGen (Streamlit UI + FastAPI API + Worker)
Generación masiva de documentos (DOCX template + Excel) → PDFs individuales + ZIP final.

## Servicios (docker compose)
- **api**: FastAPI (endpoints + trazabilidad)
- **worker**: Celery worker (procesa lotes; incluye LibreOffice para DOCX→PDF)
- **ui**: Streamlit (subir archivos, lanzar lote, ver progreso y descargar ZIP)
- **redis**: cola para Celery
- **db**: Postgres (opcional; por defecto el API usa SQLite si no configuras DATABASE_URL)

## Quickstart (Docker)
1. Instala Docker Desktop.
2. Desde la carpeta raíz:
   ```bash
   docker compose up --build
   ```
3. Abre:
   - UI Streamlit: http://localhost:8501
   - API FastAPI docs: http://localhost:8000/docs

## Flujo
1) Subes **datos.xlsx** + **plantilla.docx** (variables `{{NombreColumna}}` iguales al Excel).  
2) Das un patrón de nombre, p.ej: `Proceso_{NumeroProceso}_{NombreContribuyente}`  
3) Se genera un PDF por fila y al final un `salida.zip` con todos los PDFs.

## Notas
- Para DOCX→PDF se usa LibreOffice (`soffice --headless`). En Windows fuera de Docker, debes instalar LibreOffice.
- En producción: cambia storage a S3/Azure Blob y añade auth (JWT) en la API.
