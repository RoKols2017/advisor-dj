#!/bin/bash
# Скрипт установки Print Advisor в Docker
# Использование: ./scripts/setup.sh

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Установка Print Advisor в Docker ===${NC}"
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Ошибка: Docker не установлен${NC}"
    exit 1
fi

# Проверка docker compose
if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
    echo -e "${RED}Ошибка: docker compose не установлен${NC}"
    exit 1
fi

# Определение команды docker compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Проверка прав доступа
USE_SUDO=false
if ! docker ps &> /dev/null; then
    echo -e "${YELLOW}Нет доступа к Docker, будет использоваться sudo${NC}"
    USE_SUDO=true
    DOCKER_COMPOSE="sudo $DOCKER_COMPOSE"
    DOCKER_CMD="sudo docker"
else
    DOCKER_CMD="docker"
fi

# Шаг 1: Проверка .env файла
echo -e "${GREEN}[1/7] Проверка .env файла...${NC}"
if [[ ! -f .env ]]; then
    echo -e "${YELLOW}.env файл не найден, генерирую...${NC}"
    if [[ -f scripts/generate_env.sh ]]; then
        chmod +x scripts/generate_env.sh
        ./scripts/generate_env.sh
    else
        echo -e "${RED}Ошибка: скрипт generate_env.sh не найден${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}.env файл уже существует${NC}"
fi

# Шаг 2: Создание каталогов
echo -e "${GREEN}[2/7] Создание каталогов...${NC}"
mkdir -p data/{watch,processed,quarantine}
echo -e "${GREEN}Каталоги созданы${NC}"

# Шаг 3: Создание сети для Nginx
echo -e "${GREEN}[3/7] Создание сети reverse-proxy-network...${NC}"
if $DOCKER_CMD network inspect reverse-proxy-network &> /dev/null; then
    echo -e "${GREEN}Сеть уже существует${NC}"
else
    $DOCKER_CMD network create reverse-proxy-network || echo -e "${YELLOW}Не удалось создать сеть (возможно, уже существует)${NC}"
fi

# Шаг 4: Сборка образов
echo -e "${GREEN}[4/7] Сборка Docker образов...${NC}"
echo -e "${YELLOW}Это может занять несколько минут...${NC}"
$DOCKER_COMPOSE build

# Шаг 5: Запуск контейнеров
echo -e "${GREEN}[5/7] Запуск контейнеров...${NC}"
$DOCKER_COMPOSE up -d

# Ожидание готовности сервисов
echo -e "${YELLOW}Ожидание готовности сервисов...${NC}"
sleep 10

# Шаг 6: Миграции
echo -e "${GREEN}[6/7] Выполнение миграций базы данных...${NC}"
$DOCKER_COMPOSE exec -T web python manage.py migrate --noinput

# Шаг 7: Сборка статических файлов
echo -e "${GREEN}[7/7] Сборка статических файлов...${NC}"
$DOCKER_COMPOSE exec -T web python manage.py collectstatic --noinput

echo ""
echo -e "${GREEN}✅ Установка завершена!${NC}"
echo ""
echo -e "${BLUE}Следующие шаги:${NC}"
echo "  1. Проверьте статус: $DOCKER_COMPOSE ps"
echo "  2. Проверьте health: curl http://localhost:8001/health/"
echo "  3. Создайте суперпользователя: $DOCKER_COMPOSE exec web python manage.py createsuperuser"
echo "  4. Откройте в браузере: http://localhost:8001"
echo ""
echo -e "${YELLOW}Для просмотра логов используйте:${NC}"
echo "  $DOCKER_COMPOSE logs -f web"
echo "  $DOCKER_COMPOSE logs -f watcher"
echo ""

