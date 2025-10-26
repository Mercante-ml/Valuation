"""
Django settings for valuation project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GAMMA_API_KEY = os.environ.get('GAMMA_API_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost 127.0.0.1').split(' ')
CSRF_TRUSTED_ORIGINS = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(' ')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', # Necessário para estáticos
    'django.contrib.humanize',
    'users',
    'chatbot',
    'reports',
    'crispy_forms',
    'crispy_bootstrap5',
    # 'whitenoise.runserver_nostatic', # CERTIFIQUE-SE QUE ESTÁ REMOVIDO/COMENTADO
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
   "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'valuation.urls' # Verifique nome da pasta

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'valuation.wsgi.application' # Verifique nome da pasta

DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600) if DATABASE_URL else {} # Adicionado 'if' para segurança local
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Configuração de Ficheiros Estáticos (Final Recomendada) ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_build' # Onde collectstatic coloca os ficheiros


# Vamos tornar o caminho explícito e imprimir para debug
static_dirs_path = os.path.join(BASE_DIR, 'static')
print(f"DEBUG: BASE_DIR is: {BASE_DIR}")
print(f"DEBUG: STATICFILES_DIRS calculated path is: {static_dirs_path}")
STATICFILES_DIRS = [ static_dirs_path, ]

# Usar o storage mais simples do Whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

# WHITENOISE_ROOT e WHITENOISE_STATIC_PREFIX devem estar REMOVIDOS ou COMENTADOS
# WHITENOISE_ROOT = STATIC_ROOT
# WHITENOISE_STATIC_PREFIX = '/static/'
# --- Fim da Configuração de Estáticos ---


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'chatbot:dashboard'
LOGOUT_REDIRECT_URL = 'index'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
SERVER_EMAIL = DEFAULT_FROM_EMAIL
ADMINS = [('contato', 'contato@dsprime.net')] # Ajuste conforme necessário