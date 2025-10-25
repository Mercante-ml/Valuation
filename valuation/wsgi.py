"""
WSGI config for valuation project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application
# --- ADICIONE ESTAS IMPORTAÇÕES ---
from whitenoise import WhiteNoise
from django.conf import settings # Para aceder a STATIC_ROOT

# Certifique-se que o nome 'valuation.settings' está correto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valuation.settings')

# Pega a aplicação Django padrão
application = get_wsgi_application()

# --- ENVOLVE A APLICAÇÃO COM WHITENOISE, ESPECIFICANDO O ROOT ---
# Isto diz explicitamente ao Whitenoise onde procurar os ficheiros
# que foram coletados pelo collectstatic.
#application = WhiteNoise(_application, root=settings.STATIC_ROOT)