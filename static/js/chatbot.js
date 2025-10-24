// static/js/chatbot.js

document.addEventListener('DOMContentLoaded', () => {

    const calculateBtn = document.getElementById('calculate-btn');
    const apiFeedback = document.getElementById('api-feedback');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatWindow = document.getElementById('chat-window');

    // Objeto para armazenar as respostas do usuário
    const chatInputs = {
        "faturamento_anual": null,
        "custos_anuais": null,
        "crescimento_esperado": null
        // Adicione mais perguntas conforme sua IA precisar
    };

    // --- Lógica do Chat (Simples) ---
    // Em um projeto real, isso seria uma máquina de estados mais complexa
    
    chatSendBtn.addEventListener('click', handleChatSend);
    chatInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            handleChatSend();
        }
    });

    function handleChatSend() {
        const message = chatInput.value;
        if (message.trim() === '') return;

        // Adiciona a mensagem do usuário à janela
        addChatMessage(message, 'user');
        chatInput.value = '';

        // Lógica de perguntas (placeholder)
        // Você deve criar uma lógica de "qual é a próxima pergunta?"
        if (chatInputs.faturamento_anual === null) {
            chatInputs.faturamento_anual = parseFloat(message);
            addChatMessage('Entendido. E quais são os seus custos anuais (incluindo impostos, salários, etc.)?', 'bot');
        } else if (chatInputs.custos_anuais === null) {
            chatInputs.custos_anuais = parseFloat(message);
            addChatMessage('Ótimo. Por último, qual é a taxa de crescimento esperada para os próximos 5 anos (em %)?', 'bot');
        } else if (chatInputs.crescimento_esperado === null) {
            chatInputs.crescimento_esperado = parseFloat(message);
            addChatMessage('Excelente! Coletei todos os dados. Agora, por favor, clique no botão "Calcular Valuation" ao lado.', 'bot');
            calculateBtn.disabled = false; // Ativa o botão
            calculateBtn.classList.remove('btn-secondary');
            calculateBtn.classList.add('btn-primary');
        }
    }

    function addChatMessage(message, type) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${type}`;
        msgDiv.textContent = message;
        chatWindow.appendChild(msgDiv);
        // Rola para a última mensagem
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }


    // --- Lógica da API (O mais importante) ---
    
    calculateBtn.addEventListener('click', () => {
        
        // 1. Mostrar estado de "Carregando"
        calculateBtn.disabled = true;
        calculateBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            Processando...
        `;
        apiFeedback.innerHTML = '<div class="alert alert-info small">Iniciando análise... Isso pode levar até 60 segundos.</div>';
        
        // 2. Enviar os dados para a API do Django
        fetch('/chatbot/api/calculate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // O 'X-CSRFToken' é necessário se você NÃO usar @csrf_exempt
                // 'X-CSRFToken': getCookie('csrftoken') 
            },
            body: JSON.stringify({ inputs: chatInputs })
        })
        .then(response => {
            // A API do Django responde com um JSON
            return response.json().then(data => ({ status: response.status, body: data }));
        })
        .then(({ status, body }) => {
            
            if (status === 200) {
                // Sucesso! A tarefa foi enfileirada
                apiFeedback.innerHTML = `
                    <div class="alert alert-success">
                        <strong>Sucesso!</strong> ${body.message}
                        <br>
                        O resultado aparecerá no seu histórico em breve.
                    </div>`;
                // Reseta o botão
                calculateBtn.disabled = false;
                calculateBtn.innerHTML = '<i class="bi bi-calculator-fill me-2"></i> Calcular Novamente';
                
                // Limpa o chat para um novo cálculo
                // ...
                
            } else {
                // Erro (Ex: Limite de uso, 403 Forbidden)
                throw new Error(body.message || 'Ocorreu um erro.');
            }
        })
        .catch(error => {
            // Erro de rede ou erro lançado acima
            console.error('Erro na API:', error);
            apiFeedback.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Erro:</strong> ${error.message}
                </div>`;
            calculateBtn.disabled = false;
            calculateBtn.innerHTML = '<i class="bi bi-calculator-fill me-2"></i> Tentar Calcular Novamente';
        });
    });

    // Função para pegar o cookie CSRF (se você precisar)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});