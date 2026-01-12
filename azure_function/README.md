# Azure Function - RecommendArticle

Cette Azure Function expose une API HTTP pour obtenir des recommandations d'articles personnalisées pour un utilisateur donné.

## Architecture

```
azure_function/
├── RecommendArticle/
│   ├── __init__.py          # Code principal de la fonction
│   └── function.json        # Configuration des bindings
├── host.json                # Configuration globale
└── requirements.txt         # Dépendances Python
```

## Fonctionnement

### Chargement des Modèles

Les modèles sont chargés depuis **Azure Blob Storage** au démarrage de la fonction:
- `als_model.pkl`: Modèle ALS entraîné (user/item factors)
- `metadata.pkl`: Métadonnées (mappings user_id, article_id, etc.)
- `csr_train.pkl`: Matrice sparse CSR des interactions

**Configuration requise**:
```python
AzureWebJobsStorage = "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;"
```

### API Endpoint

**URL**: `https://func-recommender-XXXXXXXXXX.azurewebsites.net/api/recommendarticle`

**Méthodes**: GET, POST

**Paramètres**:
- `user_id` (int): ID de l'utilisateur

**Exemples**:
```bash
# Via Query Parameter (GET)
curl "https://func-recommender-XXXXXXXXXX.azurewebsites.net/api/recommendarticle?user_id=123&code=YOUR_FUNCTION_KEY"

# Via Body (POST)
curl -X POST "https://func-recommender-XXXXXXXXXX.azurewebsites.net/api/recommendarticle?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123}'
```

**Réponse**:
```json
{
  "user_id": 123,
  "recommendations": [293114, 3, 160974, 272143, 336221],
  "count": 5
}
```

**Codes d'erreur**:
- `400`: `user_id` manquant ou invalide
- `500`: Erreur serveur (chargement modèle, calcul recommandations)

## Algorithme de Recommandation

### 1. Utilisateurs Connus

Pour un utilisateur ayant déjà interagi avec des articles:
1. Calcul des scores de recommandation via ALS
2. Filtrage des articles déjà consultés
3. Retour des Top-5 articles

```python
# Scores = user_factors @ item_factors.T
scores = model.recommend(user_idx, csr_train[user_idx], N=5, filter_already_liked_items=True)
```

### 2. Nouveaux Utilisateurs (Cold Start)

Pour un utilisateur sans historique (user_id = 0 ou inconnu):
1. Fallback sur les articles les plus populaires
2. Basé sur le nombre total d'interactions

```python
# Articles les plus cliqués globalement
popular_articles = train_data['click_article_id'].value_counts().head(5)
```

## Configuration

### host.json

Configure les paramètres globaux de la Function App:
```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

### function.json

Configure les bindings de la fonction:
```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "function",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["get", "post"]
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    },
    {
      "name": "models",
      "type": "blob",
      "direction": "in",
      "path": "models",
      "connection": "AzureWebJobsStorage",
      "dataType": "binary"
    }
  ]
}
```

**Important**: `"dataType": "binary"` est crucial pour charger correctement les fichiers pickle.

## Déploiement

### Déploiement Manuel

```bash
# Depuis la racine du projet
cd azure_function

# Déployer
func azure functionapp publish func-recommender-XXXXXXXXXX --python
```

### Déploiement CI/CD (Automatique)

Le déploiement se fait automatiquement via GitHub Actions:
1. Push sur `main` avec modifications dans `azure_function/`
2. Le workflow `.github/workflows/azure-function-deploy.yml` se déclenche
3. Déploiement automatique en ~2 minutes

Voir [CI_CD_SETUP.md](../CI_CD_SETUP.md) pour plus de détails.

## Logs et Monitoring

### Voir les Logs en Temps Réel

```bash
# Via Azure CLI
func azure functionapp logstream func-recommender-XXXXXXXXXX --browser

# Ou via Portal Azure
# https://portal.azure.com → Function App → Log stream
```

### Application Insights

Les métriques sont automatiquement envoyées à Application Insights:
- Nombre d'exécutions
- Temps d'exécution
- Taux d'erreur
- Exceptions

**Voir les métriques**:
```bash
# Via Azure CLI
az monitor app-insights metrics show \
  --app func-recommender-insights \
  --resource-group rg-recommender \
  --metric "requests/count"
```

## Tests

### Test Local

```bash
# Démarrer localement
cd azure_function
func start

# Tester
curl "http://localhost:7071/api/recommendarticle?user_id=123"
```

### Test en Production

```bash
# Depuis la racine du projet
export AZURE_FUNCTION_KEY="votre_cle"
python3 test_function.py 123

# Ou
source set_api_key.sh
python3 test_function.py 123
```

## Dépendances

Voir `requirements.txt`:
- `azure-functions`: Framework Azure Functions
- `implicit`: Bibliothèque de Collaborative Filtering
- `numpy`: Calculs numériques
- `scipy`: Matrices sparse
- `pandas`: Manipulation de données (pour fallback)

**Note**: Les dépendances sont installées automatiquement lors du déploiement.

## Performance

### Métriques Observées

- **Cold Start**: ~3-5 secondes (première exécution)
- **Warm Start**: ~0.5-1 seconde (exécutions suivantes)
- **Mémoire utilisée**: ~512 MB
- **Coût par requête**: ~$0.0000068 (voir [AZURE_COSTS.md](../AZURE_COSTS.md))

### Optimisations Appliquées

1. **Chargement Global des Modèles**
   - Les modèles sont chargés une seule fois au démarrage
   - Réutilisés entre les exécutions (warm start)

2. **Format Pickle Optimisé**
   - Utilisation de `protocol=4` pour pickle
   - Chargement binaire direct depuis Blob Storage

3. **Matrice Sparse CSR**
   - Format efficace pour les données creuses
   - Multiplication matricielle optimisée

## Troubleshooting

### Erreur: "Blob not found"

**Cause**: Les modèles ne sont pas uploadés sur Blob Storage

**Solution**:
```bash
./reupload_models.sh
```

### Erreur: "UnpicklingError"

**Cause**: Les fichiers pickle sont corrompus ou en mauvais format

**Solution**:
```bash
# Re-sérialiser les modèles
python serialize_artifacts.py

# Re-uploader
./reupload_models.sh
```

### Erreur: "Object of type int64 is not JSON serializable"

**Cause**: NumPy int64 ne peut pas être sérialisé en JSON

**Solution** (déjà implémentée):
```python
# Convertir NumPy int64 en Python int
recommendations = [int(x) for x in article_ids]
```

### La fonction est lente

**Causes possibles**:
1. Cold start (première exécution)
2. Modèles trop gros
3. Temps de chargement depuis Blob Storage

**Solutions**:
- Activer Application Insights pour identifier le bottleneck
- Réduire la taille des modèles (quantification)
- Utiliser Premium Plan pour éliminer les cold starts

## Ressources

- [Documentation Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/)
- [Guide de Déploiement](../CI_CD_SETUP.md)
- [Analyse des Coûts](../AZURE_COSTS.md)
- [README Principal](../README.md)

---

**Dernière mise à jour**: 2026-01-12
