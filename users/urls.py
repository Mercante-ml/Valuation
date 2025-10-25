# users/urls.py
from django.urls import path, reverse_lazy # Garante que reverse_lazy está importado
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # --- Cadastro e Ativação ---
    path('register/', views.RegisterView.as_view(), name='register'),
    path('registration-confirm-email/', views.RegistrationConfirmEmailView.as_view(), name='registration_confirm_email'),
    path('confirm/<uidb64>/<token>/', views.activate, name='activate'), # Rota para o link do email

    # --- Login / Logout ---
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- Recuperação de Senha (Esqueci Senha) ---
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

    # --- Configurações do Usuário Logado ---
    path('settings/', views.profile_settings_view, name='settings'), # Página principal de config

    # --- Troca de Senha (Usuário Logado) ---
    path(
        'password_change/',
        auth_views.PasswordChangeView.as_view(
            template_name='users/password_change_form.html', # Template correto
            success_url=reverse_lazy('users:password_change_done') # URL de sucesso correta
        ),
        name='password_change'
    ),
    path(
        'password_change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html' # Template correto
        ),
        name='password_change_done'
    ),
]