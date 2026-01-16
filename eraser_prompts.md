# Prompts Eraser - Système de Recommandation d'Articles

## Prompt 1 : Architecture Actuelle

```
// Architecture Actuelle - Système de Recommandation d'Articles
// Type: Cloud Architecture Diagram

title Architecture Actuelle - Système de Recommandation

// === DATA SOURCES ===
Data Sources [icon: database, color: blue] {
  clicks.csv [icon: file-text, label: "Historique Clics"]
  articles_metadata.csv [icon: file-text, label: "Métadonnées Articles"]
  clicks_partitioned [icon: folder, label: "clicks/*.csv (partitionné par mois)"]
}

// === DATA PROCESSING LAYER ===
Data Processing [icon: cpu, color: purple] {
  Notebook Discovery [icon: book-open, label: "Notebook_discover_data.ipynb\nExploration & Statistiques"]
  Notebook Training [icon: brain, label: "Notebook_recommender_system.ipynb\nEntraînement ALS"]
  Serialize Script [icon: package, label: "serialize_artifacts.py\nSérialisation Modèle"]
}

// === ML MODEL ===
ML Model [icon: zap, color: orange] {
  ALS Algorithm [icon: grid, label: "ALS - Alternating Least Squares\nCollaborative Filtering\nfactors=50, iterations=15"]
  User Embeddings [icon: users, label: "User Factors\n(num_users × 50)"]
  Item Embeddings [icon: layers, label: "Item Factors\n(num_articles × 50)"]
  Popularity Fallback [icon: trending-up, label: "Top 5 Articles Populaires\n(Cold Start Users)"]
}

// === ARTIFACTS ===
Artifacts [icon: archive, color: green] {
  als_model.pkl [icon: file, label: "als_model.pkl\n~1-2 GB"]
  metadata.pkl [icon: file, label: "metadata.pkl\n~50-100 MB\nmappings + popularity"]
  csr_train.pkl [icon: file, label: "csr_train.pkl\n~2-3 GB\nMatrice Sparse CSR"]
}

// === AZURE INFRASTRUCTURE ===
Azure Cloud [icon: cloud, color: azure] {
  Resource Group [icon: folder, label: "rg-recommender"] {

    Blob Storage [icon: database, label: "Storage Account\nContainer: models"] {
      model_blob [icon: file, label: "als_model.pkl"]
      metadata_blob [icon: file, label: "metadata.pkl"]
      csr_blob [icon: file, label: "csr_train.pkl"]
    }

    Azure Function [icon: zap, label: "func-recommender\nPython 3.11\nConsumption Plan"] {
      HTTP Trigger [icon: globe, label: "POST /api/recommendarticle"]
      Blob Bindings [icon: link, label: "Input Bindings\n(Binary Pickle)"]
      Recommender Module [icon: cpu, label: "recommender.py\nGlobal Cache"]
    }

    App Insights [icon: activity, label: "Application Insights\nMonitoring & Logs"]
  }
}

// === CLIENT APPLICATIONS ===
Clients [icon: monitor, color: gray] {
  Streamlit App [icon: layout, label: "app.py\nDemo Interface\nPort 8501"]
  API Client [icon: terminal, label: "curl / requests\nHTTP Client"]
}

// === CI/CD ===
CI/CD [icon: git-branch, color: red] {
  GitHub Repo [icon: github, label: "Repository P10"]
  Deploy Workflow [icon: play, label: "azure-function-deploy.yml\nAuto-deploy on main"]
  Test Workflow [icon: check-circle, label: "azure-function-test.yml\nPR Validation"]
  Deploy Scripts [icon: terminal, label: "deploy_azure.sh\nredeploy_function.sh\nreupload_models.sh"]
}

// === CONNECTIONS ===

// Data Flow
clicks.csv --> Notebook Discovery
articles_metadata.csv --> Notebook Discovery
clicks_partitioned --> Notebook Discovery

Notebook Discovery --> Notebook Training
Notebook Training --> ALS Algorithm

ALS Algorithm --> User Embeddings
ALS Algorithm --> Item Embeddings
ALS Algorithm --> Popularity Fallback

Notebook Training --> Serialize Script
Serialize Script --> als_model.pkl
Serialize Script --> metadata.pkl
Serialize Script --> csr_train.pkl

// Deployment Flow
als_model.pkl --> model_blob: "Upload"
metadata.pkl --> metadata_blob: "Upload"
csr_train.pkl --> csr_blob: "Upload"

// Runtime Flow
model_blob --> Blob Bindings
metadata_blob --> Blob Bindings
csr_blob --> Blob Bindings

Blob Bindings --> Recommender Module
HTTP Trigger --> Recommender Module
Recommender Module --> HTTP Trigger: "JSON Response"

Azure Function --> App Insights: "Telemetry"

// Client Flow
Streamlit App --> HTTP Trigger: "POST user_id"
API Client --> HTTP Trigger: "POST user_id"

// CI/CD Flow
GitHub Repo --> Deploy Workflow
GitHub Repo --> Test Workflow
Deploy Workflow --> Azure Function: "Deploy"
Deploy Scripts --> Blob Storage: "Upload Models"
Deploy Scripts --> Azure Function: "Deploy Code"
```

---

## Prompt 2 : Architecture Cible (Gestion Cold Start)

```
// Architecture Cible - Système de Recommandation avec Gestion Cold Start
// Type: Cloud Architecture Diagram

title Architecture Cible - Recommandation Hybride avec Cold Start

// === DATA SOURCES ===
Data Sources [icon: database, color: blue] {
  clicks.csv [icon: file-text, label: "Historique Clics\n(existant)"]
  articles_metadata.csv [icon: file-text, label: "Métadonnées Articles\n(existant)"]
  article_content [icon: file-text, label: "Contenu Articles\n(NOUVEAU - texte, tags)"]
  user_profiles [icon: users, label: "Profils Utilisateurs\n(NOUVEAU - démographie, préférences)"]
}

// === REAL-TIME DATA INGESTION (NOUVEAU) ===
Real-Time Ingestion [icon: radio, color: cyan] {
  Event Hub [icon: activity, label: "Azure Event Hub\nFlux Clics Temps Réel"]
  Stream Analytics [icon: trending-up, label: "Azure Stream Analytics\nAgrégation Fenêtrée"]
  New User Detector [icon: user-plus, label: "Détecteur Nouveaux Users\nFirst-click trigger"]
  New Article Detector [icon: file-plus, label: "Détecteur Nouveaux Articles\nPublication trigger"]
}

// === FEATURE ENGINEERING (NOUVEAU) ===
Feature Engineering [icon: layers, color: purple] {

  Article Features [icon: file-text, label: "Features Articles"] {
    Text Embeddings [icon: type, label: "Sentence Transformers\nEmbeddings Texte 384D"]
    Category Encoding [icon: tag, label: "Category One-Hot\n+ Hierarchie"]
    Temporal Features [icon: clock, label: "Recency Score\nPublication Age"]
    Popularity Score [icon: trending-up, label: "Click Velocity\nTrending Score"]
  }

  User Features [icon: user, label: "Features Utilisateurs"] {
    Behavior Profile [icon: activity, label: "Profil Comportemental\nCategories préférées"]
    Session Context [icon: monitor, label: "Contexte Session\nDevice, Time, Location"]
    Engagement Metrics [icon: bar-chart, label: "Métriques Engagement\nCTR, Dwell Time"]
  }
}

// === HYBRID RECOMMENDATION ENGINE (NOUVEAU) ===
Hybrid Engine [icon: cpu, color: orange] {

  Collaborative Filtering [icon: users, label: "CF - ALS\n(existant)\nUsers similaires"] {
    ALS Model [icon: grid, label: "ALS factors=50\nMatrice Factorisation"]
    User Embeddings [icon: user, label: "User Vectors 50D"]
    Item Embeddings [icon: layers, label: "Item Vectors 50D"]
  }

  Content-Based [icon: file-text, label: "CBF - Content-Based\n(NOUVEAU)\nArticles similaires"] {
    Article Encoder [icon: type, label: "Article Encoder\nTransformers + Metadata"]
    Similarity Engine [icon: git-merge, label: "Cosine Similarity\nNearest Neighbors"]
    FAISS Index [icon: search, label: "FAISS Vector Index\nRecherche Rapide"]
  }

  Cold Start Handler [icon: thermometer, label: "Cold Start Manager\n(NOUVEAU)"] {

    New User Strategy [icon: user-plus, label: "Stratégie Nouveaux Users"] {
      Popularity Based [icon: trending-up, label: "1. Articles Populaires\n(fallback actuel)"]
      Category Exploration [icon: compass, label: "2. Exploration Catégories\nDiversité forcée"]
      Session Based [icon: clock, label: "3. Session-Based Reco\nClicks récents session"]
      MAB Exploration [icon: shuffle, label: "4. Multi-Armed Bandit\nExploration/Exploitation"]
    }

    New Article Strategy [icon: file-plus, label: "Stratégie Nouveaux Articles"] {
      Content Similarity [icon: git-merge, label: "1. Similarité Contenu\nArticles existants proches"]
      Category Boost [icon: arrow-up, label: "2. Boost Catégorie\nUsers intéressés catégorie"]
      Trending Injection [icon: zap, label: "3. Injection Trending\nExposition garantie"]
      A/B Testing [icon: shuffle, label: "4. A/B Test\nMesure engagement"]
    }
  }

  Ensemble Combiner [icon: git-merge, label: "Ensemble Combiner\n(NOUVEAU)"] {
    Weight Manager [icon: sliders, label: "Pondération Dynamique\nCF: 0.6 | CBF: 0.3 | Pop: 0.1"]
    Diversity Filter [icon: maximize, label: "Filtre Diversité\nMMR (Maximal Marginal Relevance)"]
    Business Rules [icon: shield, label: "Règles Métier\nFreshness, Publisher diversity"]
  }
}

// === MODEL TRAINING PIPELINE (AMÉLIORÉ) ===
Training Pipeline [icon: refresh-cw, color: green] {

  Batch Training [icon: database, label: "Batch Training\n(Quotidien)"] {
    ALS Retrain [icon: grid, label: "Réentraînement ALS\nIncrémental Update"]
    Embedding Update [icon: layers, label: "Mise à jour Embeddings\nArticles + Users"]
    Index Rebuild [icon: search, label: "Rebuild FAISS Index\nNouveaux articles"]
  }

  Online Learning [icon: radio, label: "Online Learning\n(Temps Réel - NOUVEAU)"] {
    Click Feedback [icon: mouse-pointer, label: "Feedback Clics\nImmediate reward signal"]
    Embedding Update [icon: refresh-cw, label: "Update Incrémental\nUser vectors légers"]
    Bandit Update [icon: shuffle, label: "MAB Reward Update\nArm statistics"]
  }

  Model Registry [icon: archive, label: "Model Registry\n(NOUVEAU)"] {
    Version Control [icon: git-branch, label: "Versioning Modèles\nMLflow / Azure ML"]
    A/B Variants [icon: shuffle, label: "Variantes A/B\nChampion/Challenger"]
    Rollback [icon: rotate-ccw, label: "Rollback Capability\nModèle précédent"]
  }
}

// === ARTIFACTS (ENRICHIS) ===
Artifacts [icon: archive, color: teal] {
  als_model.pkl [icon: file, label: "als_model.pkl\n(existant)"]
  metadata.pkl [icon: file, label: "metadata.pkl\n(existant + enrichi)"]
  csr_train.pkl [icon: file, label: "csr_train.pkl\n(existant)"]
  article_embeddings.pkl [icon: file, label: "article_embeddings.pkl\n(NOUVEAU - 384D)"]
  faiss_index.bin [icon: file, label: "faiss_index.bin\n(NOUVEAU)"]
  user_profiles.pkl [icon: file, label: "user_profiles.pkl\n(NOUVEAU)"]
  bandit_state.pkl [icon: file, label: "bandit_state.pkl\n(NOUVEAU - MAB state)"]
}

// === AZURE INFRASTRUCTURE (ÉTENDUE) ===
Azure Cloud [icon: cloud, color: azure] {
  Resource Group [icon: folder, label: "rg-recommender-v2"] {

    Blob Storage [icon: database, label: "Storage Account"] {
      models_container [icon: folder, label: "Container: models\nTous les artifacts"]
      embeddings_container [icon: folder, label: "Container: embeddings\nVecteurs articles"]
      cache_container [icon: folder, label: "Container: cache\nPré-calculs"]
    }

    Redis Cache [icon: database, label: "Azure Cache for Redis\n(NOUVEAU)"] {
      user_cache [icon: user, label: "Cache User Vectors\nTTL: 1 heure"]
      reco_cache [icon: list, label: "Cache Recommendations\nTTL: 15 min"]
      session_cache [icon: clock, label: "Cache Session\nClicks récents"]
    }

    Azure Functions [icon: zap, label: "Function App v2"] {

      Reco Function [icon: cpu, label: "RecommendArticle v2\nHybrid Engine"] {
        Cold Start Check [icon: thermometer, label: "Check Cold Start\nUser/Article"]
        Strategy Router [icon: git-branch, label: "Route Strategy\nCF/CBF/Hybrid"]
        Cache Layer [icon: database, label: "Redis Integration"]
      }

      Feedback Function [icon: mouse-pointer, label: "TrackClick\n(NOUVEAU)"] {
        Event Processor [icon: activity, label: "Process Click Event"]
        Bandit Updater [icon: shuffle, label: "Update MAB State"]
        Profile Updater [icon: user, label: "Update User Profile"]
      }

      Warmup Function [icon: sunrise, label: "WarmupModels\n(NOUVEAU)"] {
        Preload Models [icon: download, label: "Préchargement\nÉvite cold start Azure"]
        Timer Trigger [icon: clock, label: "Timer: every 5 min"]
      }
    }

    Azure ML [icon: brain, label: "Azure Machine Learning\n(NOUVEAU)"] {
      Training Pipeline [icon: git-branch, label: "Pipeline Entraînement\nScheduled daily"]
      Model Registry [icon: archive, label: "Registry Modèles\nVersioning"]
      Endpoints [icon: globe, label: "Managed Endpoints\nScaling auto"]
    }

    App Insights [icon: activity, label: "Application Insights\nMetrics enrichies"]

    Cosmos DB [icon: database, label: "Azure Cosmos DB\n(NOUVEAU)"] {
      user_interactions [icon: mouse-pointer, label: "Interactions Users\nHistorique complet"]
      article_metadata [icon: file-text, label: "Métadonnées Articles\nMises à jour temps réel"]
      recommendations_log [icon: list, label: "Log Recommendations\nA/B Testing data"]
    }
  }
}

// === MONITORING & EXPERIMENTATION (NOUVEAU) ===
Observability [icon: eye, color: red] {
  A/B Testing [icon: shuffle, label: "Plateforme A/B\nExperimentation"] {
    Variant Manager [icon: sliders, label: "Gestion Variantes\nTraffic splitting"]
    Metrics Collector [icon: bar-chart, label: "Collecte Métriques\nCTR, Engagement, Revenue"]
    Statistical Analysis [icon: trending-up, label: "Analyse Statistique\nSignificance testing"]
  }

  ML Monitoring [icon: activity, label: "ML Monitoring"] {
    Data Drift [icon: alert-triangle, label: "Détection Data Drift\nDistribution shift"]
    Model Performance [icon: bar-chart, label: "Performance Modèle\nPrecision/Recall temps réel"]
    Cold Start Metrics [icon: thermometer, label: "Métriques Cold Start\nTaux conversion nouveaux"]
  }

  Alerting [icon: bell, label: "Alerting"] {
    Latency Alerts [icon: clock, label: "Alertes Latence\np99 > 2s"]
    Error Rate [icon: alert-circle, label: "Taux d'Erreur\n> 1% threshold"]
    Cold Start Rate [icon: thermometer, label: "Taux Cold Start\nUsers/Articles"]
  }
}

// === CLIENT APPLICATIONS ===
Clients [icon: monitor, color: gray] {
  Streamlit App [icon: layout, label: "app.py v2\nInterface Enrichie"]
  Mobile SDK [icon: smartphone, label: "SDK Mobile\n(NOUVEAU)"]
  Web Widget [icon: code, label: "Widget JavaScript\n(NOUVEAU)"]
}

// === CONNECTIONS ===

// Real-time Data Flow
clicks.csv --> Event Hub: "Batch historique"
Event Hub --> Stream Analytics
Stream Analytics --> New User Detector
Stream Analytics --> New Article Detector
New User Detector --> Cold Start Handler
New Article Detector --> Cold Start Handler

// Feature Engineering
article_content --> Text Embeddings
articles_metadata.csv --> Category Encoding
articles_metadata.csv --> Temporal Features
Event Hub --> Popularity Score

user_profiles --> Behavior Profile
Event Hub --> Session Context
Event Hub --> Engagement Metrics

// Cold Start Flow
New User Strategy --> Ensemble Combiner
New Article Strategy --> Ensemble Combiner
Content Similarity --> FAISS Index

// Hybrid Engine Flow
ALS Model --> User Embeddings
ALS Model --> Item Embeddings
User Embeddings --> Ensemble Combiner
Item Embeddings --> Ensemble Combiner

Article Encoder --> FAISS Index
FAISS Index --> Similarity Engine
Similarity Engine --> Ensemble Combiner

Weight Manager --> Ensemble Combiner
Diversity Filter --> Ensemble Combiner
Business Rules --> Ensemble Combiner

// Training Flow
Batch Training --> als_model.pkl
Batch Training --> article_embeddings.pkl
Batch Training --> faiss_index.bin
Online Learning --> bandit_state.pkl
Online Learning --> user_profiles.pkl
Model Registry --> models_container

// Azure Infrastructure Flow
models_container --> Reco Function
embeddings_container --> Reco Function
Redis Cache --> Reco Function
Reco Function --> Redis Cache

Feedback Function --> Online Learning
Feedback Function --> Cosmos DB
Warmup Function --> Redis Cache

Azure ML --> Batch Training
Azure ML --> Model Registry

// Client Flow
Streamlit App --> Reco Function: "GET recommendations"
Mobile SDK --> Reco Function
Web Widget --> Reco Function
Streamlit App --> Feedback Function: "Track click"

// Monitoring Flow
Reco Function --> App Insights
Reco Function --> A/B Testing
Cosmos DB --> ML Monitoring
ML Monitoring --> Alerting
A/B Testing --> Statistical Analysis
```

---

## Notes d'Implémentation

### Différences Clés entre Architecture Actuelle et Cible

| Aspect | Actuelle | Cible |
|--------|----------|-------|
| **Nouveaux Users** | Top 5 populaires uniquement | Multi-stratégie (Popular → Category → Session → MAB) |
| **Nouveaux Articles** | Non géré (doit être dans training) | Content-based + Injection trending + A/B test |
| **Type Recommandation** | Collaborative Filtering pur | Hybride (CF + CBF + Rules) |
| **Mise à jour modèle** | Batch manuel | Batch quotidien + Online incremental |
| **Cache** | Global Python uniquement | Redis distribué + pré-calcul |
| **Cold Start Azure** | Accepté (3-5s) | Warmup Function (évité) |
| **Expérimentation** | Aucune | A/B Testing intégré |
| **Monitoring** | Basic (App Insights) | ML Monitoring + Drift Detection |

### Priorités d'Implémentation Suggérées

1. **Phase 1 - Quick Wins**
   - Content-based pour nouveaux articles (Sentence Transformers)
   - FAISS index pour recherche rapide
   - Redis cache pour recommendations

2. **Phase 2 - Cold Start Complet**
   - Multi-Armed Bandit pour exploration
   - Session-based recommendations
   - User profile enrichissement

3. **Phase 3 - Scaling & Monitoring**
   - Azure ML pipeline
   - A/B Testing framework
   - ML Monitoring complet
