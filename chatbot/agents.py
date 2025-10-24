# chatbot/agents.py
import google.generativeai as genai
from django.conf import settings
import json
import logging # Para registrar erros

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
    model = genai.GenerativeModel('gemini-2.5-flash') # Ou outro modelo Gemini

    # -- Construção do Prompt para Gemini --
    # Este prompt é crucial e pode precisar de muitos ajustes!
    
    # Prepara os inputs para o prompt de forma legível
    inputs_str = "\n".join([f"- {key.replace('_', ' ').capitalize()}: {value}" for key, value in inputs_data.items()])
    
    prompt = f"""
    Você é um assistente de análise financeira especializado em valuation simplificado para pequenas e médias empresas.
    Analise os seguintes dados fornecidos para a empresa "{user_razao_social}":

    {inputs_str}

    Sua tarefa é realizar as seguintes ações e retornar a resposta **estritamente** no formato JSON especificado abaixo:

    1.  **Calcular Lucratividade Estimada:** Baseado no faturamento anual, custos operacionais mensais e alíquota de imposto sobre lucro, estime o Lucro Líquido Anual. Considere o custo operacional mensal * 12.
    2.  **Estimar Valuation:** Use um método de Múltiplo de Faturamento. Escolha um múltiplo *razoável* baseado no setor de atuação (ex: Varejo 0.5-1.0x, Serviços 1.0-2.0x, Tecnologia 2.0-5.0x+). Justifique brevemente a escolha do múltiplo. Calcule o Valuation = Faturamento Anual * Múltiplo Escolhido.
    3.  **Gerar Resumo Estruturado:** Crie um resumo conciso com os pontos-chave.
    4.  **Gerar Prompt para Gamma:** Baseado no resumo, crie um prompt de texto otimizado para a API do Gamma (gamma.app) gerar uma apresentação de 5-7 slides sobre a empresa e seu valuation.

    **Formato de Resposta JSON OBRIGATÓRIO:**
    {{
        "valuation_calculado": <valor_numerico_float_do_valuation>,
        "metodologia_usada": "Múltiplo de Faturamento (Setor: [Nome do Setor], Múltiplo: [Valor X.Yx])",
        "resumo_para_gamma": {{
            "empresa_nome": "{user_razao_social}",
            "setor": "[Setor de Atuação]",
            "tempo_operacao": "[Tempo de Operação] anos",
            "diferencial": "[Diferencial Competitivo]",
            "snapshot_financeiro": "Faturamento Anual: R$ [Valor Formatado], Lucratividade Líquida Anual Estimada: R$ [Valor Formatado]",
            "valuation_estimado": "R$ [Valor Formatado]",
            "metodologia_resumo": "Baseado em Múltiplo de Faturamento de [Valor X.Yx] para o setor.",
            "principais_drivers": "Faturamento atual e potencial de crescimento no setor [Nome do Setor].",
            "pontos_fortes": "Principalmente [Diferencial Competitivo] e [Tempo de Operação] anos no mercado.",
            "pontos_atencao": "Dependência do crescimento projetado, concorrência no setor."
        }},
        "prompt_gamma": "Crie uma apresentação concisa sobre a empresa {user_razao_social}. Slide 1: Título 'Valuation Estimado - {user_razao_social}'. Slide 2: Sobre a Empresa (Setor: [Setor], Tempo: [Tempo], Diferencial: [Diferencial]). Slide 3: Snapshot Financeiro (Faturamento Anual: R$ [Valor], Lucro Anual Estimado: R$ [Valor]). Slide 4: Valuation Estimado (R$ [Valor] - Metodologia: Múltiplo de Faturamento [X.Yx]). Slide 5: Drivers, Pontos Fortes e Atenção. Slide 6: Próximos Passos (sugestão genérica)."
    }}

    **Instruções Adicionais:**
    - Seja realista na escolha do múltiplo.
    - Formate os valores monetários no resumo e prompt gamma como "R$ X.XXX.XXX,XX".
    - Se algum dado crucial faltar ou for inválido para o cálculo, retorne um erro no JSON.
    - **NÃO inclua nenhuma explicação fora do formato JSON.** Sua resposta deve ser *apenas* o JSON.
    """

    try:
        response = model.generate_content(prompt)
        
        # Tenta limpar e parsear a resposta JSON
        # Modelos podem retornar ```json ... ``` ou apenas o JSON cru.
        cleaned_response = response.text.strip().lstrip('```json').rstrip('```').strip()
        
        logger.debug(f"Resposta bruta da IA: {response.text}") # Log para debug
        logger.debug(f"Resposta limpa da IA: {cleaned_response}") # Log para debug
        
        result_json = json.loads(cleaned_response)
        
        # Validação básica do JSON retornado (verificar chaves principais)
        required_keys = ["valuation_calculado", "metodologia_usada", "resumo_para_gamma", "prompt_gamma"]
        if not all(key in result_json for key in required_keys):
            raise ValueError("Resposta da IA não contém todas as chaves esperadas.")
            
        return result_json

    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON da resposta da IA: {e}\nResposta recebida: {cleaned_response}")
        return {
            "error": "Não foi possível processar a resposta da IA (formato inválido).",
            "valuation_calculado": None, # ... valores padrão/erro
        }
    except Exception as e:
        logger.error(f"Erro inesperado ao chamar a API Gemini: {e}")
        return {
            "error": f"Erro ao comunicar com a IA: {e}",
             "valuation_calculado": None, # ... valores padrão/erro
        }