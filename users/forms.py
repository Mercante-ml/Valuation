# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    Formulário para a página de "Cadastrar".
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Define os campos que aparecerão no formulário
        fields = ('razao_social', 'cnpj', 'email')

    def clean_cnpj(self):
        """Garante que o CNPJ seja salvo apenas com números."""
        data = self.cleaned_data['cnpj']
        # Remove pontuação (ex: 12.345.678/0001-99 -> 12345678000199)
        cnpj_limpo = re.sub(r'[^0-9]', '', data)
        return cnpj_limpo

class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulário para a página de "Login".
    Customizado para pedir "CNPJ" em vez de "username".
    """
    # O campo 'username' é usado pelo backend do Django
    # Nós apenas mudamos o 'label' dele para "CNPJ"
    username = forms.CharField(
        label="CNPJ",
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'})
    )
    
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )