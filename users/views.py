# users/views.py
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth import views as auth_views
from django.contrib import messages # <--- FALTAVA ESTE
from django.shortcuts import render, redirect # <--- FALTAVA ESTE
from django.contrib.auth.decorators import login_required # <--- FALTAVA ESTE

from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm,
    UserProfileUpdateForm
)

class RegisterView(CreateView):
    """
    View para a página de cadastro.
    Usa o formulário que criamos e redireciona para o login ao sucesso.
    """
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login') # Redireciona para o login após cadastrar

    def form_valid(self, form):
        # Opcional: Se você quiser que o usuário
        # confirme o email, sete 'is_active' para False aqui.
        # user = form.save(commit=False)
        # user.is_active = False # Desativa a conta
        # user.save()
        # ... aqui você enviaria o email de confirmação ...
        
        # Por enquanto, vamos logar o usuário direto (comportamento padrão)
        return super().form_valid(form)

class CustomLoginView(auth_views.LoginView):
    """
    View para a página de login.
    Usa o formulário de login customizado.
    """
    form_class = CustomAuthenticationForm
    template_name = 'users/login.html'

# LogoutView não precisa de customização, podemos usar a do Django direto nas URLs.

# --- Views de Recuperação de Senha ---
# O Django já tem TODAS as views prontas. Só precisamos apontar para
# os templates corretos. Não precisamos escrever código Python.

class CustomPasswordResetView(auth_views.PasswordResetView):
    """Página 'Esqueci minha senha'."""
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html' # O email em si
    subject_template_name = 'users/password_reset_subject.txt' # Assunto do email
    success_url = reverse_lazy('users:password_reset_done')

class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    """Página 'Email de recuperação enviado'."""
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Página para 'Digitar a nova senha' (a que o link do email leva)."""
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """Página 'Senha alterada com sucesso'."""
    template_name = 'users/password_reset_complete.html'
    
# --- NOVA VIEW DE CONFIGURAÇÕES ---
@login_required
def profile_settings_view(request):
    """
    Página de 'Configurações', onde o usuário atualiza o perfil.
    """
    if request.method == 'POST':
        # Se o formulário foi enviado, preenche com os dados do POST
        form = UserProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            # Envia uma mensagem de sucesso
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('users:settings') # Redireciona para a mesma página
    else:
        # Se for um GET, apenas mostra o formulário preenchido com os dados atuais
        form = UserProfileUpdateForm(instance=request.user)

    context = {
        'profile_form': form
    }
    return render(request, 'users/settings.html', context)