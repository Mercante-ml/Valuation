# chatbot/tasks.py
from celery import shared_task
from reports.models import ValuationReport
from django.db.models import F
from .agents import run_valuation_agent
import requests
import time
import logging
from django.conf import settings
from django.apps import apps # <-- ADICIONADO PARA OBTER O MODELO DE UTILIZADOR
import random # <-- ADICIONADO PARA RETRY DELAY

logger = logging.getLogger(__name__)

@shared_task
def process_valuation_request(report_id):
    """
    Tarefa do Celery para processar o valuation usando o agente Gemini
    e disparar a geração Gamma.
    """
    user = None # Inicializa user
    try:
        report = ValuationReport.objects.get(id=report_id)
        report.status = ValuationReport.StatusChoices.PROCESSING
        report.save(update_fields=['status']) # Salva apenas o status por enquanto

        user = report.user
        inputs = report.inputs_data

        # 1. Chama o Agente Gemini
        logger.info(f"Iniciando chamada ao Agente Gemini para Report {report_id}")
        agent_result = run_valuation_agent(inputs_data=inputs, user_razao_social=user.razao_social)
        logger.info(f"Agente Gemini retornou para Report {report_id}")

        # 2. Salva o resultado (incluindo possíveis erros do agente)
        report.result_data = agent_result # Sobrescreve/define result_data

        gamma_generation_triggered = False # Flag para saber se tentamos gerar

        # 3. Define o status do relatório baseado no resultado do agente Gemini
        if agent_result.get("error"):
            report.status = ValuationReport.StatusChoices.FAILED
            logger.error(f"Agente Gemini falhou para Report {report_id}: {agent_result.get('error')}")
        else:
            report.status = ValuationReport.StatusChoices.SUCCESS
            logger.info(f"Agente Gemini concluiu com sucesso para Report {report_id}.")

            # 4. Atualiza o contador de uso APENAS em caso de sucesso do Gemini
            if user: # Garante que user não é None
                # Obtém a classe do modelo de utilizador a partir de settings.AUTH_USER_MODEL
                User = apps.get_model(settings.AUTH_USER_MODEL)
                # Atualiza diretamente no banco de dados para evitar race conditions
                User.objects.filter(pk=user.pk).update(usage_count=F('usage_count') + 1)
                logger.info(f"Contador de uso incrementado para user {user.pk}")
            else:
                 logger.warning(f"Objeto User não disponível para incrementar usage_count no Report {report_id}")


            # 5. Prepara para disparar Gamma: Adiciona status pendente
            if report.result_data and report.result_data.get('prompt_gamma'):
                report.result_data['gamma_status'] = 'pending' # Indica que vamos tentar gerar
                gamma_generation_triggered = True
                logger.info(f"Gamma status definido como 'pending' para Report {report_id}")
            else:
                 logger.warning(f"Prompt Gamma não encontrado na resposta do Gemini para Report {report_id}. Geração Gamma não será disparada.")


        # 6. Salva o resultado final do Gemini e o status do relatório (e gamma_status se aplicável)
        report.save(update_fields=['result_data', 'status'])
        logger.info(f"Resultado Gemini e status final salvos para Report {report_id}")


        # 7. Dispara a tarefa Gamma APENAS SE o Gemini teve sucesso e gerou prompt
        if gamma_generation_triggered:
            logger.info(f"Disparando tarefa generate_gamma_presentation para Report {report_id}")
            generate_gamma_presentation.delay(report_id)

    # REMOVIDOS BLOCOS except DUPLICADOS DAQUI

    except ValuationReport.DoesNotExist:
        logger.error(f"Erro CRÍTICO: Relatório {report_id} não encontrado em process_valuation_request.")
    except Exception as e:
        logger.exception(f"Erro CRÍTICO inesperado em process_valuation_request para Report {report_id}: {e}")
        try:
            # Tenta marcar o relatório como falho se ainda existir
            report_qs = ValuationReport.objects.filter(id=report_id)
            if report_qs.exists():
                report_qs.update(
                    status=ValuationReport.StatusChoices.FAILED,
                    result_data={"error": f"Erro inesperado na tarefa Celery: {str(e)}"}
                )
        except Exception as inner_e:
             logger.error(f"Erro ao tentar marcar Report {report_id} como falho após exceção principal: {inner_e}")


# --- TAREFA PARA GERAR APRESENTAÇÃO GAMMA (COM RETENTATIVAS) ---
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_gamma_presentation(self, report_id):
    """
    Tarefa Celery para pegar o prompt do report, chamar a API Gamma,
    fazer polling e salvar a URL da apresentação gerada.
    """
    logger.info(f"Iniciando geração Gamma para Report ID: {report_id} (Tentativa {self.request.retries + 1})")
    report = None # Inicializa report como None
    generation_id = None # Inicializa generation_id
    try:
        report = ValuationReport.objects.get(id=report_id)

        # 1. Verificar prompt e status
        prompt_gamma = report.result_data.get('prompt_gamma')
        current_gamma_status = report.result_data.get('gamma_status')

        if not prompt_gamma:
            logger.warning(f"Report {report_id} não possui prompt_gamma. Abortando tarefa Gamma.")
            return
        # Não reprocessar se já completou ou falhou permanentemente
        if current_gamma_status in ['completed', 'failed']:
             logger.warning(f"Report {report_id} já tem gamma_status '{current_gamma_status}'. Abortando tarefa Gamma.")
             return

        # 2. Verificar API Key
        gamma_api_key = settings.GAMMA_API_KEY
        if not gamma_api_key:
            logger.error(f"GAMMA_API_KEY não configurada. Marcando falha para Report {report_id}.")
            if report.result_data:
                report.result_data['gamma_status'] = 'failed'
                report.save(update_fields=['result_data'])
            return

        # 3. Preparar chamada API
        headers = {"X-API-KEY": gamma_api_key, "Content-Type": "application/json"}
        gamma_payload = {"inputText": prompt_gamma, "format": "presentation", "textMode": "generate", "textOptions": {"language": "pt-br"}}
        gamma_endpoint = "https://public-api.gamma.app/v0.2/generations"

        # 4. Iniciar Geração
        logger.info(f"Enviando prompt para Gamma API para Report {report_id}")
        response_post = requests.post(gamma_endpoint, headers=headers, json=gamma_payload, timeout=30)
        response_post.raise_for_status()
        generation_id = response_post.json().get("generationId") # Atribui a generation_id
        if not generation_id:
            logger.error(f"Gamma API não retornou generationId para Report {report_id}. Resposta: {response_post.text}")
            raise ValueError("Gamma API não retornou ID de geração.")

        logger.info(f"Gamma iniciou geração (ID: {generation_id}) para Report {report_id}. Iniciando polling...")
        status_endpoint = f"{gamma_endpoint}/{generation_id}"
        start_time = time.time()
        timeout_seconds = 480 # 8 minutos

        # 5. Polling
        while (time.time() - start_time) < timeout_seconds:
            time.sleep(30) # Verifica a cada 30 segundos
            try:
                response_get = requests.get(status_endpoint, headers=headers, timeout=15)
                response_get.raise_for_status()
                status_data = response_get.json()
                current_status = status_data.get('status')
                logger.info(f"Status Gamma para {generation_id} (Report {report_id}): {current_status}")

                if current_status == "completed":
                    gamma_url = status_data.get("gammaUrl")
                    if gamma_url:
                        # 6. Sucesso: Salvar URL e status
                        report.gamma_presentation_url = gamma_url
                        if report.result_data:
                            report.result_data['gamma_status'] = 'completed'
                        report.save(update_fields=['gamma_presentation_url', 'result_data'])
                        logger.info(f"Apresentação Gamma concluída e URL salva para Report {report_id}: {gamma_url}")
                        return # Sucesso! Termina a tarefa
                    else:
                        logger.error(f"Status Gamma 'completed' mas sem gammaUrl para {generation_id}. Resposta: {status_data}")
                        raise ValueError("Resposta Gamma 'completed' sem URL.")

                elif current_status in ["failed", "error"]:
                     logger.error(f"Geração Gamma falhou explicitamente para {generation_id}. Status: {current_status}. Resposta: {status_data}")
                     raise ValueError(f"Geração Gamma falhou com status: {current_status}")

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout durante polling do status Gamma para {generation_id}. Tentando novamente...")
            except requests.exceptions.RequestException as poll_error:
                # Erros 4xx/5xx no polling são tratados aqui
                if poll_error.response is not None and 400 <= poll_error.response.status_code < 500:
                     logger.error(f"Erro cliente ({poll_error.response.status_code}) durante polling Gamma para {generation_id}. Abortando retentativas. Erro: {poll_error}")
                     raise # Não tentar novamente para erros cliente
                else:
                     logger.warning(f"Erro de rede/servidor durante polling Gamma para {generation_id}: {poll_error}. Tentando novamente...")
            # Continua o loop até timeout ou sucesso/falha explícita

        # Saiu do loop por timeout geral
        logger.error(f"Timeout geral ({timeout_seconds}s) atingido ao esperar geração Gamma para Report {report_id} (ID: {generation_id}).")
        raise TimeoutError("Geração Gamma demorou demasiado.")

    except ValuationReport.DoesNotExist:
        logger.error(f"Erro CRÍTICO: Report {report_id} não encontrado em generate_gamma_presentation.")
    except (requests.exceptions.RequestException, ValueError, TimeoutError) as e:
        # Erros esperados que podem justificar retentativa
        logger.warning(f"Erro tratável ({type(e).__name__}) na tarefa Gamma para Report {report_id}: {e}. Verificando retentativas...")
        try:
            # Tentar novamente com delay exponencial + jitter
            retry_delay = int(random.uniform(2, 5) * (2 ** self.request.retries))
            logger.info(f"Agendando retentativa para Report {report_id} em {retry_delay}s.")
            raise self.retry(exc=e, countdown=retry_delay)
        except self.MaxRetriesExceededError:
             logger.error(f"Máximo de retentativas atingido para Report {report_id} na tarefa Gamma.")
             if report and report.result_data and report.result_data.get('gamma_status') == 'pending':
                 report.result_data['gamma_status'] = 'failed'
                 report.save(update_fields=['result_data'])
    except Exception as e:
        # Erros inesperados
        logger.exception(f"Erro INESPERADO na tarefa generate_gamma_presentation para Report {report_id}: {e}")
        if report and report.result_data and report.result_data.get('gamma_status') == 'pending':
            report.result_data['gamma_status'] = 'failed'
            report.save(update_fields=['result_data']) # Marca como falha final