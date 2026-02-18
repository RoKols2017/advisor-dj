"""
Health check endpoint for Docker and load balancers.
"""
import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint that verifies:
    - Database connectivity
    - Cache connectivity
    - Basic application health
    """
    health_status = {
        'status': 'healthy',
        'checks': {
            'database': 'ok',
            'cache': 'ok',
            'application': 'ok'
        }
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status['checks']['database'] = 'error'
        health_status['status'] = 'unhealthy'
    
    # Check cache connectivity
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') != 'ok':
            raise Exception("Cache read/write failed")
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status['checks']['cache'] = 'error'
        health_status['status'] = 'unhealthy'
    
    # Return appropriate HTTP status
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)
