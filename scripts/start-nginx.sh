#!/bin/bash
# Скрипт запуска Nginx reverse proxy
# Использование: ./scripts/start-nginx.sh

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Запуск Nginx Reverse Proxy ===${NC}"
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Ошибка: Docker не установлен${NC}"
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

# Шаг 1: Проверка сети
echo -e "${GREEN}[1/3] Проверка сети reverse-proxy-network...${NC}"
if $DOCKER_CMD network inspect reverse-proxy-network &> /dev/null; then
    echo -e "${GREEN}Сеть существует${NC}"
else
    echo -e "${YELLOW}Создание сети reverse-proxy-network...${NC}"
    $DOCKER_CMD network create reverse-proxy-network
    echo -e "${GREEN}Сеть создана${NC}"
fi

# Шаг 2: Проверка основного стека
echo -e "${GREEN}[2/3] Проверка основного стека приложения...${NC}"
if $DOCKER_CMD ps --format "{{.Names}}" | grep -q "advisor-web"; then
    echo -e "${GREEN}Контейнер advisor-web запущен${NC}"
    
    # Проверка подключения к сети
    if $DOCKER_CMD inspect advisor-web --format '{{range $net, $v := .NetworkSettings.Networks}}{{$net}} {{end}}' | grep -q "reverse-proxy-network"; then
        echo -e "${GREEN}Контейнер подключен к сети reverse-proxy-network${NC}"
    else
        echo -e "${YELLOW}Контейнер не подключен к сети reverse-proxy-network${NC}"
        echo -e "${YELLOW}Перезапустите основной стек: docker compose up -d${NC}"
    fi
else
    echo -e "${RED}Ошибка: контейнер advisor-web не запущен${NC}"
    echo -e "${YELLOW}Запустите основной стек: docker compose up -d${NC}"
    exit 1
fi

# Шаг 3: Запуск Nginx
echo -e "${GREEN}[3/3] Запуск Nginx...${NC}"
$DOCKER_COMPOSE -f docker-compose.proxy.yml up -d

# Ожидание готовности
echo -e "${YELLOW}Ожидание готовности Nginx...${NC}"
sleep 5

# Проверка статуса
if $DOCKER_CMD ps --format "{{.Names}}" | grep -q "reverse-proxy-nginx"; then
    echo ""
    echo -e "${GREEN}✅ Nginx запущен!${NC}"
    echo ""
    echo -e "${BLUE}Проверка доступности:${NC}"
    echo "  curl http://localhost/health"
    echo "  curl http://localhost/health/"
    echo ""
    echo -e "${BLUE}Приложение доступно по адресу:${NC}"
    echo "  http://localhost/"
    echo ""
    echo -e "${YELLOW}Для просмотра логов:${NC}"
    echo "  $DOCKER_COMPOSE -f docker-compose.proxy.yml logs -f nginx"
else
    echo -e "${RED}Ошибка: Nginx не запустился${NC}"
    echo -e "${YELLOW}Проверьте логи:${NC}"
    echo "  $DOCKER_COMPOSE -f docker-compose.proxy.yml logs nginx"
    exit 1
fi

