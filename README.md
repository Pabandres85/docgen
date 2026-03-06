# DocGen — Generación Masiva de Documentos
Excel + Plantilla DOCX → PDFs individuales + ZIP final.

## Servicios (docker compose)

| Servicio | Tecnología | Puerto | Rol |
|---|---|---|---|
| `api` | FastAPI + Alembic | 8000 | REST API y trazabilidad de lotes |
| `worker` | Celery + LibreOffice | — | Procesamiento DOCX→PDF en background |
| `ui` | Streamlit | 8501 | Interfaz web (flujo completo en una página) |
| `redis` | Redis 7 | 6379 | Cola de tareas Celery |
| `db` | PostgreSQL 16 | 5432 | Persistencia de lotes e items |

## Quickstart (Docker)

1. Instala Docker Desktop.
2. Desde la carpeta raiz:
```bash
docker compose up --build
```
3. La API aplica migraciones automaticamente al iniciar (`alembic upgrade head`).
4. Abre:
   - UI: http://localhost:8501
   - API docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health
   - Readiness: http://localhost:8000/ready

## Flujo de uso

1. Sube `datos.xlsx` y `plantilla.docx` en la UI.
2. La UI detecta automaticamente las columnas del Excel y sugiere un patron de nombre.
3. Ajusta el patron si es necesario y haz clic en **Crear y ejecutar lote**.
4. La UI muestra progreso en tiempo real (timer + barra + contadores OK/Error).
5. Al finalizar, descarga `salida.zip` con un PDF por fila.

## Plantilla DOCX — reglas

El motor de plantillas es `docxtpl` (Jinja2). Variables con doble llave:

```
{{ NOMBRE }}
{{ CEDULA_NIT }}
{{ EXPEDIENTE_DE_COBRO }}
```

**Normalización automática de columnas:** el sistema convierte los encabezados del Excel
a identificadores válidos antes de renderizar:
- Espacios → `_`
- Tildes y caracteres especiales → equivalente ASCII sin acento
- Ejemplo: `EXPEDIENTE DE COBRO` → `EXPEDIENTE_DE_COBRO`

La UI muestra los nombres normalizados al subir el Excel para que puedas copiarlos
directamente en el Word sin errores.

**Error común — "run partido":** si al editar el Word la variable queda internamente
fragmentada (`{{ NOM` + `BRE }}`), Jinja2 no la reconoce. Solución: borrar y
reescribir la variable de un solo golpe sin pausas ni ediciones intermedias.

## Patron de nombre de archivo

Usa los nombres de columna normalizados entre llaves simples:

```
{NOMBRE}_{CEDULA_NIT}
{EXPEDIENTE_DE_COBRO}_{NOMBRE}
registro_{row_index}        ← siempre disponible, no requiere columnas
```

## Comandos operativos

**Linux/macOS (`make`):**
```bash
make up           # Levantar todos los servicios (con rebuild)
make down         # Bajar todos los servicios
make logs         # Ver logs en tiempo real
make ps           # Estado de los contenedores
make migrate      # Aplicar migraciones Alembic manualmente
make test-api     # Correr tests de la API
make release VERSION=x.y.z
```

**Windows PowerShell:**
```powershell
.\ops.ps1 up
.\ops.ps1 down
.\ops.ps1 logs
.\ops.ps1 ps
.\ops.ps1 migrate
.\ops.ps1 test-api
.\ops.ps1 release -Version x.y.z
```

## Arquitectura técnica

```
UI (Streamlit)
  └─► POST /batches          → crea lote, guarda Excel + DOCX en storage/
  └─► POST /batches/{id}/run → valida columnas del patron, encola tarea Celery
  └─► GET  /batches/{id}     → polling de progreso (status, total, ok, error)
  └─► GET  /batches/{id}/download → descarga salida.zip

Worker (Celery)
  1. Lee Excel con pandas → normaliza columnas
  2. Por cada fila: renderiza DOCX con docxtpl (Jinja2)
  3. Convierte DOCX→PDF con LibreOffice headless (2 intentos)
  4. Empaqueta todos los PDFs en salida.zip
  5. Actualiza estado en PostgreSQL
```

## Despliegue

**Otra máquina Windows/Mac/Linux:**
- Instalar Docker Desktop, copiar el proyecto, `docker compose up --build`.

**Servidor / nube:**
- VPS con Docker (DigitalOcean, Vultr, etc.) — exponer puerto 8501.
- Railway.app o Render.com — soportan docker-compose directamente.

> El worker instala LibreOffice (~400MB), el primer build tarda varios minutos.
> La primera conversión DOCX→PDF tarda 15-30s (cold start de LibreOffice).

## Hardening incluido

- Rate limiting configurable por IP (`RATE_LIMIT_*`).
- Validacion de `Host` por lista permitida (`TRUSTED_HOSTS`).
- Cabeceras de seguridad HTTP en todas las respuestas API.
- CORS estricto por ambiente (`ENVIRONMENT=prod` rechaza `*`).

## Notas de produccion

- Storage local (`/data/storage`) → migrar a S3 / Azure Blob para escalar.
- Agregar autenticacion JWT en la API.
- Ver checklist completo en `RELEASE_CHECKLIST.md`.
- Version actual en `VERSION`; historial en `CHANGELOG.md`.
