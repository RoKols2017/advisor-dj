#!/bin/bash
# Скрипт для проверки статуса импорта файлов

echo "=== СТАТУС ИМПОРТА ФАЙЛОВ ==="
echo ""

echo "📁 Файлы в каталоге watch (ожидают обработки):"
ls -lh data/watch/ 2>/dev/null | tail -n +2 | wc -l | xargs -I {} echo "   Файлов: {}"
ls -lh data/watch/ 2>/dev/null | tail -n +2 | head -5

echo ""
echo "✅ Обработанные файлы:"
ls -lh data/processed/ 2>/dev/null | tail -n +2 | wc -l | xargs -I {} echo "   Файлов: {}"
ls -lh data/processed/ 2>/dev/null | tail -n +2 | head -5

echo ""
echo "❌ Файлы в карантине (ошибки):"
ls -lh data/quarantine/ 2>/dev/null | tail -n +2 | wc -l | xargs -I {} echo "   Файлов: {}"
ls -lh data/quarantine/ 2>/dev/null | tail -n +2 | head -5

echo ""
echo "📊 Статистика в базе данных:"
docker compose exec -T web python manage.py shell << 'PYTHON'
from printing.models import PrintEvent
from accounts.models import User
from django.utils import timezone
from datetime import timedelta

total = PrintEvent.objects.count()
print(f"   Всего событий печати: {total}")

if total > 0:
    last_24h = PrintEvent.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).count()
    print(f"   За последние 24 часа: {last_24h}")
    
    latest = PrintEvent.objects.order_by('-timestamp').first()
    if latest:
        print(f"   Последнее событие: {latest.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

users_count = User.objects.count()
print(f"   Всего пользователей: {users_count}")
PYTHON

echo ""
echo "📋 Последние логи watcher:"
docker compose logs watcher --tail=10 | grep -E "(Найден|обработан|error|ERROR|успешно)" | tail -5 || echo "   Нет недавних событий"


