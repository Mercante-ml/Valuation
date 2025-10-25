# valuation/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

# Certifique-se que o nome 'valuation.settings' está correto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valuation.settings')

application = get_wsgi_application()
# NENHUMA linha do WhiteNoise aqui