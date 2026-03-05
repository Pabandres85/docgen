# DocGen (Streamlit UI + FastAPI API + Worker)
Generacion masiva de documentos (DOCX template + Excel) -> PDFs individuales + ZIP final.

## Servicios (docker compose)
- `api`: FastAPI (endpoints + trazabilidad).
- `worker`: Celery worker (procesa lotes; incluye LibreOffice para DOCX->PDF).
- `ui`: Streamlit (subir archivos, lanzar lote, ver progreso y descargar ZIP).
- `redis`: cola para Celery.
- `db`: Postgres (el API puede usar SQLite si no configuras `DATABASE_URL`).

## Quickstart (Docker)
1. Instala Docker Desktop.
2. Desde la carpeta raiz:
```bash
docker compose up --build
```
3. La API aplica migraciones automaticamente al iniciar (`alembic upgrade head`).
4. Abre:
- UI Streamlit: http://localhost:8501
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/health
- API readiness: http://localhost:8000/ready

## Flujo
1. Subes `datos.xlsx` + `plantilla.docx` (variables `{{NombreColumna}}` iguales al Excel).
2. Das un patron de nombre, por ejemplo `Proceso_{NumeroProceso}_{NombreContribuyente}`.
3. Se genera un PDF por fila y al final un `salida.zip` con todos los PDFs.

## Notas
- Para DOCX->PDF se usa LibreOffice (`soffice --headless`).
- En produccion: cambiar storage a S3/Azure Blob y agregar auth (JWT) en API.

## Hardening basico incluido
- Rate limiting configurable por IP (`RATE_LIMIT_*`).
- Validacion de `Host` por lista permitida (`TRUSTED_HOSTS`).
- Cabeceras de seguridad HTTP en respuestas API.
- CORS configurable por ambiente (`ENVIRONMENT`, `CORS_ORIGINS`).
