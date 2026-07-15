# Image Python officielle
FROM python:3.12

# Dossier de travail dans le conteneur
WORKDIR /app

# Copie et installation des dépendances
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copie des scripts
COPY init_mongo.py .
COPY migrate.py .
COPY clean_csv.py .
COPY test_before_migration.py .
COPY test_after_migration.py .