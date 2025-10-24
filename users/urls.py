# apps/users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users' # Namespace

urlpatterns = [
    # Cadastro
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Login / Logout
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'), # Usa a view padrão

    # --- Recuperação de Senha ---
    path('password_reset/', 
         views.CustomPasswordResetView.as_view(), 
         name='password_reset'),
    
    path('password_reset/done/', 
         views.CustomPasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
         
    path('reset/done/', 
         views.CustomPasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
]