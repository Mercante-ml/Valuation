// static/js/theme-toggle.js
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle-switch');
    const themeLabel = document.getElementById('theme-toggle-label');
    const htmlEl = document.documentElement;

    // Função para definir o tema (e atualizar o switch)
    function setTheme(theme) {
        if (theme === 'dark') {
            htmlEl.setAttribute('data-bs-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            if (themeToggle) {
                themeToggle.checked = true;
                themeLabel.textContent = 'Modo Escuro Ativado';
            }
        } else {
            htmlEl.setAttribute('data-bs-theme', 'light');
            localStorage.setItem('theme', 'light');
            if (themeToggle) {
                themeToggle.checked = false;
                themeLabel.textContent = 'Ativar Modo Escuro (Dark Mode)';
            }
        }
    }

    // Verifica o tema salvo quando o switch é carregado
    const currentTheme = localStorage.getItem('theme') || 'light';
    setTheme(currentTheme);

    // Adiciona o 'listener' ao switch
    if (themeToggle) {
        themeToggle.addEventListener('change', () => {
            if (themeToggle.checked) {
                setTheme('dark');
            } else {
                setTheme('light');
            }
        });
    }
});