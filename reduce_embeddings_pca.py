"""
Script optionnel pour réduire la dimensionnalité des embeddings avec PCA
Utile si le fichier articles_embeddings.pickle est trop volumineux
"""

import pickle
import numpy as np
from sklearn.decomposition import PCA
from pathlib import Path

def reduce_embeddings_pca(input_path='articles_embeddings.pickle', 
                          output_path='articles_embeddings_reduced.pickle',
                          n_components=50,
                          explained_variance_threshold=0.95):
    """
    Réduit la dimensionnalité des embeddings avec PCA
    
    Args:
        input_path: Chemin vers le fichier embeddings original
        output_path: Chemin de sortie pour les embeddings réduits
        n_components: Nombre de composantes principales (si None, utilise explained_variance_threshold)
        explained_variance_threshold: Variance expliquée minimale (si n_components=None)
    """
    print("=== RÉDUCTION DES EMBEDDINGS AVEC PCA ===")
    
    # 1. Charger les embeddings originaux
    print(f"\n1. Chargement des embeddings depuis '{input_path}'...")
    with open(input_path, 'rb') as f:
        embeddings = pickle.load(f)
    
    embeddings = np.array(embeddings).astype(np.float32)
    original_shape = embeddings.shape
    print(f"   Shape original: {original_shape}")
    print(f"   Taille mémoire: {embeddings.nbytes / (1024**2):.2f} MB")
    
    # 2. Appliquer PCA
    print(f"\n2. Application de PCA...")
    if n_components is None:
        # Utiliser explained_variance_threshold pour déterminer n_components
        pca = PCA()
        pca.fit(embeddings)
        cumsum_variance = np.cumsum(pca.explained_variance_ratio_)
        n_components = np.argmax(cumsum_variance >= explained_variance_threshold) + 1
        print(f"   Nombre de composantes pour {explained_variance_threshold*100}% de variance: {n_components}")
    
    pca = PCA(n_components=n_components, random_state=42)
    embeddings_reduced = pca.fit_transform(embeddings)
    embeddings_reduced = embeddings_reduced.astype(np.float32)
    
    # 3. Statistiques
    explained_variance = pca.explained_variance_ratio_.sum()
    print(f"   Shape réduit: {embeddings_reduced.shape}")
    print(f"   Variance expliquée: {explained_variance*100:.2f}%")
    print(f"   Taille mémoire réduite: {embeddings_reduced.nbytes / (1024**2):.2f} MB")
    print(f"   Réduction: {(1 - embeddings_reduced.nbytes / embeddings.nbytes) * 100:.1f}%")
    
    # 4. Sauvegarder
    print(f"\n3. Sauvegarde dans '{output_path}'...")
    with open(output_path, 'wb') as f:
        pickle.dump(embeddings_reduced, f)
    
    file_size = Path(output_path).stat().st_size / (1024 * 1024)
    print(f"   ✅ Embeddings réduits sauvegardés ({file_size:.2f} MB)")
    
    # 5. Sauvegarder aussi le modèle PCA pour référence
    pca_path = output_path.replace('.pickle', '_pca_model.pickle')
    with open(pca_path, 'wb') as f:
        pickle.dump(pca, f)
    print(f"   ✅ Modèle PCA sauvegardé dans '{pca_path}'")
    
    print("\n=== RÉDUCTION TERMINÉE ===")
    print(f"\nPour utiliser les embeddings réduits, modifiez votre code pour charger:")
    print(f"  with open('{output_path}', 'rb') as f:")
    print(f"      embeddings = pickle.load(f)")
    
    return embeddings_reduced, pca


if __name__ == "__main__":
    # Exemple d'utilisation
    # Réduire à 50 composantes (ou ~95% de variance)
    reduce_embeddings_pca(
        input_path='articles_embeddings.pickle',
        output_path='articles_embeddings_reduced.pickle',
        n_components=50  # ou None pour utiliser explained_variance_threshold
    )

