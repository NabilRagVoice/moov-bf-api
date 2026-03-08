# 🇧🇫 Moov BF API

API complète pour la gestion des accords et offres Moov Burkina Faso.

## 📋 Fonctionnalités

- **Accords Haut Débit** : Gestion des accords FAI avec localisation GPS
- **Accords Mobile** : Gestion des accords opérateur mobile
- **Accords Moov Money** : Gestion des accords microfinance/mobile money
- **Offres** : Catalogue flexible des offres (tous types)
- **Documents** : Stockage CNI et photos d'identité

## 🏗️ Architecture

- **API** : Flask (Python)
- **Base de données** : Azure CosmosDB (NoSQL)
- **Stockage** : Azure Blob Storage
- **Déploiement** : Azure Container Apps

## 🚀 Installation locale

```bash
# Cloner le repo
git clone https://github.com/NabilRagVoice/moov-bf-api.git
cd moov-bf-api

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos credentials

# Lancer l'API
python app.py
```

## 📚 Documentation API

Une fois l'API lancée, accédez à :
- Health check : `GET /api/health`
- Documentation : `GET /api/docs`

## 🔐 Authentification

Toutes les routes (sauf `/api/health`) nécessitent une API Key dans le header :
```
X-API-Key: votre-cle-api
```

## 📁 Structure du projet

```
moov-bf-api/
├── app.py                 # Point d'entrée Flask
├── config.py              # Configuration
├── requirements.txt       # Dépendances Python
├── Dockerfile             # Image Docker
├── .env.example           # Template variables d'environnement
├── routes/
│   ├── __init__.py
│   ├── accords_haut_debit.py
│   ├── accords_mobile.py
│   ├── accords_moov_money.py
│   ├── offres.py
│   ├── documents.py
│   └── admin.py
├── services/
│   ├── __init__.py
│   ├── cosmos_service.py
│   └── storage_service.py
└── utils/
    ├── __init__.py
    ├── auth.py
    └── helpers.py
```

## 📄 License

Propriétaire - Moov Burkina Faso
