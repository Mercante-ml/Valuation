# apps/users/urls.py
from django.urls import path, reverse_lazy # <--- ADICIONE reverse_lazy AQUI
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
    
    # --- NOVAS ROTAS ---
    
    # 1. Página de Configurações (Editar Perfil)
    path('settings/', views.profile_settings_view, name='settings'),
    
    # 2. Fluxo de Troca de Senha (para usuários LOGADOS)
    path(
        'password_change/', 
        auth_views.PasswordChangeView.as_view(
            template_name='users/password_change_form.html', # Template que vamos criar
            success_url=reverse_lazy('users:password_change_done')
        ), 
        name='password_change'
    ),
    path(
        'password_change/done/', 
        auth_views.PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html' # Template que vamos criar
        ), 
        name='password_change_done'
    ),
]

