# apps/chatbot/views.py
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt # Cuidado com isso em produção
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from reports.models import ValuationReport
from .tasks import process_valuation_request

# Limite de uso gratuito
MAX_FREE_USES = 3

@login_required # Garante que o usuário está logado
def dashboard_view(request):
    """
    Página principal do simulador (onde o chatbot mora).
    """
    # TODO: Carregar histórico de relatórios
    context = {
        'reports': request.user.reports.all().order_by('-created_at')
    }
    return render(request, 'chatbot/dashboard.html', context)


@login_required
@require_POST # Esta view só aceita requisições POST
@csrf_exempt # Use 'ensure_csrf_cookie' no frontend em vez disso
def calculate_valuation_view(request):
    """
    View 'API' que recebe os dados do chatbot e inicia a tarefa.
    """
    try:
        # 1. Verifica limite de uso
        if request.user.usage_count >= MAX_FREE_USES:
            return JsonResponse({
                "status": "error",
                "message": "Você atingiu seu limite de simulações gratuitas."
            }, status=403) # 403 Forbidden
            
        # 2. Pega os dados do chatbot (frontend)
        data = json.loads(request.body)
        inputs = data.get('inputs') # Ex: {"faturamento": 10000, ...}
        
        if not inputs:
            return JsonResponse({"status": "error", "message": "Inputs inválidos."}, status=400)

        # 3. Cria o "Relatório" no banco de dados
        report = ValuationReport.objects.create(
            user=request.user,
            inputs_data=inputs,
            status=ValuationReport.StatusChoices.PENDING
        )

        # 4. Inicia a tarefa do CelERY! (.delay() é a chave)
        process_valuation_request.delay(report_id=report.id)

        # 5. Retorna sucesso IMEDIATAMENTE para o frontend
        return JsonResponse({
            "status": "success",
            "message": "Sua análise foi iniciada! O resultado aparecerá no seu dashboard em breve.",
            "report_id": report.id
        })

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "JSON mal formatado."}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)