#!/bin/bash
# Скрипт развертывания Print Advisor с Nginx reverse proxy
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Развертывание Print Advisor с Nginx Reverse Proxy ===${NC}"
echo ""

# Проверка .env файла
if [ ! -f .env ]; then
    echo -e "${RED}❌ Ошибка: файл .env не найден!${NC}"
    echo -e "${YELLOW}Выполните: ./scripts/generate_env.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Файл .env найден${NC}"

# Проверка каталогов
if [ ! -d "data/watch" ] || [ ! -d "data/processed" ] || [ ! -d "data/quarantine" ]; then
    echo -e "${YELLOW}⚠️  Каталоги data/ не найдены, создаю...${NC}"
    mkdir -p data/{watch,processed,quarantine}
    chmod 777 data/{watch,processed,quarantine}
fi
echo -e "${GREEN}✅ Каталоги data/ готовы${NC}"

# Шаг 1: Создание сети для reverse proxy
echo ""
echo -e "${BLUE}Шаг 1: Создание сети reverse-proxy-network...${NC}"
if docker network inspect reverse-proxy-network >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Сеть reverse-proxy-network уже существует${NC}"
else
    docker network create reverse-proxy-network
    echo -e "${GREEN}✅ Сеть создана${NC}"
fi

# Шаг 2: Запуск Nginx reverse proxy
echo ""
echo -e "${BLUE}Шаг 2: Запуск Nginx reverse proxy...${NC}"
docker compose -f docker-compose.proxy.yml up -d
echo -e "${GREEN}✅ Nginx запущен${NC}"

# Шаг 3: Сборка и запуск основного приложения
echo ""
echo -e "${BLUE}Шаг 3: Сборка и запуск основного приложения...${NC}"
docker compose build
docker compose up -d
echo -e "${GREEN}✅ Приложение запущено${NC}"

# Ожидание готовности сервисов
echo ""
echo -e "${YELLOW}⏳ Ожидание готовности сервисов (30 секунд)...${NC}"
sleep 30

# Шаг 4: Проверка статуса
echo ""
echo -e "${BLUE}Шаг 4: Проверка статуса сервисов...${NC}"
echo ""
echo -e "${YELLOW}=== Статус Nginx ===${NC}"
docker compose -f docker-compose.proxy.yml ps
echo ""
echo -e "${YELLOW}=== Статус основного приложения ===${NC}"
docker compose ps

# Шаг 5: Выполнение миграций
echo ""
echo -e "${BLUE}Шаг 5: Выполнение миграций БД...${NC}"
docker compose exec web python manage.py migrate --noinput
echo -e "${GREEN}✅ Миграции выполнены${NC}"

# Шаг 6: Проверка health checks
echo ""
echo -e "${BLUE}Шаг 6: Проверка health checks...${NC}"
echo -e "${YELLOW}Проверка Nginx health check...${NC}"
if curl -f -s http://localhost/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Nginx health check: OK${NC}"
else
    echo -e "${RED}❌ Nginx health check: FAILED${NC}"
fi

echo -e "${YELLOW}Проверка Django health check...${NC}"
if curl -f -s http://localhost/health/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Django health check: OK${NC}"
else
    echo -e "${YELLOW}⚠️  Django health check: проверьте логи${NC}"
fi

# Итоговая информация
echo ""
echo -e "${GREEN}=== Развертывание завершено! ===${NC}"
echo ""
echo -e "${BLUE}Доступ к приложению:${NC}"
echo -e "  - Через Nginx: ${GREEN}http://localhost/${NC}"
echo -e "  - Прямой доступ (если порт открыт): ${GREEN}http://localhost:8000/${NC}"
echo ""
echo -e "${BLUE}Полезные команды:${NC}"
echo -e "  - Логи Nginx: ${YELLOW}docker compose -f docker-compose.proxy.yml logs -f nginx${NC}"
echo -e "  - Логи приложения: ${YELLOW}docker compose logs -f web${NC}"
echo -e "  - Логи watcher: ${YELLOW}docker compose logs -f watcher${NC}"
echo -e "  - Статус всех сервисов: ${YELLOW}docker compose ps && docker compose -f docker-compose.proxy.yml ps${NC}"
echo ""
echo -e "${YELLOW}⚠️  Не забудьте создать суперпользователя:${NC}"
echo -e "  ${BLUE}docker compose exec web python manage.py createsuperuser${NC}"
echo ""
