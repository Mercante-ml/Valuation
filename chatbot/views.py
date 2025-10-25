# chatbot/views.py
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from reports.models import ValuationReport
from .tasks import process_valuation_request
# Remova a importação antiga de CustomUser se não for mais usada aqui

MAX_FREE_USES = 5

@login_required
def dashboard_view(request):
    context = {
        'reports': request.user.reports.all().order_by('-created_at')
    }
    return render(request, 'chatbot/dashboard.html', context)

# --- FUNÇÃO DE VALIDAÇÃO BACKEND (Exemplo) ---
def validate_inputs_backend(inputs):
    """Valida os tipos e regras dos inputs no backend."""
    errors = {}
    validated_data = {}

    # Valida faturamento_anual (número > 0)
    try:
        val = float(inputs.get('faturamento_anual', 0))
        if val <= 0: raise ValueError("Deve ser positivo.")
        validated_data['faturamento_anual'] = val
    except (TypeError, ValueError):
        errors['faturamento_anual'] = "Faturamento anual inválido ou não informado."
        
    # Valida custos_operacionais_mensais (número >= 0)
    try:
        val = float(inputs.get('custos_operacionais_mensais', 0))
        if val < 0: raise ValueError("Não pode ser negativo.")
        validated_data['custos_operacionais_mensais'] = val
    except (TypeError, ValueError):
        errors['custos_operacionais_mensais'] = "Custo operacional mensal inválido."

    # Valida aliquota_imposto_lucro_perc (0 a 100)
    try:
        val = float(inputs.get('aliquota_imposto_lucro_perc', 0))
        if not (0 <= val <= 100): raise ValueError("Deve estar entre 0 e 100.")
        validated_data['aliquota_imposto_lucro_perc'] = val
    except (TypeError, ValueError):
        errors['aliquota_imposto_lucro_perc'] = "Alíquota de imposto inválida."
        
    # Valida projecao_crescimento_anual_perc (número)
    try:
        val = float(inputs.get('projecao_crescimento_anual_perc', 0))
        validated_data['projecao_crescimento_anual_perc'] = val # Pode ser negativo
    except (TypeError, ValueError):
        errors['projecao_crescimento_anual_perc'] = "Projeção de crescimento inválida."
        
    # Valida setor_atuacao (texto não vazio)
    val = str(inputs.get('setor_atuacao', '')).strip()
    if not val: errors['setor_atuacao'] = "Setor de atuação não informado."
    else: validated_data['setor_atuacao'] = val
    
    # Valida tempo_operacao_anos (inteiro >= 0)
    try:
        val = int(inputs.get('tempo_operacao_anos', 0))
        if val < 0: raise ValueError("Não pode ser negativo.")
        validated_data['tempo_operacao_anos'] = val
    except (TypeError, ValueError):
         errors['tempo_operacao_anos'] = "Tempo de operação inválido."
         
    # Valida diferencial_competitivo (texto não vazio)
    val = str(inputs.get('diferencial_competitivo', '')).strip()
    if not val: errors['diferencial_competitivo'] = "Diferencial competitivo não informado."
    else: validated_data['diferencial_competitivo'] = val

    if errors:
        return None, errors # Retorna None e o dicionário de erros
    return validated_data, None # Retorna dados validados e None para erros

# --- View da API Atualizada ---
@login_required
@require_POST
@csrf_exempt # Mantenha se não quiser configurar o token CSRF no JS
def calculate_valuation_view(request):
    """Recebe dados do chatbot, VALIDA NO BACKEND, e inicia a tarefa."""
    try:
        if request.user.usage_count >= MAX_FREE_USES:
            return JsonResponse({
                "status": "error",
                "message": "Você atingiu seu limite de simulações gratuitas."
            }, status=403)

        data = json.loads(request.body)
        raw_inputs = data.get('inputs')

        if not raw_inputs:
            return JsonResponse({"status": "error", "message": "Nenhum dado recebido."}, status=400)

        # VALIDAÇÃO NO BACKEND
        validated_inputs, errors = validate_inputs_backend(raw_inputs)
        
        if errors:
            # Formata a mensagem de erro
            error_message = "Por favor, corrija os seguintes erros: " + "; ".join(errors.values())
            return JsonResponse({
                "status": "error",
                "message": error_message,
                "details": errors # Opcional: envia detalhes dos erros
            }, status=400) # Bad Request

        # Cria o Relatório com os DADOS VALIDADOS
        report = ValuationReport.objects.create(
            user=request.user,
            inputs_data=validated_inputs, # USA OS DADOS VALIDADOS
            status=ValuationReport.StatusChoices.PENDING
        )

        # Inicia a tarefa Celery
        process_valuation_request.delay(report_id=report.id)

        return JsonResponse({
            "status": "success",
            "message": "Sua análise foi iniciada! O resultado aparecerá no seu dashboard em breve.",
            "report_id": report.id
        })

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "JSON mal formatado."}, status=400)
    except Exception as e:
        # Logar o erro real no servidor
        print(f"Erro inesperado na view calculate_valuation: {e}") 
        return JsonResponse({"status": "error", "message": "Ocorreu um erro inesperado no servidor."}, status=500)