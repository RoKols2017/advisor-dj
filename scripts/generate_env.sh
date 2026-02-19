#!/bin/bash
# Генератор .env файла для Print Advisor
# Использование: ./scripts/generate_env.sh [OPTIONS]
#
# Опции:
#   --output FILE      Файл для сохранения .env (по умолчанию: .env)
#   --allowed-hosts    Разрешенные хосты (по умолчанию: auto-detect)
#   --interactive      Интерактивный режим с запросами
#   --production       Сгенерировать production env (.env.prod по умолчанию)
#   --help             Показать эту справку

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

OUTPUT_FILE=".env"
ALLOWED_HOSTS=""
INTERACTIVE=false
PRODUCTION=false

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --allowed-hosts)
            ALLOWED_HOSTS="$2"
            shift 2
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        --production)
            PRODUCTION=true
            shift
            ;;
        --help)
            echo "Генератор .env файла для Print Advisor"
            echo ""
            echo "Использование: $0 [OPTIONS]"
            echo ""
            echo "Опции:"
            echo "  --output FILE      Файл для сохранения .env (по умолчанию: .env)"
            echo "  --allowed-hosts    Разрешенные хосты через запятую (по умолчанию: auto-detect)"
            echo "  --interactive      Интерактивный режим с запросами"
            echo "  --production       Сгенерировать production env (.env.prod по умолчанию)"
            echo "  --help             Показать эту справку"
            exit 0
            ;;
        *)
            echo -e "${RED}Ошибка: неизвестный аргумент $1${NC}"
            echo "Используйте --help для справки"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=== Генератор .env файла для Print Advisor ===${NC}"
echo ""

if [[ "$PRODUCTION" == true && "$OUTPUT_FILE" == ".env" ]]; then
    OUTPUT_FILE=".env.prod"
fi

# Проверка существования файла
if [[ -f "$OUTPUT_FILE" ]]; then
    if [[ "$INTERACTIVE" == true ]]; then
        echo -e "${YELLOW}Файл $OUTPUT_FILE уже существует.${NC}"
        read -p "Перезаписать? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Отменено."
            exit 0
        fi
    else
        echo -e "${YELLOW}Предупреждение: файл $OUTPUT_FILE уже существует и будет перезаписан${NC}"
    fi
fi

# Генерация SECRET_KEY через Python
echo -e "${GREEN}Генерация SECRET_KEY...${NC}"
if command -v python3 &> /dev/null; then
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || \
                 python3 -c "import secrets; print(secrets.token_urlsafe(50))")
elif command -v python &> /dev/null; then
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || \
                 python -c "import secrets; print(secrets.token_urlsafe(50))")
else
    # Fallback: используем openssl
    SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n' | head -c 80)
fi

# Генерация POSTGRES_PASSWORD (64 символа, безопасные символы)
echo -e "${GREEN}Генерация POSTGRES_PASSWORD...${NC}"
POSTGRES_PASSWORD=$(openssl rand -base64 48 | tr -d '\n' | head -c 64)

# Генерация IMPORT_TOKEN
echo -e "${GREEN}Генерация IMPORT_TOKEN...${NC}"
IMPORT_TOKEN=$(openssl rand -hex 32)

# Определение ALLOWED_HOSTS
if [[ -z "$ALLOWED_HOSTS" ]]; then
    if [[ "$INTERACTIVE" == true ]]; then
        echo -e "${BLUE}Введите разрешенные хосты через запятую (например: 192.168.1.100,localhost,127.0.0.1):${NC}"
        read -p "ALLOWED_HOSTS: " ALLOWED_HOSTS
    else
        # Автоопределение IP адресов
        echo -e "${GREEN}Автоопределение ALLOWED_HOSTS...${NC}"
        HOST_IPS=$(hostname -I 2>/dev/null | tr ' ' ',' || echo "")
        if [[ -n "$HOST_IPS" ]]; then
            ALLOWED_HOSTS="${HOST_IPS}localhost,127.0.0.1"
        else
            # Попытка через ip
            HOST_IPS=$(ip addr show 2>/dev/null | grep -oP 'inet \K[\d.]+' | grep -v '127.0.0.1' | head -1 || echo "")
            if [[ -n "$HOST_IPS" ]]; then
                ALLOWED_HOSTS="${HOST_IPS},localhost,127.0.0.1"
            else
                ALLOWED_HOSTS="localhost,127.0.0.1"
                echo -e "${YELLOW}Не удалось определить IP адреса, используем только localhost${NC}"
            fi
        fi
    fi
fi

# Запрос остальных параметров в интерактивном режиме
if [[ "$INTERACTIVE" == true ]]; then
    read -p "POSTGRES_DB [advisor]: " POSTGRES_DB_INPUT
    POSTGRES_DB=${POSTGRES_DB_INPUT:-advisor}
    
    read -p "POSTGRES_USER [advisor]: " POSTGRES_USER_INPUT
    POSTGRES_USER=${POSTGRES_USER_INPUT:-advisor}
    
    read -p "WEB_PORT [8001]: " WEB_PORT_INPUT
    WEB_PORT=${WEB_PORT_INPUT:-8001}
    
    read -p "POSTGRES_PORT [5432]: " POSTGRES_PORT_INPUT
    POSTGRES_PORT=${POSTGRES_PORT_INPUT:-5432}
else
    POSTGRES_DB="advisor"
    POSTGRES_USER="advisor"
    WEB_PORT="8000"
    POSTGRES_PORT="5432"
fi

if [[ "$PRODUCTION" == true ]]; then
    DJANGO_SETTINGS_MODULE_VALUE="config.settings.production"
else
    DJANGO_SETTINGS_MODULE_VALUE="config.settings.docker"
fi

# Создание .env файла
cat > "$OUTPUT_FILE" << EOF
# Print Advisor - Environment Variables
# Сгенерировано: $(date '+%Y-%m-%d %H:%M:%S')
# ВНИМАНИЕ: Не коммитьте этот файл в git! Он содержит секретные ключи.

# === База данных ===
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_PORT=${POSTGRES_PORT}

# === Django ===
DEBUG=0
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=${ALLOWED_HOSTS}
DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE_VALUE}

# === Логи ===
LOG_TO_FILE=1
LOG_TO_CONSOLE=0
LOG_DIR=/app/logs
LOG_FILE_NAME=project.log
WATCHER_LOG_FILE_NAME=print_events_watcher.log

# === Watcher / Импорт ===
PRINT_EVENTS_WATCH_DIR=/app/data/watch
PRINT_EVENTS_PROCESSED_DIR=/app/data/processed
PRINT_EVENTS_QUARANTINE_DIR=/app/data/quarantine
IMPORT_TOKEN=${IMPORT_TOKEN}
ENABLE_WINDOWS_AUTH=0

# === Watcher настройки (опционально) ===
# WATCHER_MAX_RETRIES=5
# WATCHER_BACKOFF_BASE=2
# WATCHER_BACKOFF_MAX=30
# WATCHER_DEADLINE_SECONDS=300

# === Порты ===
WEB_PORT=${WEB_PORT}

# === Безопасность (для production, раскомментируйте при необходимости) ===
# CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
# SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
EOF

echo ""
echo -e "${GREEN}✅ Файл $OUTPUT_FILE успешно создан!${NC}"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО:${NC}"
echo -e "  - Проверьте значение ALLOWED_HOSTS (сейчас: ${ALLOWED_HOSTS})"
echo -e "  - Не коммитьте этот файл в git!"
echo -e "  - Сохраните пароли и ключи в безопасном месте"
echo ""
echo -e "${BLUE}Сгенерированные значения:${NC}"
echo -e "  SECRET_KEY: ${SECRET_KEY:0:20}... (${#SECRET_KEY} символов)"
echo -e "  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:0:10}... (${#POSTGRES_PASSWORD} символов)"
echo -e "  IMPORT_TOKEN: ${IMPORT_TOKEN:0:10}... (${#IMPORT_TOKEN} символов)"
echo ""


