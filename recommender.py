"""
Module de recommandation - Fonction pure pour la production
"""

import pickle
import numpy as np
from pathlib import Path
from typing import List, Optional
from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares


class Recommender:
    """Classe pour gérer le système de recommandation"""
    
    def __init__(self, artifacts_path: Optional[str] = None):
        """
        Initialise le recommandeur
        
        Args:
            artifacts_path: Chemin vers le fichier artifacts.pkl (optionnel)
        """
        self.als_model = None
        self.csr_train = None
        self.user_to_idx = None
        self.item_to_idx = None
        self.unique_users = None
        self.unique_items = None
        self.popularity_recommendations = None
        
        if artifacts_path:
            self.load_artifacts(artifacts_path)
    
    def load_artifacts(self, artifacts_path: str):
        """Charge les artefacts depuis un fichier pickle"""
        with open(artifacts_path, 'rb') as f:
            artifacts = pickle.load(f)
        
        self.als_model = artifacts['als_model']
        self.csr_train = artifacts['csr_train']
        self.user_to_idx = artifacts['user_to_idx']
        self.item_to_idx = artifacts['item_to_idx']
        self.unique_users = artifacts['unique_users']
        self.unique_items = artifacts['unique_items']
        self.popularity_recommendations = artifacts['popularity_recommendations']
    
    def load_from_separate_files(self, model_path: str, metadata_path: str, csr_path: str):
        """Charge les artefacts depuis des fichiers séparés (utile pour Azure)"""
        # Charger le modèle
        with open(model_path, 'rb') as f:
            self.als_model = pickle.load(f)
        
        # Charger les metadata
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        self.user_to_idx = metadata['user_to_idx']
        self.item_to_idx = metadata['item_to_idx']
        self.unique_users = metadata['unique_users']
        self.unique_items = metadata['unique_items']
        self.popularity_recommendations = metadata['popularity_recommendations']
        
        # Charger la matrice CSR
        with open(csr_path, 'rb') as f:
            self.csr_train = pickle.load(f)
    
    def recommend(self, user_id: int, n_reco: int = 5) -> List[int]:
        """
        Fonction pure de recommandation
        
        Args:
            user_id: ID de l'utilisateur
            n_reco: Nombre de recommandations (défaut: 5)
        
        Returns:
            Liste de article_id recommandés
        """
        if self.als_model is None:
            raise ValueError("Le modèle n'a pas été chargé. Appelez load_artifacts() d'abord.")
        
        # Si l'utilisateur n'est pas dans le train, retourner popularité
        if user_id not in self.user_to_idx:
            return self.popularity_recommendations[:n_reco]
        
        # Obtenir l'index de l'utilisateur et son vecteur
        user_idx = self.user_to_idx[user_id]
        user_vector = self.csr_train[user_idx]
        
        # Obtenir les recommandations
        recommendations = self.als_model.recommend(
            user_idx, 
            user_vector, 
            N=n_reco, 
            filter_already_liked_items=True
        )
        
        # Convertir les indices d'articles en article_id
        try:
            if isinstance(recommendations, np.ndarray):
                if recommendations.ndim == 2 and recommendations.shape[1] == 2:
                    # Array de shape (n, 2) : colonne 0 = item_idx, colonne 1 = score
                    recommended_item_ids = [self.unique_items[int(item_idx)] for item_idx in recommendations[:, 0]]
                elif recommendations.ndim == 1:
                    # Array 1D : ce sont directement les indices
                    recommended_item_ids = [self.unique_items[int(item_idx)] for item_idx in recommendations]
                else:
                    raise ValueError(f"Format d'array non reconnu: shape {recommendations.shape}")
            elif isinstance(recommendations, (list, tuple)):
                if len(recommendations) > 0:
                    first_rec = recommendations[0]
                    if isinstance(first_rec, (tuple, list, np.ndarray)) and len(first_rec) >= 2:
                        recommended_item_ids = [self.unique_items[int(rec[0])] for rec in recommendations]
                    elif isinstance(first_rec, (int, np.integer)):
                        recommended_item_ids = [self.unique_items[int(rec)] for rec in recommendations]
                    else:
                        raise ValueError(f"Format de liste non reconnu: {type(first_rec)}")
                else:
                    recommended_item_ids = []
            else:
                raise ValueError(f"Type de retour non reconnu: {type(recommendations)}")
        except Exception as e:
            # En cas d'erreur, utiliser popularité
            print(f"Warning: Erreur lors du parsing des recommandations ALS: {e}")
            recommended_item_ids = self.popularity_recommendations[:n_reco]
        
        # S'assurer d'avoir exactement n_reco recommandations
        if len(recommended_item_ids) < n_reco:
            recommended_item_ids.extend(self.popularity_recommendations[:n_reco - len(recommended_item_ids)])
        
        return recommended_item_ids[:n_reco]


# Fonction pure pour faciliter l'utilisation
def recommend(user_id: int, artifacts_path: str = "artifacts.pkl", n_reco: int = 5) -> List[int]:
    """
    Fonction pure de recommandation (interface simplifiée)
    
    Args:
        user_id: ID de l'utilisateur
        artifacts_path: Chemin vers le fichier artifacts.pkl
        n_reco: Nombre de recommandations (défaut: 5)
    
    Returns:
        Liste de article_id recommandés
    """
    recommender = Recommender(artifacts_path)
    return recommender.recommend(user_id, n_reco)


if __name__ == "__main__":
    # Test de la fonction
    print("Test de la fonction recommend()...")
    
    # Créer un recommandeur
    recommender = Recommender("artifacts.pkl")
    
    # Tester avec quelques utilisateurs
    test_user_ids = [0, 1, 2, 999999]  # Le dernier n'existe pas (test fallback)
    
    for user_id in test_user_ids:
        recommendations = recommender.recommend(user_id, n_reco=5)
        print(f"User {user_id}: {recommendations}")

