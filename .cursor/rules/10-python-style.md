# Python Style & Conventions (Django 5.2 / Python 3.13)

## Language Level
- Python **3.13**. Разрешено pattern matching, `typing` (PEP 484/695), `|` для union.

## Code Style
- **PEP 8** + автоформат: `black` (120 cols), линт: `ruff`.
- Имена: `snake_case` (функции/переменные), `PascalCase` (классы), константы `UPPER_SNAKE_CASE`.
- Импорты: stdlib → third-party → local; никаких `from x import *`.

## Typing
- Везде **type hints**, `mypy --strict`. Избегать `Any`, иначе — явный escape-комментарий.
- Для структур данных: `dataclasses` либо `TypedDict`. Pydantic — только при явной нужде.

## Errors & Logging
- Поднимать **специфичные** исключения; не глотать `Exception`.
- Логирование через `logging` (конфиг из `config/logging.py`). Никаких `print()` в библиотечном коде.

## Django API Contracts
- Функции ≤ 30 строк, SRP.
- Публичные view/service/serializer — docstring (NumPy/Google style) + пример использования.

## IO & Env
- Никакого IO на уровне импорта модулей. Конфиг читаем через ENV в `settings`.
