# apps/reports/models.py
from django.db import models
from django.conf import settings

class ValuationReport(models.Model):
    """Armazena o resultado de um cálculo de valuation."""
    
    gamma_presentation_url = models.URLField(
        max_length=500, # URLs do Gamma podem ser longas
        null=True,
        blank=True,
        help_text="URL da apresentação gerada pelo Gamma (se houver)"
    ) # <-- ADICIONE ESTE CAMPO
    
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PROCESSING = 'PROCESSING', 'Processando'
        SUCCESS = 'SUCCESS', 'Sucesso'
        FAILED = 'FAILED', 'Falha'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='reports'
    )
    # Inputs que vieram do chatbot
    inputs_data = models.JSONField(help_text="JSON com as perguntas e respostas do chat")
    
    # Resultado que veio da IA
    result_data = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON com o feedback e cálculo da IA"
    )
    
    # Campo para o PDF ou link da Gamma (como você sugeriu)
    output_file = models.FileField(upload_to='reports_pdf/', null=True, blank=True)
    
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.PENDING
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Relatório de {self.user.razao_social} em {self.created_at.strftime('%d/%m/%Y')}"