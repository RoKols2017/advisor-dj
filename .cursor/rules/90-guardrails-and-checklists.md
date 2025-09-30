# Guardrails & Checklists (DoD)

## Before you code
- Прочти `@README.md`, `@DEVELOPER.md`, `@PROJECT_PLAN.md`, `@REFACTORING_PLAN.md`, `.env.example`.
- Зафиксируй требования/входы/выходы. Опиши инварианты.

## While coding
- Малые коммиты (повелительное наклонение).
- Без скрытых глобальных состояний. Никакой магии в импортах.

## Before you submit
- [ ] ruff/black/mypy/pytest — зелёные
- [ ] Docstrings и примеры на публичные функции/вью/команды
- [ ] meaningful логи/ошибки, без секретов
- [ ] Тесты добавлены/обновлены
- [ ] `CHANGELOG.md`/`docs` обновлены при изменении контрактов
