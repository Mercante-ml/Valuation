# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Define como o CustomUser será exibido no Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Campos a serem exibidos na lista de usuários
    list_display = ('cnpj', 'email', 'razao_social', 'ddd', 'telefone', 'is_staff', 'is_active', 'usage_count')
    # Campos pelos quais se pode pesquisar
    search_fields = ('cnpj', 'email', 'razao_social', 'ddd', 'telefone',)
    # Campos que podem ser usados para filtrar
    list_filter = ('is_staff', 'is_active')
    # Agrupamento dos campos no formulário de edição (usa a estrutura padrão do UserAdmin)
    fieldsets = UserAdmin.fieldsets + (
        ('Dados da Empresa', {'fields': ('razao_social', 'ddd', 'telefone', 'usage_count')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados da Empresa', {'fields': ('razao_social', 'ddd', 'telefone')}),
    )
    # Define o campo de login (já definido no model, mas bom ter aqui)
    ordering = ('cnpj',)

# Registra o modelo CustomUser com a configuração CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)