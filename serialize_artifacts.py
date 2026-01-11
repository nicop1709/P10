"""
Script de sérialisation des artefacts pour le système de recommandation
À exécuter après l'entraînement du modèle dans le notebook
"""

import pickle
import numpy as np
from pathlib import Path
import pandas as pd
from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares
from sklearn.model_selection import train_test_split

def load_data():
    """Charge les données nécessaires"""
    # Load articles' metadata
    articles = pd.read_csv('articles_metadata.csv')
    articles.drop(columns=['publisher_id'], inplace=True)
    articles = articles.astype(np.int64)

    # Load clicks
    clicks_list = []
    for file in sorted(Path("clicks/").glob("*.csv")):
        clicks_list.append(pd.read_csv(file))
    clicks = pd.concat(clicks_list, ignore_index=True)
    clicks.rename(columns={'click_article_id':'article_id'}, inplace=True)
    clicks.drop(columns=['click_environment', 'click_deviceGroup', 'click_os', 
                        'click_country', 'click_region', 'click_referrer_type'], inplace=True)
    clicks = clicks.astype(np.int64)
    
    return articles, clicks

def create_sparse_matrix(interactions_df):
    """Crée une matrice sparse CSR (user_id, article_id)"""
    unique_users = sorted(interactions_df['user_id'].unique())
    unique_items = sorted(interactions_df['article_id'].unique())
    
    user_to_idx = {uid: idx for idx, uid in enumerate(unique_users)}
    item_to_idx = {iid: idx for idx, iid in enumerate(unique_items)}
    
    user_indices = [user_to_idx[uid] for uid in interactions_df['user_id']]
    item_indices = [item_to_idx[iid] for iid in interactions_df['article_id']]
    values = interactions_df['count'].values.astype(np.float32)
    
    csr_matrix_train = csr_matrix((values, (user_indices, item_indices)), 
                                   shape=(len(unique_users), len(unique_items)))
    
    return csr_matrix_train, user_to_idx, item_to_idx, unique_users, unique_items

def serialize_artifacts():
    """Sérialise tous les artefacts nécessaires pour la production"""
    print("=== SÉRIALISATION DES ARTEFACTS ===")
    
    # 1. Charger les données
    print("\n1. Chargement des données...")
    articles, clicks = load_data()
    
    # 2. Créer les interactions
    print("2. Création des interactions...")
    interactions = clicks.groupby(['user_id', 'article_id']).size().reset_index(name='count')
    
    # 3. Séparer train/test (on utilise seulement le train pour le modèle final)
    print("3. Séparation train/test...")
    train_interactions, _ = train_test_split(
        interactions, 
        test_size=0.2, 
        random_state=42,
        stratify=interactions['user_id']
    )
    
    # 4. Créer la matrice sparse et les mappings
    print("4. Création de la matrice sparse...")
    csr_train, user_to_idx, item_to_idx, unique_users, unique_items = create_sparse_matrix(train_interactions)
    
    print(f"   Matrice shape: {csr_train.shape}")
    print(f"   Utilisateurs: {len(unique_users):,}")
    print(f"   Articles: {len(unique_items):,}")
    
    # 5. Entraîner le modèle ALS
    print("\n5. Entraînement du modèle ALS...")
    als_model = AlternatingLeastSquares(factors=50, iterations=15, random_state=42, num_threads=4)
    als_model.fit(csr_train)
    print("   ✅ Modèle entraîné")
    
    # 6. Calculer les articles populaires (fallback)
    print("\n6. Calcul des articles populaires (fallback)...")
    popularity_recommendations = train_interactions.groupby('article_id')['count'].sum().sort_values(ascending=False).head(5).index.tolist()
    print(f"   Top 5 articles: {popularity_recommendations}")
    
    # 7. Sérialiser tous les artefacts
    print("\n7. Sérialisation des artefacts...")
    artifacts = {
        'als_model': als_model,
        'csr_train': csr_train,
        'user_to_idx': user_to_idx,
        'item_to_idx': item_to_idx,
        'unique_users': unique_users,
        'unique_items': unique_items,
        'popularity_recommendations': popularity_recommendations
    }
    
    output_path = 'artifacts.pkl'
    with open(output_path, 'wb') as f:
        pickle.dump(artifacts, f)
    
    # Afficher la taille du fichier
    file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB
    print(f"   ✅ Artefacts sauvegardés dans '{output_path}' ({file_size:.2f} MB)")
    
    # 8. Sérialiser aussi séparément pour faciliter le chargement
    print("\n8. Sauvegarde séparée des composants...")
    
    # Modèle ALS
    with open('als_model.pkl', 'wb') as f:
        pickle.dump(als_model, f)
    print(f"   ✅ Modèle ALS: {Path('als_model.pkl').stat().st_size / (1024 * 1024):.2f} MB")
    
    # Mappings et metadata (plus petits)
    metadata = {
        'user_to_idx': user_to_idx,
        'item_to_idx': item_to_idx,
        'unique_users': unique_users,
        'unique_items': unique_items,
        'popularity_recommendations': popularity_recommendations
    }
    with open('metadata.pkl', 'wb') as f:
        pickle.dump(metadata, f)
    print(f"   ✅ Metadata: {Path('metadata.pkl').stat().st_size / (1024 * 1024):.2f} MB")
    
    # Matrice CSR (peut être gros)
    with open('csr_train.pkl', 'wb') as f:
        pickle.dump(csr_train, f)
    print(f"   ✅ Matrice CSR: {Path('csr_train.pkl').stat().st_size / (1024 * 1024):.2f} MB")
    
    print("\n=== SÉRIALISATION TERMINÉE ===")
    print("\nFichiers créés:")
    print("  - artifacts.pkl (tout en un)")
    print("  - als_model.pkl (modèle seul)")
    print("  - metadata.pkl (mappings et fallback)")
    print("  - csr_train.pkl (matrice sparse)")
    
    return artifacts

if __name__ == "__main__":
    artifacts = serialize_artifacts()

