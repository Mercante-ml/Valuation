# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm # Importa o formulário de criação
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Usa o nosso formulário customizado para a página "Adicionar utilizador"
    add_form = CustomUserCreationForm

    model = CustomUser
    
    # --- O que mostrar na lista principal de utilizadores ---
    list_display = (
        'cnpj', 
        'email', 
        'razao_social', 
        'ddd', 
        'telefone', 
        'is_staff', 
        'is_active', 
        'usage_count', 
        'date_joined' # Adicionado aqui para visualização
    )
    
    # --- O que pode ser pesquisado ---
    search_fields = ('cnpj', 'email', 'razao_social', 'telefone')
    
    # --- Filtros laterais ---
    list_filter = ('is_staff', 'is_active', 'date_joined')
    
    # --- Campo de ordenação ---
    ordering = ('cnpj',)

    # --- A CORREÇÃO CRÍTICA ESTÁ AQUI ---

    # 1. Define os campos que são apenas para leitura na página de edição.
    # 'date_joined' e 'last_login' são geridos automaticamente pelo Django.
    readonly_fields = ('last_login', 'date_joined')

    # 2. Define os fieldsets para a PÁGINA DE ADIÇÃO (add)
    # (Usado quando clica em "Add custom user")
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # Usa os campos do CustomUserCreationForm + password
            'fields': ('cnpj', 'razao_social', 'email', 'ddd', 'telefone', 'is_staff', 'is_active', 'password', 'password2'),
        }),
    )

    # 3. Define os fieldsets para a PÁGINA DE EDIÇÃO (change)
    # (Usado quando clica num utilizador existente. Substitui completamente o padrão.)
    fieldsets = (
        # Informação Principal (Login e Senha)
        (None, {'fields': ('cnpj', 'password')}),
        
        # Informações da Empresa (Nossos campos)
        ('Dados da Empresa', {'fields': ('razao_social', 'email', 'ddd', 'telefone')}),
        
        # Permissões
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        
        # Contagem de Uso
        ('Uso', {'fields': ('usage_count',)}),
        
        # Datas Importantes (Como estão em 'readonly_fields', serão mostrados mas não editáveis)
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    # --- FIM DA CORREÇÃO ---

# Registra o modelo CustomUser com a configuração CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)