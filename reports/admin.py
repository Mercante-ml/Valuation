# reports/admin.py
from django.contrib import admin
from .models import ValuationReport
import json # Para formatar o JSON
from django.utils.safestring import mark_safe # Para exibir HTML formatado

@admin.register(ValuationReport)
class ValuationReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_link', 'status', 'created_at', 'gamma_link_display')
    list_filter = ('status', 'created_at')
    search_fields = ('user__razao_social', 'user__cnpj', 'id')
    readonly_fields = ('user', 'inputs_data_formatted', 'result_data_formatted', 'created_at', 'updated_at', 'gamma_presentation_url') # Campos não editáveis no admin
    list_display_links = ('id',) # Torna o ID clicável

    # Campo customizado para exibir o user como link
    def user_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:users_customuser_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user)
    user_link.short_description = 'Usuário' # Nome da coluna

    # Campo customizado para exibir link do Gamma
    def gamma_link_display(self, obj):
        if obj.gamma_presentation_url:
            return mark_safe(f'<a href="{obj.gamma_presentation_url}" target="_blank">Abrir Gamma</a>')
        return "N/A"
    gamma_link_display.short_description = 'Gamma Link'

    # Funções para formatar os campos JSON para melhor leitura
    def inputs_data_formatted(self, obj):
        formatted_json = json.dumps(obj.inputs_data, indent=2, ensure_ascii=False)
        return mark_safe(f'<pre>{formatted_json}</pre>')
    inputs_data_formatted.short_description = 'Dados Fornecidos (JSON)'

    def result_data_formatted(self, obj):
        formatted_json = json.dumps(obj.result_data, indent=2, ensure_ascii=False)
        return mark_safe(f'<pre>{formatted_json}</pre>')
    result_data_formatted.short_description = 'Resultado da IA (JSON)'

    # Organiza os campos no formulário de visualização/edição
    fieldsets = (
        (None, {
            'fields': ('user', 'status', 'created_at', 'updated_at')
        }),
        ('Dados Coletados', {
            'fields': ('inputs_data_formatted',),
        }),
        ('Resultados', {
            'fields': ('result_data_formatted', 'gamma_presentation_url')
        }),
    )