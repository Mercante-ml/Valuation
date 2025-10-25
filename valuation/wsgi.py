"""
WSGI config for valuation project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
# --- ADICIONE ESTA IMPORTAÇÃO ---
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valuation.settings') # Verifique se 'valuation.settings' está correto

# Pega a aplicação Django padrão
application = get_wsgi_application()

# --- ENVOLVE A APLICAÇÃO COM WHITENOISE ---
# Isto permite ao Whitenoise servir ficheiros diretamente do STATIC_ROOT
# Se STATICFILES_STORAGE foi removido/comentado em settings.py
application = WhiteNoise(application)
# Se você quiser manter STATICFILES_STORAGE='whitenoise.storage.CompressedManifestStaticFilesStorage',
# pode usar: application = WhiteNoise(application, root=settings.STATIC_ROOT)
# Mas vamos tentar sem o STATICFILES_STORAGE primeiro.