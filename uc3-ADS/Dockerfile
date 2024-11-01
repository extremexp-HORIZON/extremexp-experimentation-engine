# Utiliser l'image de base Python
FROM python:3.9

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires dans le conteneur
COPY . /app

# Installer les dépendances
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Exposer le port sur lequel l'application écoute
EXPOSE 8081

# Commande pour exécuter l'application
CMD ["python", "MainWorkflow.py"]