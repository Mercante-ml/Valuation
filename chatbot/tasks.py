# chatbot/tasks.py
from celery import shared_task
from reports.models import ValuationReport
from django.db.models import F
from .agents import run_valuation_agent
import requests # <-- IMPORTAR requests
import time     # <-- IMPORTAR time
import logging  # <-- IMPORTAR logging
from django.conf import settings # <-- IMPORTAR settings

logger = logging.getLogger(__name__) # Configura o logger

# Remova ou comente a função placeholder call_ai_valuation_model

@shared_task
def process_valuation_request(report_id):
    """
    Tarefa do Celery para processar o valuation usando o agente Gemini.
    """
    try:
        report = ValuationReport.objects.get(id=report_id)
        report.status = ValuationReport.StatusChoices.PROCESSING
        report.save()

        user = report.user
        inputs = report.inputs_data

        # 1. Chama o Agente Gemini
        agent_result = run_valuation_agent(inputs_data=inputs, user_razao_social=user.razao_social)

        # 2. Salva o resultado (incluindo possíveis erros do agente)
        report.result_data = agent_result
        
        # Define o status baseado no resultado do agente
        if agent_result.get("error"):
            report.status = ValuationReport.StatusChoices.FAILED
            logger.error(f"Agente Gemini falhou para Report {report_id}: {agent_result.get('error')}")
        else:
            report.status = ValuationReport.StatusChoices.SUCCESS
            logger.info(f"Agente Gemini concluiu com sucesso para Report {report_id}.")
            
            # 3. Atualiza o contador de uso APENAS em caso de sucesso
            user.usage_count = F('usage_count') + 1
            user.save(update_fields=['usage_count']) # Otimiza o save

        report.save() # Salva o resultado e o status final
        
        # --- CHAMAR TAREFA GAMMA APÓS SUCESSO DO GEMINI ---
        if report.status == ValuationReport.StatusChoices.SUCCESS and report.result_data.get('prompt_gamma'):
            logger.info(f"Disparando tarefa generate_gamma_presentation para Report {report_id}")
            generate_gamma_presentation.delay(report_id) # Chama a nova tarefa!
        # --- FIM DA CHAMADA GAMMA ---

    except ValuationReport.DoesNotExist:
        logger.error(f"Erro: Relatório {report_id} não encontrado.")
    except Exception as e:
        logger.exception(f"Erro crítico ao processar relatório {report_id}: {e}") # Usar logger.exception para incluir traceback
        try:
            report = ValuationReport.objects.get(id=report_id)
            report.status = ValuationReport.StatusChoices.FAILED
            report.result_data = {"error": f"Erro inesperado na tarefa Celery: {str(e)}"}
            report.save()
        except ValuationReport.DoesNotExist:
            pass
        
        # 4. Opcional: Chamar a tarefa para gerar apresentação Gamma
        # if report.status == ValuationReport.StatusChoices.SUCCESS:
        #     generate_gamma_presentation.delay(report_id)

    except ValuationReport.DoesNotExist:
        print(f"Erro: Relatório {report_id} não encontrado.")
        # Log error
    except Exception as e:
        print(f"Erro crítico ao processar relatório {report_id}: {e}")
        # Log error
        try:
            # Tenta marcar como falho se possível
            report = ValuationReport.objects.get(id=report_id)
            report.status = ValuationReport.StatusChoices.FAILED
            report.result_data = {"error": f"Erro inesperado na tarefa Celery: {str(e)}"}
            report.save()
        except ValuationReport.DoesNotExist:
            pass # Não há o que fazer se o report sumiu
        
# --- NOVA TAREFA PARA GERAR APRESENTAÇÃO GAMMA ---
@shared_task
def generate_gamma_presentation(report_id):
    """
    Tarefa Celery para pegar o prompt do report, chamar a API Gamma,
    e salvar a URL da apresentação gerada.
    """
    logger.info(f"Iniciando geração Gamma para Report ID: {report_id}")
    try:
        report = ValuationReport.objects.get(id=report_id)

        # 1. Verificar se temos um prompt
        prompt_gamma = report.result_data.get('prompt_gamma')
        if not prompt_gamma:
            logger.warning(f"Report {report_id} não possui prompt_gamma. Abortando.")
            return # Não há o que fazer

        # 2. Verificar API Key do Gamma
        gamma_api_key = settings.GAMMA_API_KEY
        if not gamma_api_key:
            logger.error("GAMMA_API_KEY não configurada. Abortando geração.")
            # Opcional: Atualizar status do report para indicar falha na config?
            return

        # 3. Preparar chamada para API Gamma (baseado no seu script)
        headers = {
            "X-API-KEY": gamma_api_key,
            "Content-Type": "application/json"
        }
        # Usaremos 'presentation' como formato
        gamma_payload = {
            "inputText": prompt_gamma,
            "format": "presentation",
            "textMode": "generate",
            "textOptions": {"language": "pt-br"},
            # "numCards": 7 # Opcional: Sugerir número de slides
        }
        gamma_endpoint = "https://public-api.gamma.app/v0.2/generations" # Endpoint base

        # 4. Fazer a requisição POST para iniciar a geração
        logger.info(f"Enviando prompt para Gamma API para Report {report_id}")
        response_post = requests.post(gamma_endpoint, headers=headers, json=gamma_payload)
        response_post.raise_for_status() # Lança erro para status HTTP >= 400

        generation_id = response_post.json().get("generationId")
        if not generation_id:
            logger.error(f"Gamma API não retornou generationId para Report {report_id}. Resposta: {response_post.text}")
            return

        logger.info(f"Gamma iniciou geração (ID: {generation_id}) para Report {report_id}. Iniciando polling...")
        status_endpoint = f"{gamma_endpoint}/{generation_id}"
        start_time = time.time()
        timeout_seconds = 300 # 5 minutos de timeout

        # 5. Fazer Polling do status
        while (time.time() - start_time) < timeout_seconds:
            time.sleep(15) # Espera 15 segundos entre verificações
            try:
                response_get = requests.get(status_endpoint, headers=headers)
                response_get.raise_for_status()
                status_data = response_get.json()
                current_status = status_data.get('status')
                logger.info(f"Status Gamma para {generation_id}: {current_status}")

                if current_status == "completed":
                    gamma_url = status_data.get("gammaUrl")
                    if gamma_url:
                        # 6. Salvar a URL no relatório
                        report.gamma_presentation_url = gamma_url
                        report.save(update_fields=['gamma_presentation_url'])
                        logger.info(f"Apresentação Gamma concluída e URL salva para Report {report_id}: {gamma_url}")
                        return # Sucesso!
                    else:
                        logger.error(f"Status Gamma 'completed' mas sem gammaUrl para {generation_id}. Resposta: {status_data}")
                        return # Falha

                elif current_status in ["failed", "error"]:
                     logger.error(f"Geração Gamma falhou para {generation_id}. Status: {current_status}. Resposta: {status_data}")
                     # Opcional: Salvar o erro no report?
                     return # Falha

            except requests.exceptions.RequestException as poll_error:
                logger.warning(f"Erro durante polling do status Gamma para {generation_id}: {poll_error}. Tentando novamente...")
                # Continua o loop até o timeout

        # Se saiu do loop por timeout
        logger.error(f"Timeout ( {timeout_seconds}s ) atingido ao esperar geração Gamma para Report {report_id} (ID: {generation_id}).")

    except ValuationReport.DoesNotExist:
        logger.error(f"Erro: Report {report_id} não encontrado na tarefa generate_gamma_presentation.")
    except requests.exceptions.RequestException as api_error:
        logger.error(f"Erro de API ao chamar Gamma para Report {report_id}: {api_error}. Resposta: {api_error.response.text if api_error.response else 'N/A'}")
        # Opcional: Salvar erro no report?
    except Exception as e:
        logger.exception(f"Erro inesperado na tarefa generate_gamma_presentation para Report {report_id}: {e}")
        # Opcional: Salvar erro no report?