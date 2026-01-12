# Système de Recommandation d'Articles

![Deploy Status](https://github.com/nicop1709/P10/actions/workflows/azure-function-deploy.yml/badge.svg)
![Test Status](https://github.com/nicop1709/P10/actions/workflows/azure-function-test.yml/badge.svg)

Projet de recommandation d'articles basé sur le Collaborative Filtering avec l'algorithme ALS (Alternating Least Squares).

Ce système analyse les interactions utilisateurs-articles pour fournir des recommandations personnalisées, déployé sur Azure Functions et accessible via une application web Streamlit.

## Architecture du Projet

```
P10/
├── app.py                          # Application Streamlit (démo)
├── run_app.sh                      # Script de lancement de l'app
├── recommender.py                  # Classe Recommender
├── serialize_artifacts.py          # Sérialisation des modèles
├── requirements.txt                # Dépendances Python
│
├── notebooks/
│   ├── Notebook_discover_data.ipynb       # Exploration des données
│   └── Notebook_recommender_system.ipynb  # Training du modèle
│
├── azure_function/
│   ├── RecommendArticle/
│   │   ├── __init__.py            # Code de l'Azure Function
│   │   └── function.json          # Configuration des bindings
│   ├── host.json                  # Configuration globale
│   └── requirements.txt           # Dépendances Azure Function
│
├── scripts/
│   ├── deploy_azure.sh            # Déploiement complet sur Azure
│   ├── redeploy_function.sh       # Redéploiement de la fonction
│   ├── reupload_models.sh         # Re-upload des modèles
│   └── test_function.py           # Tests de l'API
│
├── data/
│   ├── clicks/                    # Données de clics (partitionnées)
│   ├── clicks.csv                 # Dataset complet
│   └── articles_metadata.csv      # Métadonnées des articles
│
└── models/ (générés)
    ├── als_model.pkl              # Modèle ALS entraîné
    ├── metadata.pkl               # Métadonnées (mappings, etc.)
    └── csr_train.pkl              # Matrice sparse CSR
```

## Installation

### Prérequis

- Python 3.11 ou supérieur
- Azure CLI (pour le déploiement)
- Azure Functions Core Tools (pour le test local)
- Compte Azure (pour le déploiement)

### Installation des dépendances

```bash
# Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

### 1. Entraînement du Modèle

Le modèle a déjà été entraîné. Pour ré-entraîner ou explorer les données:

```bash
# Ouvrir les notebooks Jupyter
jupyter notebook
```

Notebooks disponibles:
- `Notebook_discover_data.ipynb`: Exploration et analyse des données
- `Notebook_recommender_system.ipynb`: Entraînement du modèle ALS

### 2. Configuration de la Clé d'API

L'Azure Function nécessite une clé d'authentification. La clé est déjà configurée dans `app.py`, mais si vous devez la mettre à jour:

```bash
# Récupérer la clé depuis Azure
az functionapp keys list --name func-recommender-1768155564 --resource-group rg-recommender --query "functionKeys.default" -o tsv

# Ou utiliser le script fourni
source ./set_api_key.sh
```

Pour les tests via scripts Python:
```bash
# Option 1: Exporter la clé
export AZURE_FUNCTION_KEY='votre_cle'

# Option 2: Utiliser le script
source ./set_api_key.sh

# Puis tester
python3 test_function.py 0
```

### 3. Application Streamlit (Démo Locale)

Pour lancer l'application de démonstration:

```bash
# Option 1: Script de lancement
./run_app.sh

# Option 2: Commande directe
streamlit run app.py
```

L'application sera accessible sur: http://localhost:8501

**Note**: La clé d'API est déjà configurée dans le code de l'application.

**Fonctionnalités:**
- Sélection d'un utilisateur par ID
- Récupération des 5 recommandations via l'Azure Function
- Affichage des métadonnées des articles recommandés
- Mesure du temps de réponse
- **Calcul du coût Azure par requête** avec projections
- Détails de la tarification Consumption Plan

### 4. Test de l'Azure Function

Pour tester l'API Azure déployée:

```bash
# Configurer la clé d'API
export AZURE_FUNCTION_KEY='votre_cle'
# ou
source ./set_api_key.sh

# Test simple
python3 test_function.py <user_id>

# Test avec analyse détaillée
python3 test_and_analyze.py <user_id>

# Exemple
python3 test_function.py 0
```

## Déploiement sur Azure

### Déploiement Initial (Première fois seulement)

```bash
# 1. Se connecter à Azure
az login

# 2. Exécuter le script de déploiement complet
./deploy_azure.sh
```

Ce script va:
1. Créer le Resource Group
2. Créer le Storage Account
3. Créer le conteneur `models`
4. Uploader les modèles (als_model.pkl, metadata.pkl, csr_train.pkl)
5. Créer la Function App
6. Déployer le code de la fonction

### CI/CD - Déploiement Automatique (Recommandé)

Le projet est configuré pour le déploiement automatique via **GitHub Actions**.

**Configuration initiale (une seule fois)**:
```bash
# Configurer automatiquement les secrets GitHub
./setup_github_secrets.sh
```

**Utilisation quotidienne**:
```bash
# Modifier le code de la fonction
vim azure_function/RecommendArticle/__init__.py

# Commit et push sur main
git add azure_function/
git commit -m "Update recommendation logic"
git push origin main

# ✨ Le déploiement se fait automatiquement!
# Voir les logs: https://github.com/YOUR_REPO/actions
```

**Workflows disponibles**:
- `.github/workflows/azure-function-deploy.yml` - Déploiement auto (push sur main)
- `.github/workflows/azure-function-test.yml` - Tests seuls (Pull Requests)

Pour plus de détails, consultez [CI_CD_SETUP.md](CI_CD_SETUP.md).

### Redéploiement Manuel (Si nécessaire)

```bash
# Redéployer uniquement la fonction (sans CI/CD)
./redeploy_function.sh
```

### Re-upload des Modèles

Si vous avez ré-entraîné le modèle:

```bash
# 1. Sérialiser les nouveaux modèles
python serialize_artifacts.py

# 2. Re-upload sur Azure Blob Storage
./reupload_models.sh

# 3. Redémarrer la Function App
az functionapp restart --name func-recommender-XXXXXXXXXX --resource-group rg-recommender
```

## API Azure Function

### Endpoint

```
POST https://func-recommender-XXXXXXXXXX.azurewebsites.net/api/recommendarticle
```

### Requête

**Body (JSON):**
```json
{
  "user_id": 123
}
```

**Ou Query Parameter:**
```
GET ?user_id=123
```

### Réponse

```json
{
  "user_id": 123,
  "recommendations": [293114, 3, 160974, 272143, 336221],
  "count": 5
}
```

### Codes d'erreur

- `400`: `user_id` manquant ou invalide
- `500`: Erreur serveur (chargement du modèle, etc.)

## Modèle de Recommandation

### Algorithme: ALS (Alternating Least Squares)

Le système utilise l'algorithme ALS de la bibliothèque `implicit` pour le Collaborative Filtering.

**Caractéristiques:**
- Matrice sparse utilisateur-article (CSR format)
- Filtrage des articles déjà consultés
- Fallback sur les articles populaires pour les nouveaux utilisateurs

### Métriques du Modèle

Consultez le notebook `Notebook_recommender_system.ipynb` pour les métriques d'évaluation:
- Precision@K
- Recall@K
- MAP (Mean Average Precision)

## Structure des Données

### Fichier: `clicks.csv`

Données d'interactions utilisateurs-articles:
- `user_id`: ID de l'utilisateur
- `click_article_id`: ID de l'article cliqué
- `click_timestamp`: Timestamp du clic

### Fichier: `articles_metadata.csv`

Métadonnées des articles:
- `article_id`: ID de l'article
- `category_id`: Catégorie de l'article
- `created_at_ts`: Date de création
- `publisher_id`: ID de l'éditeur
- `words_count`: Nombre de mots

## Scripts Utiles

| Script | Description |
|--------|-------------|
| `run_app.sh` | Lance l'application Streamlit |
| `deploy_azure.sh` | Déploiement complet sur Azure |
| `redeploy_function.sh` | Redéploie la fonction Azure |
| `reupload_models.sh` | Re-upload les modèles pickle |
| `test_function.py` | Test simple de l'API |
| `test_and_analyze.py` | Test avec analyse détaillée |
| `serialize_artifacts.py` | Sérialise les modèles |
| `check_function_logs.py` | Récupère les logs Azure |

## Résolution de Problèmes

### Erreur: `UnpicklingError`

Si vous rencontrez une erreur de pickle:

```bash
# Re-upload les modèles en mode binaire
./reupload_models.sh

# Redémarrer la Function App
az functionapp restart --name func-recommender-XXXXXXXXXX --resource-group rg-recommender
```

### Erreur: `Object of type int64 is not JSON serializable`

Cette erreur est déjà corrigée dans le code (conversion NumPy → Python int).

### Logs Azure

```bash
# Voir les logs en temps réel
func azure functionapp logstream func-recommender-XXXXXXXXXX --browser

# Ou via script Python
python3 get_function_logs.py
```

## Coûts d'Exploitation

### Estimation des coûts Azure

Le système utilise Azure Functions en mode **Consumption (Serverless)**:

- **Coût par requête**: ~$0.000025 (25 micro-dollars)
- **Offre gratuite**: 1 million de requêtes/mois
- **100 requêtes/jour**: $0/mois (gratuit)
- **10,000 requêtes/jour**: ~$0.86/mois
- **100,000 requêtes/jour**: ~$67/mois

Pour plus de détails, consultez [AZURE_COSTS.md](AZURE_COSTS.md).

## Documentation Complémentaire

Consultez les fichiers suivants pour plus de détails:

- `AZURE_COSTS.md`: Analyse détaillée des coûts Azure
- `DEPLOYMENT.md`: Guide de déploiement détaillé
- `GUIDE_DEPLOIEMENT_AZURE.md`: Instructions Azure complètes
- `SOLUTION_UNPICKLING_ERROR.md`: Résolution des erreurs pickle
- `azure_function/README.md`: Documentation de l'Azure Function

## Technologies Utilisées

- **Python 3.11**: Langage principal
- **Implicit**: Bibliothèque Collaborative Filtering
- **Streamlit**: Application web de démo
- **Azure Functions**: Hébergement de l'API
- **Azure Blob Storage**: Stockage des modèles
- **Pandas/NumPy**: Manipulation des données
- **Scikit-learn**: Preprocessing et métriques

## Auteur

Projet P10 - OpenClassrooms Ingénieur IA

## Licence

Ce projet est développé dans le cadre d'une formation OpenClassrooms.

---

**Note**: Remplacez `XXXXXXXXXX` par l'ID unique de votre Function App Azure dans les commandes ci-dessus.
