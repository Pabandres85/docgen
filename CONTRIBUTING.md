# Contributing

## Convencion de commits
Se recomienda usar Conventional Commits:
- `feat:` nueva funcionalidad.
- `fix:` correccion de bug.
- `chore:` tareas de mantenimiento.
- `docs:` cambios de documentacion.
- `refactor:` cambios internos sin variar comportamiento.
- `test:` pruebas.

Ejemplo:
`feat(api): agregar endpoint /ready`

## Versionado
- Se usa SemVer (`MAJOR.MINOR.PATCH`).
- La version actual vive en `VERSION`.
- Cada release debe registrar cambios en `CHANGELOG.md`.

## Flujo recomendado
1. Crear rama.
2. Implementar cambios + pruebas.
3. Actualizar documentacion si aplica.
4. Abrir PR con contexto tecnico y riesgo.
