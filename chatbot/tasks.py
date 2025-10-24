# apps/chatbot/tasks.py
import time
from celery import shared_task
from users.models import CustomUser
from reports.models import ValuationReport

def call_ai_valuation_model(inputs):
    """
    FUNÇÃO PLACEHOLDER (SUBSTITUA)
    
    Esta é a função que você precisa criar.
    Ela recebe os inputs do chat e deve retornar um dicionário
    com o resultado do valuation e o feedback.
    
    Ex:
    import openai
    openai.api_key = "..."
    response = openai.ChatCompletion.create(...)
    return {"valuation_value": 1000000, "feedback": "Seu negócio..."}
    """
    print(f"Iniciando cálculo de IA para: {inputs}")
    # Simula uma chamada de IA demorada
    time.sleep(15) 
    print("Cálculo de IA concluído.")
    
    # Resultado fictício
    return {
        "valuation_calculado": 5000000,
        "metodologia": "Fluxo de Caixa Descontado (Simulado)",
        "feedback_ia": "Com base nos seus inputs de faturamento e custos, o valuation simulado é X. Pontos fortes: ... Pontos a melhorar: ...",
    }

@shared_task
def process_valuation_request(report_id):
    """
    Tarefa do Celery para processar o valuation.
    """
    try:
        report = ValuationReport.objects.get(id=report_id)
        report.status = ValuationReport.StatusChoices.PROCESSING
        report.save()
        
        user = report.user
        inputs = report.inputs_data
        
        # 1. Chama a IA (a função "cara")
        ai_result = call_ai_valuation_model(inputs)
        
        # 2. Salva o resultado no relatório
        report.result_data = ai_result
        report.status = ValuationReport.StatusChoices.SUCCESS
        report.save()
        
        # 3. Atualiza o contador de uso do usuário
        # (Usando F() para evitar 'race conditions')
        from django.db.models import F
        user.usage_count = F('usage_count') + 1
        user.save()
        
        # 4. Opcional: Gerar o PDF/Gamma
        # (Esta pode ser outra tarefa celery!)
        # generate_pdf_report.delay(report_id)

    except ValuationReport.DoesNotExist:
        print(f"Erro: Relatório {report_id} não encontrado.")
    except Exception as e:
        print(f"Erro ao processar relatório {report_id}: {e}")
        # Tenta marcar o relatório como falho
        try:
            report = ValuationReport.objects.get(id=report_id)
            report.status = ValuationReport.StatusChoices.FAILED
            report.result_data = {"error": str(e)}
            report.save()
        except ValuationReport.DoesNotExist:
            pass # Não há o que fazer