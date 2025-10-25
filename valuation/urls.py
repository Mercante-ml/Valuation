# valuation/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
# REMOVA as importações de 'settings' e 'static' se não forem mais usadas

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('accounts/', include('users.urls', namespace='users')),
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),
    path('reports/', include('reports.urls', namespace='reports')),
]

