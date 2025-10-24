# apps/chatbot/urls.py
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Página do dashboard/chatbot
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Endpoint da API para calcular
    path('api/calculate/', views.calculate_valuation_view, name='api_calculate'),
]