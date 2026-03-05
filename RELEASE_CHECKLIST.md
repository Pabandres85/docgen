# Release Checklist

## 1. Validaciones previas
- Confirmar que `.env` de despliegue no usa secretos por defecto.
- Verificar `ENVIRONMENT=prod`.
- Verificar `CORS_ORIGINS` y `TRUSTED_HOSTS` con valores de produccion.
- Verificar `RATE_LIMIT_*` acorde al trafico esperado.

## 2. Build y arranque
- Ejecutar `docker compose build`.
- Ejecutar `docker compose up -d`.
- Confirmar servicios saludables (`docker compose ps`).

## 3. Migraciones y esquema
- Ejecutar migraciones: `docker compose exec api sh -c "cd /app/apps/api && alembic -c alembic.ini upgrade head"`.
- Validar que API responde `/ready` en estado `ready`.

## 4. Pruebas basicas
- Ejecutar tests API: `docker compose run --rm api sh -c "cd /app/apps/api && pip install --no-cache-dir -r requirements-dev.txt && pytest -q"`.
- Smoke test: crear lote pequeno y verificar descarga de `salida.zip`.

## 5. Verificaciones operativas
- Revisar logs de `api` y `worker` por errores.
- Confirmar que se registran `batch_started` y `batch_finished`.
- Confirmar que no hay lotes en estado `FAILED` inesperado.

## 6. Cierre
- Generar release notes y actualizar version:
  - Linux/macOS: `make release VERSION=x.y.z`
  - Windows: `.\ops.ps1 release -Version x.y.z`
- Revisar `CHANGELOG.md` y `VERSION`.
- Documentar version liberada y fecha.
- Registrar cambios de configuracion aplicados.
