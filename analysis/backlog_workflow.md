# Backlog workflow para subagents

Guia breve para sesiones futuras. Usar siempre `./scripts/backlog.sh` para leer o actualizar tareas.

## Inicio de una sesion

1. Leer la tarea:

```bash
./scripts/backlog.sh task <id> --plain
```

2. Ponerla `In Progress` y asignarla:

```bash
./scripts/backlog.sh task edit <id> -s "In Progress" -a @codex-orchestrator
```

3. Registrar el plan antes de tocar codigo o docs:

```bash
./scripts/backlog.sh task edit <id> --plan "1. Revisar contexto\n2. Implementar\n3. Verificar\n4. Cerrar"
```

## Convencion de modelo

- `model-small`: tarea corta, cambio puntual, una sola sesion.
- `model-medium`: tarea con varias partes, requiere lectura y verificacion extra.
- `model-large`: tarea amplia o con riesgo alto, dividir antes de ejecutar.

Para esta repo, el default recomendado es `model-small` salvo que la tarea pida mas alcance.

## Regla de alcance

- Un subagent o una sesion trabaja una sola tarea atomica.
- No mezclar tareas distintas en la misma sesion.
- Si aparece trabajo adicional, dejarlo como nota o crear una nueva tarea.

## Cierre

Cuando el trabajo esta listo:

```bash
./scripts/backlog.sh task edit <id> --append-notes "Trabajo completado"
./scripts/backlog.sh task edit <id> --check-ac 1 --check-ac 2 --check-ac 3
./scripts/backlog.sh task edit <id> --final-summary "Resumen breve del cambio"
./scripts/backlog.sh task edit <id> -s Done
```

Checklist rapida:

- ACs marcados.
- Resumen final escrito.
- Estado final en `Done`.
- No editar `backlog/tasks/*.md` a mano.
