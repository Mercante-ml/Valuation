"""
WSGI config for valuation project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application

# Certifique-se que o nome 'valuation.settings' está correto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valuation.settings')

application = get_wsgi_application()
# Linha removida: application = WhiteNoise(application)