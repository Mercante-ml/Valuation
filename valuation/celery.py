# valuation/celery.py
import os
from celery import Celery
from django.conf import settings

# Define o módulo de settings do Django para o 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valuation.settings')

app = Celery('valuation')

# Lê a configuração do Celery a partir do settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover: Procura por tarefas em arquivos 'tasks.py' em cada app
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)