FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta Streamlit
EXPOSE 8501

# Rodar Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
