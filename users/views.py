# users/views.py
from django.urls import reverse_lazy, reverse
from django.views.generic.edit import CreateView
from django.contrib.auth import views as auth_views, login
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

# Importações para envio de email e tokens
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.http import HttpResponse, HttpResponseRedirect # Adicionado HttpResponseRedirect
from django.conf import settings # Adicionado settings
import logging # Adicionado logging

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    UserProfileUpdateForm
)
from .models import CustomUser
from .tokens import account_activation_token

# Configura o logger
logger = logging.getLogger(__name__)

# --- FUNÇÃO PARA ENVIAR EMAIL DE ATIVAÇÃO ---
def send_activation_email(request, user):
    current_site = get_current_site(request)
    subject = render_to_string('users/account_activation_subject.txt', {'user': user}).strip()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)

    context = {
        'user': user,
        # Determina o protocolo (http ou https)
        'protocol': 'https' if request.is_secure() else 'http',
        # Pega o domínio do site atual (ex: localhost:8000 ou seu domínio .onrender.com)
        'domain': current_site.domain,
        'uid': uid,
        'token': token,
    }

    # Renderiza corpo em HTML e TXT
    html_message = render_to_string('users/account_activation_email.html', context)
    plain_message = render_to_string('users/account_activation_email.txt', context)

    # Usa o email configurado em settings.py como remetente
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email

    try:
        msg = EmailMultiAlternatives(subject, plain_message, from_email, [to_email])
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        logger.info(f"E-mail de ativação enviado para {to_email}")
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail de ativação para {to_email}: {e}")
        # Considerar como lidar com falha no envio (ex: logar erro crítico)


# --- RegisterView (VERSÃO CORRETA COM ATIVAÇÃO POR EMAIL) ---
class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    # Redireciona para página de "Verifique seu email" após submissão
    success_url = reverse_lazy('users:registration_confirm_email')

    def form_valid(self, form):
        # Salva o usuário mas não o loga ainda
        user = form.save(commit=False)
        user.is_active = False # Define usuário como inativo até confirmação
        user.save()

        # Envia o email de ativação
        send_activation_email(self.request, user)

        # Retorna o redirecionamento para success_url
        return HttpResponseRedirect(str(self.success_url))


# --- VIEW (Classe) para página de "Verifique seu email" ---
class RegistrationConfirmEmailView(TemplateView):
     template_name = 'users/registration_confirm_email.html'


# --- VIEW (Função) para ativar a conta via link do email ---
def activate(request, uidb64, token):
    try:
        # Decodifica o ID do usuário da URL
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None # Se o ID for inválido ou usuário não existir

    # Verifica se o usuário existe, se o token é válido para ele E se ele ainda não está ativo
    if user is not None and account_activation_token.check_token(user, token):
        if user.is_active:
             # Usuário já ativo (talvez clicou no link de novo)
             messages.info(request, 'Sua conta já está ativa. Você pode fazer login.')
             # Redireciona para o login ou uma página que indique que já está ativo
             return redirect('users:login') # Ou para account_activation_complete
        else:
            # Ativa o usuário
            user.is_active = True
            user.save()
            messages.success(request, 'Sua conta foi ativada com sucesso! Você já pode fazer login.')
            # Redireciona para página de sucesso
            return render(request, 'users/account_activation_complete.html')
    else:
        # Link inválido ou expirado
        return render(request, 'users/account_activation_invalid.html')


# --- CustomLoginView (COM CHECAGEM DE is_active) ---
class CustomLoginView(auth_views.LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'users/login.html'

    def form_valid(self, form):
        """Checa se o usuário está ativo antes de logar."""
        user = form.get_user()
        # Se o usuário existe mas NÃO está ativo
        if user is not None and not user.is_active:
            messages.error(self.request, 'Sua conta ainda não foi ativada. Por favor, verifique seu e-mail.')
            return self.form_invalid(form) # Retorna para a página de login com erro

        # Se usuário existe E está ativo (ou não existe, o que causa erro padrão),
        # prossegue com o login normal
        return super().form_valid(form)


# --- Views de Recuperação de Senha (Sem mudanças, apenas checando imports) ---
class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')

class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'


# --- View de Configurações ---
@login_required
def profile_settings_view(request):
    """
    Página de 'Configurações', onde o usuário atualiza o perfil.
    """
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('users:settings')
    else:
        form = UserProfileUpdateForm(instance=request.user)

    context = {
        'profile_form': form
    }
    return render(request, 'users/settings.html', context)