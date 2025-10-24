# reports/urls.py
from django.urls import path
from . import views


app_name = 'reports' # Define o namespace

urlpatterns = [
    # 1. Página de Lista (Histórico)
    # Ex: /reports/history/
    path('history/', views.report_history_view, name='report_history'),
    
    # 2. Página de Detalhe (para cada relatório individual)
    # Ex: /reports/detail/5/ (onde 5 é o ID do relatório)
    path('detail/<int:pk>/', views.report_detail_view, name='report_detail'),
]