# valuation/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings # <-- ADICIONE ISTO
from django.conf.urls.static import static # <-- ADICIONE ISTO

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('accounts/', include('users.urls', namespace='users')),
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),
    path('reports/', include('reports.urls', namespace='reports')),
]

# --- ADICIONE ESTE BLOCO APENAS PARA DIAGNÓSTICO ---
# AVISO: Não use isto num ambiente de produção real com DEBUG=False
#          Isto é apenas para testar se o Django consegue encontrar os ficheiros.
if settings.DEBUG is False: # Aplica apenas se DEBUG for False (como no Render)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# --- FIM DO BLOCO DE DIAGNÓSTICO ---