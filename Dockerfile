# Dockerfile

# 1. Imagem base do Python
FROM python:3.11-slim

# 2. Variáveis de Ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Instala dependências do sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# 4. Cria o diretório de trabalho
WORKDIR /app

# 5. Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copia o código do projeto
COPY . .

# 7. (Opcional) Usuário não-root por segurança
RUN addgroup --system app && adduser --system --group app
RUN chown -R app:app /app
USER app

# 8. Define o comando padrão para iniciar o container (Gunicorn for web)
# CORRIGIDO para usar sh -c e interpretar $PORT
CMD ["sh", "-c", "gunicorn valuation.wsgi:application --bind 0.0.0.0:${PORT}"]