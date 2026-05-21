# Image Python officielle
FROM python:3.12

# Dossier de travail dans le conteneur
WORKDIR /app

# Copie et installation des dépendances
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copie des scripts
COPY migrate.py .
COPY test_migration.py .