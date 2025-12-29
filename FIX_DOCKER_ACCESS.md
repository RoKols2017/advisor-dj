# Исправление доступа к Docker

## Проблема
Пользователь добавлен в группу `docker`, но текущая сессия не видит эту группу.

## Решение

### Вариант 1: Применить группу в текущей сессии (быстро)

Выполните в терминале:

```bash
newgrp docker
```

После этого проверьте:
```bash
docker ps
```

Если работает, выполните команды для запуска Nginx.

### Вариант 2: Использовать sg (без новой сессии)

```bash
sg docker -c "docker ps"
```

### Вариант 3: Перелогиниться (надежно)

Выйдите из системы и войдите снова, или выполните:
```bash
su - $USER
```

## После исправления доступа

Запустите Nginx:

```bash
# Проверка сети
docker network create reverse-proxy-network 2>/dev/null || true

# Проверка основного стека
docker compose ps

# Запуск Nginx
docker compose -f docker-compose.proxy.yml up -d

# Проверка
docker compose -f docker-compose.proxy.yml ps
curl http://localhost/health
```

## Проверка

Убедитесь, что группа docker активна:
```bash
groups
# Должна быть группа "docker" в списке

id
# Должна быть группа docker в выводе
```

