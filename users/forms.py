# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
import re

class CustomUserCreationForm(UserCreationForm):
    """
    Formulário para a página de "Cadastrar".
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Define os campos que aparecerão no formulário
        fields = ('razao_social', 'cnpj', 'email', 'ddd', 'telefone', 'is_staff', 'is_active')

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
    
# --- NOVO FORMULÁRIO PARA ATUALIZAR O PERFIL ---
class UserProfileUpdateForm(forms.ModelForm):
    """
    Formulário para o usuário editar seus próprios dados de perfil.
    """
    class Meta:
        model = CustomUser
        # Campos que o usuário PODE editar
        fields = ('razao_social', 'email', 'ddd', 'telefone')

    def __init__(self, *args, **kwargs):
        """
        Adiciona classes do Bootstrap e define o CNPJ como readonly.
        """
        super().__init__(*args, **kwargs)
        
        # Adiciona um campo 'cnpj' desabilitado, apenas para exibição
        # Pegamos o valor da 'instance' (o objeto do usuário)
        cnpj_val = self.instance.cnpj if self.instance else ''
        self.fields['cnpj'] = forms.CharField(
            label="CNPJ",
            initial=cnpj_val,
            widget=forms.TextInput(attrs={'readonly': True, 'class': 'form-control-plaintext'})
        )
        
        # Reordena os campos
        self.order_fields(['cnpj', 'razao_social', 'email', 'ddd', 'telefone'])