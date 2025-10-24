// static/js/chatbot.js
document.addEventListener('DOMContentLoaded', () => {
    const calculateBtn = document.getElementById('calculate-btn');
    const apiFeedback = document.getElementById('api-feedback');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatWindow = document.getElementById('chat-window');

    // --- Estado do Chat ---
    let currentQuestionIndex = 0;
    const questions = [
        { id: 'faturamento_anual', text: "Nos últimos 12 meses, qual foi o faturamento bruto aproximado da sua empresa?", type: 'number_positive' },
        { id: 'custos_operacionais_mensais', text: "Qual é a média mensal dos seus custos operacionais (sem impostos sobre lucro)?", type: 'number_non_negative' },
        { id: 'aliquota_imposto_lucro_perc', text: "Qual a alíquota média de impostos sobre o LUCRO (em %)? (Ex: 15, 25)", type: 'percentage' },
        { id: 'projecao_crescimento_anual_perc', text: "Qual sua expectativa de crescimento médio anual do faturamento (%) para os próximos 3-5 anos?", type: 'number' }, // Pode ser negativo
        { id: 'setor_atuacao', text: "Em qual setor principal sua empresa atua? (Ex: Varejo, Tecnologia, Serviços)", type: 'text' },
        { id: 'tempo_operacao_anos', text: "Há quantos anos a sua empresa está em operação?", type: 'integer_non_negative' },
        { id: 'diferencial_competitivo', text: "Qual você considera o maior diferencial ou vantagem competitiva do seu negócio?", type: 'text' }
    ];
    const chatInputs = {}; // Respostas serão armazenadas aqui

    // --- Funções Auxiliares ---
    function addChatMessage(message, type = 'bot') {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${type}`;
        // Para evitar injeção de HTML simples, usamos textContent
        // Para mensagens complexas, você precisaria sanitizar
        msgDiv.textContent = message;
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll
    }

    function disableInput() {
        chatInput.disabled = true;
        chatSendBtn.disabled = true;
    }

    function enableInput(placeholder = "Digite sua resposta aqui...") {
        chatInput.disabled = false;
        chatSendBtn.disabled = false;
        chatInput.placeholder = placeholder;
        chatInput.focus();
    }

    function askQuestion() {
        if (currentQuestionIndex < questions.length) {
            const question = questions[currentQuestionIndex];
            addChatMessage(question.text);
            enableInput();
        } else {
            // Fim das perguntas
            addChatMessage("Excelente! Coletei todos os dados. Agora, por favor, clique no botão \"Calcular Valuation\" ao lado.");
            disableInput();
            calculateBtn.disabled = false; // Ativa o botão de calcular
        }
    }

    // --- Funções de Validação ---
    function validateInput(input, type) {
        let value = input.trim();
        let num;

        switch (type) {
            case 'number': // Qualquer número
                num = parseFloat(value.replace(',', '.'));
                return !isNaN(num) ? num : { error: "Por favor, insira um valor numérico válido." };
            case 'number_positive': // Número > 0
                num = parseFloat(value.replace(',', '.'));
                return !isNaN(num) && num > 0 ? num : { error: "Por favor, insira um número positivo maior que zero." };
            case 'number_non_negative': // Número >= 0
                num = parseFloat(value.replace(',', '.'));
                return !isNaN(num) && num >= 0 ? num : { error: "Por favor, insira um número válido (zero ou maior)." };
            case 'percentage': // Número entre 0 e 100
                num = parseFloat(value.replace(',', '.'));
                return !isNaN(num) && num >= 0 && num <= 100 ? num : { error: "Por favor, insira um percentual válido entre 0 e 100." };
            case 'integer_non_negative': // Inteiro >= 0
                if (!/^\d+$/.test(value)) {
                    return { error: "Por favor, insira um número inteiro (sem decimais)." };
                }
                num = parseInt(value, 10);
                return num >= 0 ? num : { error: "Por favor, insira um número inteiro positivo ou zero." }; // Redundante com regex, mas seguro
            case 'text': // Texto não vazio
                return value.length > 0 ? value : { error: "Esta resposta não pode ficar em branco." };
            default:
                return value; // Sem validação específica
        }
    }

    // --- Lógica Principal do Chat ---
    function handleChatSend() {
        const message = chatInput.value;
        if (message.trim() === '' || currentQuestionIndex >= questions.length) return;

        addChatMessage(message, 'user');
        chatInput.value = ''; // Limpa o input imediatamente

        const currentQuestion = questions[currentQuestionIndex];
        const validationResult = validateInput(message, currentQuestion.type);

        if (validationResult && typeof validationResult === 'object' && validationResult.error) {
            // Erro de validação
            addChatMessage(validationResult.error);
            enableInput(); // Permite tentar novamente
        } else {
            // Sucesso na validação
            chatInputs[currentQuestion.id] = validationResult; // Armazena o valor validado/convertido
            currentQuestionIndex++;
            disableInput(); // Desabilita enquanto pensa na próxima pergunta
            setTimeout(askQuestion, 500); // Pequeno delay para simular pensamento
        }
    }

    chatSendBtn.addEventListener('click', handleChatSend);
    chatInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            handleChatSend();
        }
    });

    // --- Lógica da API ---
    calculateBtn.addEventListener('click', () => {
        calculateBtn.disabled = true;
        calculateBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processando...`;
        apiFeedback.innerHTML = '<div class="alert alert-info small">Iniciando análise... Isso pode levar algum tempo.</div>';

        fetch('/chatbot/api/calculate/', { // URL da sua API Django
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Se CSRF_exempt não estiver ativo na view, adicione o token:
                // 'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ inputs: chatInputs })
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status === 200) {
                apiFeedback.innerHTML = `<div class="alert alert-success"><strong>Sucesso!</strong> ${body.message} O resultado aparecerá no seu histórico.</div>`;
                // Poderia resetar o chat aqui para um novo cálculo
                // currentQuestionIndex = 0;
                // chatInputs = {};
                // chatWindow.innerHTML = ''; // Limpa a janela
                // askQuestion(); // Pergunta a primeira de novo
                // Mas por enquanto, apenas reabilita o botão
                calculateBtn.disabled = false; // Ou mantenha desabilitado até resetar
                calculateBtn.innerHTML = '<i class="bi bi-calculator-fill me-2"></i> Calcular Novamente (Recarregue)';
            } else {
                throw new Error(body.message || `Erro ${status}`);
            }
        })
        .catch(error => {
            console.error('Erro na API:', error);
            apiFeedback.innerHTML = `<div class="alert alert-danger"><strong>Erro:</strong> ${error.message}</div>`;
            calculateBtn.disabled = false; // Permite tentar novamente
            calculateBtn.innerHTML = '<i class="bi bi-x-octagon-fill me-2"></i> Falha! Tentar Calcular Novamente';
        });
    });

    // Função para pegar Cookie (se necessário)
    function getCookie(name) { /* ... (código da função getCookie) ... */ }

    // --- Iniciar o Chat ---
    calculateBtn.disabled = true; // Começa desabilitado
    askQuestion(); // Faz a primeira pergunta

});