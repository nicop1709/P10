"""
Azure Function pour le système de recommandation
Option 2: Charge directement les fichiers depuis Azure Blob Storage
"""

import logging
import json
import pickle
import os
import sys
from typing import List

# Ajouter le chemin parent pour importer recommender
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .recommender import Recommender
except ImportError:
    try:
        from recommender import Recommender
    except ImportError:
        # Si recommender n'est pas disponible, définir une classe minimale
        class Recommender:
        def __init__(self):
            self.als_model = None
            self.csr_train = None
            self.user_to_idx = None
            self.item_to_idx = None
            self.unique_users = None
            self.unique_items = None
            self.popularity_recommendations = None
        
        def load_from_separate_files(self, model_path: str, metadata_path: str, csr_path: str):
            with open(model_path, 'rb') as f:
                self.als_model = pickle.load(f)
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            self.user_to_idx = metadata['user_to_idx']
            self.item_to_idx = metadata['item_to_idx']
            self.unique_users = metadata['unique_users']
            self.unique_items = metadata['unique_items']
            self.popularity_recommendations = metadata['popularity_recommendations']
            with open(csr_path, 'rb') as f:
                self.csr_train = pickle.load(f)
        
        def recommend(self, user_id: int, n_reco: int = 5) -> List[int]:
            if self.als_model is None:
                raise ValueError("Modèle non chargé")
            if user_id not in self.user_to_idx:
                return self.popularity_recommendations[:n_reco]
            user_idx = self.user_to_idx[user_id]
            user_vector = self.csr_train[user_idx]
            recommendations = self.als_model.recommend(user_idx, user_vector, N=n_reco, filter_already_liked_items=True)
            import numpy as np
            if isinstance(recommendations, np.ndarray):
                if recommendations.ndim == 2:
                    recommended_item_ids = [self.unique_items[int(item_idx)] for item_idx in recommendations[:, 0]]
                else:
                    recommended_item_ids = [self.unique_items[int(item_idx)] for item_idx in recommendations]
            else:
                if len(recommendations) > 0 and isinstance(recommendations[0], (tuple, list)) and len(recommendations[0]) >= 2:
                    recommended_item_ids = [self.unique_items[int(rec[0])] for rec in recommendations]
                else:
                    recommended_item_ids = [self.unique_items[int(rec)] for rec in recommendations]
            if len(recommended_item_ids) < n_reco:
                recommended_item_ids.extend(self.popularity_recommendations[:n_reco - len(recommended_item_ids)])
            return recommended_item_ids[:n_reco]


# Variable globale pour le recommandeur (chargé une seule fois)
_recommender = None


def load_recommender(model_blob=None, metadata_blob=None, csr_blob=None):
    """
    Charge le recommandeur depuis Azure Blob Storage (via input binding)
    
    Args:
        model_blob: Bytes du modèle ALS (depuis Azure Blob binding)
        metadata_blob: Bytes des metadata (depuis Azure Blob binding)
        csr_blob: Bytes de la matrice CSR (depuis Azure Blob binding)
    """
    global _recommender
    
    if _recommender is not None:
        return _recommender
    
    try:
        _recommender = Recommender()
        
        # Si les blobs sont fournis (production Azure), les utiliser directement
        if model_blob is not None and metadata_blob is not None and csr_blob is not None:
            logging.info("Chargement depuis Azure Blob Storage (bindings)")
            
            # Utiliser la méthode load_from_bytes si disponible
            if hasattr(_recommender, 'load_from_bytes'):
                _recommender.load_from_bytes(model_blob, metadata_blob, csr_blob)
            else:
                # Fallback: charger manuellement
                import io
                _recommender.als_model = pickle.load(io.BytesIO(model_blob))
                metadata = pickle.load(io.BytesIO(metadata_blob))
                _recommender.csr_train = pickle.load(io.BytesIO(csr_blob))
                
                _recommender.user_to_idx = metadata['user_to_idx']
                _recommender.item_to_idx = metadata['item_to_idx']
                _recommender.unique_users = metadata['unique_users']
                _recommender.unique_items = metadata['unique_items']
                _recommender.popularity_recommendations = metadata['popularity_recommendations']
        
        else:
            # Fallback: charger depuis le système de fichiers (développement local)
            logging.info("Chargement depuis le système de fichiers (mode développement)")
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            local_model = os.path.join(script_dir, '..', '..', 'als_model.pkl')
            local_metadata = os.path.join(script_dir, '..', '..', 'metadata.pkl')
            local_csr = os.path.join(script_dir, '..', '..', 'csr_train.pkl')
            
            # Vérifier que les fichiers existent
            if not os.path.exists(local_model):
                raise FileNotFoundError(f"Fichier modèle non trouvé: {local_model}")
            if not os.path.exists(local_metadata):
                raise FileNotFoundError(f"Fichier metadata non trouvé: {local_metadata}")
            if not os.path.exists(local_csr):
                raise FileNotFoundError(f"Fichier CSR non trouvé: {local_csr}")
            
            _recommender.load_from_separate_files(local_model, local_metadata, local_csr)
        
        logging.info("✅ Modèle chargé avec succès")
        return _recommender
    
    except Exception as e:
        logging.error(f"❌ Erreur lors du chargement du modèle: {e}", exc_info=True)
        raise


def main(req, modelBlob=None, metadataBlob=None, csrBlob=None) -> str:
    """
    Azure Function HTTP Trigger
    
    Args:
        req: Requête HTTP contenant user_id
        modelBlob: Blob du modèle ALS (input binding Azure)
        metadataBlob: Blob des metadata (input binding Azure)
        csrBlob: Blob de la matrice CSR (input binding Azure)
    
    Returns:
        JSON avec les recommandations
    """
    logging.info('Azure Function RecommendArticle déclenchée')
    
    try:
        # Charger le recommandeur (une seule fois, puis mis en cache)
        # Les blobs sont fournis automatiquement par Azure Functions via les input bindings
        recommender = load_recommender(modelBlob, metadataBlob, csrBlob)
        
        # Récupérer le user_id depuis la requête
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        
        # Support pour GET (query params) et POST (body)
        user_id = req_body.get('user_id') if req_body else None
        if user_id is None:
            user_id = req.params.get('user_id')
        
        if user_id is None:
            return json.dumps({
                'error': 'user_id manquant',
                'message': 'Veuillez fournir un user_id dans les paramètres de requête ou le body JSON'
            }), 400
        
        # Convertir en int
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return json.dumps({
                'error': 'user_id invalide',
                'message': 'user_id doit être un entier'
            }), 400
        
        # Obtenir les recommandations
        recommendations = recommender.recommend(user_id, n_reco=5)
        
        # Retourner le JSON
        response = {
            'user_id': user_id,
            'recommendations': recommendations,
            'count': len(recommendations)
        }
        
        logging.info(f"✅ Recommandations générées pour user_id={user_id}: {recommendations}")
        
        return json.dumps(response, indent=2)
    
    except Exception as e:
        logging.error(f"❌ Erreur: {str(e)}", exc_info=True)
        return json.dumps({
            'error': 'Erreur interne',
            'message': str(e)
        }), 500

