# chatbot/agents.py
import google.generativeai as genai
from django.conf import settings
import json
import logging # Para registrar erros
from django.apps import apps # Para obter o modelo de utilizador

logger = logging.getLogger(__name__)

def run_valuation_agent(inputs_data: dict, user_razao_social: str) -> dict:
    """
    Chama a API Gemini para analisar os inputs, calcular o valuation
    e gerar um prompt para o Gamma.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        logger.error("GEMINI_API_KEY não configurada.")
        return {
            "error": "Configuração da API de IA ausente.",
            "valuation_calculado": None,
            "metodologia_usada": "Erro",
            "resumo_para_gamma": {},
            "prompt_gamma": None
        }

    genai.configure(api_key=api_key)
    # Certifique-se que está a usar um modelo disponível, como 'gemini-pro'
    # model = genai.GenerativeModel('gemini-1.5-flash') # Este deu erro 404 antes
    model = genai.GenerativeModel('gemini-pro')

    # -- Construção do Prompt para Gemini --

    # Prepara os inputs para o prompt de forma legível
    inputs_str = "\n".join([f"- {key.replace('_', ' ').capitalize()}: {value}" for key, value in inputs_data.items()])

    # --- PROMPT ATUALIZADO COM NOVAS FAIXAS DE MÚLTIPLOS ---
    prompt = f"""
    Você é um assistente de análise financeira especializado em valuation simplificado para pequenas e médias empresas (PMEs).
    Analise os seguintes dados fornecidos para a empresa "{user_razao_social}":

    {inputs_str}

    Sua tarefa é realizar as seguintes ações e retornar a resposta **estritamente** no formato JSON especificado abaixo:

    1.  **Calcular Lucratividade Estimada:** Baseado no faturamento anual, custos operacionais mensais e alíquota de imposto sobre lucro, estime o Lucro Líquido Anual. Considere o custo operacional mensal * 12. O cálculo é: Lucro Líquido = (Faturamento Anual - (Custos Operacionais Mensais * 12)) * (1 - (Alíquota Imposto Lucro % / 100)).
    2.  **Estimar Valuation:** Use um método de Múltiplo de Faturamento Anual. Escolha um múltiplo *razoável* baseado no setor de atuação, considerando estas faixas típicas para PMEs (pequenas/médias empresas):
        - Varejo Tradicional: 0.25x - 0.75x
        - Serviços Gerais/Profissionais: 0.75x - 2.0x
        - Tecnologia (SaaS/Software): 2.0x - 6.0x (pode ser maior se a Projeção de Crescimento Anual for superior a 30-40%)
        - Serviços de TI (Consultoria/Agência): 1.0x - 2.5x
        - Indústria: 0.4x - 1.0x
        - Outros/Não especificado: 0.5x - 1.5x (use esta faixa se o setor for muito genérico ou não se encaixar)

        Use o setor informado ('{inputs_data.get('setor_atuacao', 'N/A')}') para escolher uma faixa apropriada. Considere também a projeção de crescimento ('{inputs_data.get('projecao_crescimento_anual_perc', 0)}%') e o tempo de operação ('{inputs_data.get('tempo_operacao_anos', 0)} anos') para refinar o múltiplo *dentro* da faixa escolhida (crescimento maior e mais tempo de operação geralmente justificam um múltiplo na parte superior da faixa). Justifique brevemente a escolha do múltiplo (ex: "Múltiplo X.Yx escolhido devido ao setor de Serviços e crescimento projetado moderado."). Calcule o Valuation = Faturamento Anual * Múltiplo Escolhido. Arredonde o valuation final para duas casas decimais.
    3.  **Gerar Resumo Estruturado:** Crie um resumo conciso com os pontos-chave, formatando os valores monetários.
    4.  **Gerar Prompt para Gamma:** Baseado no resumo, crie um prompt de texto otimizado para a API do Gamma (gamma.app) gerar uma apresentação de 5-7 slides sobre a empresa e seu valuation.

    **Formato de Resposta JSON OBRIGATÓRIO (Use R$ e formato X.XXX,XX para valores):**
    {{
        "valuation_calculado": <valor_numerico_float_do_valuation_arredondado>,
        "metodologia_usada": "Múltiplo de Faturamento (Setor: [Nome do Setor], Múltiplo: [Valor X.Yx]) - [Breve Justificativa da Escolha]",
        "resumo_para_gamma": {{
            "empresa_nome": "{user_razao_social}",
            "setor": "[Setor de Atuação]",
            "tempo_operacao": "[Tempo de Operação] anos",
            "diferencial": "[Diferencial Competitivo]",
            "snapshot_financeiro": "Faturamento Anual: R$ [Valor Formatado], Lucratividade Líquida Anual Estimada: R$ [Valor Formatado]",
            "valuation_estimado": "R$ [Valor Formatado]",
            "metodologia_resumo": "Baseado em Múltiplo de Faturamento de [Valor X.Yx] para o setor.",
            "principais_drivers": "Faturamento atual de R$ [Valor Formatado] e potencial de crescimento de [{inputs_data.get('projecao_crescimento_anual_perc', 0)}%] no setor [Setor de Atuação].",
            "pontos_fortes": "Principalmente [Diferencial Competitivo] e {inputs_data.get('tempo_operacao_anos', 0)} anos no mercado.",
            "pontos_atencao": "Dependência do crescimento projetado ({inputs_data.get('projecao_crescimento_anual_perc', 0)}%), concorrência no setor e necessidade de gestão de custos."
        }},
        "prompt_gamma": "Crie uma apresentação concisa sobre a empresa {user_razao_social}. Use um tom profissional e visual atraente. Slide 1: Título 'Valuation Estimado - {user_razao_social}'. Slide 2: Sobre a Empresa (Setor: [Setor], Tempo de Operação: [Tempo], Principal Diferencial: [Diferencial]). Slide 3: Snapshot Financeiro (Faturamento Anual: R$ [Valor], Lucro Anual Estimado: R$ [Valor]). Slide 4: Valuation Estimado (Valor: R$ [Valor], Metodologia: Múltiplo de Faturamento [X.Yx]). Slide 5: Análise Resumida (Principais Drivers, Pontos Fortes e Pontos de Atenção). Slide 6: Próximos Passos (Sugira foco em crescimento sustentável e otimização de custos)."
    }}

    **Instruções Adicionais:**
    - Seja realista na escolha do múltiplo dentro das faixas fornecidas.
    - **Formate TODOS os valores monetários** no JSON final (snapshot_financeiro, valuation_estimado, prompt_gamma) como "R$ X.XXX.XXX,XX" (separador de milhar com ponto, decimal com vírgula). Use formatação brasileira.
    - Se algum dado crucial faltar ou for inválido para o cálculo (ex: faturamento não numérico), retorne um JSON com uma chave "error" descrevendo o problema e as outras chaves como null ou vazias.
    - **NÃO inclua nenhuma explicação, comentário ou ```json``` fora do formato JSON.** Sua resposta deve ser *apenas* o JSON solicitado.
    """

    try:
        # Configurações de Geração (ajuste conforme necessário)
        generation_config = genai.types.GenerationConfig(
            # temperature=0.7 # Um pouco de criatividade, mas não muita para finanças
            # max_output_tokens=2048
        )
        # Configurações de Segurança (podem precisar ser ajustadas se o Gemini bloquear respostas)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        logger.debug(f"Enviando prompt para Gemini para {user_razao_social}:\n{prompt}")
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        # Tenta limpar e parsear a resposta JSON
        cleaned_response = response.text.strip().lstrip('```json').rstrip('```').strip()

        logger.debug(f"Resposta bruta da IA: {response.text}")
        logger.debug(f"Resposta limpa da IA: {cleaned_response}")

        result_json = json.loads(cleaned_response)

        # Validação básica do JSON retornado
        required_keys = ["valuation_calculado", "metodologia_usada", "resumo_para_gamma", "prompt_gamma"]
        if not all(key in result_json for key in required_keys):
            logger.error(f"Resposta da IA para {user_razao_social} não contém todas as chaves esperadas. Resposta: {cleaned_response}")
            raise ValueError("Resposta da IA não contém todas as chaves esperadas.")

        # Verifica se a IA retornou um erro interno
        if result_json.get("error"):
             logger.error(f"IA retornou erro interno para {user_razao_social}: {result_json.get('error')}")
             # Retorna o dicionário de erro da IA diretamente
             return result_json


        logger.info(f"Análise Gemini concluída com sucesso para {user_razao_social}")
        return result_json

    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON da resposta da IA para {user_razao_social}: {e}\nResposta recebida: {cleaned_response}")
        return {
            "error": "Não foi possível processar a resposta da IA (formato inválido). Tente novamente.",
            "valuation_calculado": None,
            "metodologia_usada": "Erro",
            "resumo_para_gamma": {},
            "prompt_gamma": None
        }
    except Exception as e:
        # Captura outros erros da API Gemini (ex: bloqueio de segurança, erro de chave)
        logger.error(f"Erro inesperado ao chamar a API Gemini para {user_razao_social}: {e}", exc_info=True) # exc_info=True para logar traceback
        # Tenta retornar uma mensagem de erro mais útil se possível
        error_message = f"Erro ao comunicar com a IA: {e}"
        # Verifica se é um erro comum de bloqueio de segurança
        if "response.prompt_feedback" in str(e): # Verifica se o erro menciona prompt_feedback
             error_message = "A IA bloqueou a resposta devido a políticas de segurança. Tente reformular seus inputs."

        return {
            "error": error_message,
            "valuation_calculado": None,
            "metodologia_usada": "Erro",
            "resumo_para_gamma": {},
            "prompt_gamma": None
        }

# --- É necessário importar 'apps' para obter o modelo de utilizador ---
from django.apps import apps