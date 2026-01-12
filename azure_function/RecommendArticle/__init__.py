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
import azure.functions as func

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
            
            # Les blobs peuvent être des InputStream, il faut les lire en bytes
            import io
            
            # Fonction helper pour convertir InputStream en bytes
            def read_blob(blob, name="blob"):
                try:
                    if hasattr(blob, 'read'):
                        # C'est un InputStream, le lire en mode binaire
                        # S'assurer qu'on lit tout le contenu
                        if hasattr(blob, 'seek'):
                            try:
                                blob.seek(0)  # Retourner au début si possible
                            except:
                                pass  # Si seek n'est pas supporté, continuer
                        
                        # Lire tout le contenu
                        data = blob.read()
                        
                        # Vérifier que c'est bien des bytes
                        if isinstance(data, str):
                            # Si c'est une string, c'est un problème - les pickles doivent être binaires
                            logging.error(f"Blob {name} lu comme string au lieu de bytes! Type: {type(data)}, Premiers caractères: {data[:50] if len(data) > 50 else data}")
                            # Essayer de convertir en bytes (mais cela peut corrompre les données)
                            data = data.encode('latin-1')  # Préserver les bytes
                            logging.warning(f"Conversion string->bytes effectuée pour {name}, mais les données peuvent être corrompues")
                        elif not isinstance(data, bytes):
                            # Essayer de convertir
                            logging.warning(f"Blob {name} type inattendu: {type(data)}, tentative de conversion")
                            data = bytes(data)
                        
                        # Vérifier les premiers bytes pour s'assurer que c'est un pickle valide
                        if len(data) > 0:
                            # Les fichiers pickle commencent généralement par certains bytes
                            first_bytes = data[:4] if len(data) >= 4 else data
                            logging.info(f"Blob {name} lu: {len(data)} bytes, premiers bytes: {first_bytes.hex() if isinstance(first_bytes, bytes) else str(first_bytes)}")
                        else:
                            logging.error(f"Blob {name} est vide!")
                        
                        return data
                    elif isinstance(blob, bytes):
                        # C'est déjà des bytes
                        logging.info(f"Blob {name} déjà en bytes: {len(blob)} bytes")
                        return blob
                    else:
                        # Essayer de convertir
                        logging.warning(f"Blob {name} type inattendu: {type(blob)}, tentative de conversion")
                        return bytes(blob)
                except Exception as e:
                    logging.error(f"Erreur lors de la lecture du blob {name}: {e}", exc_info=True)
                    raise ValueError(f"Impossible de lire le blob {name}: {e}")
            
            logging.info("Lecture des blobs depuis InputStream...")
            model_bytes = read_blob(model_blob, "model")
            metadata_bytes = read_blob(metadata_blob, "metadata")
            csr_bytes = read_blob(csr_blob, "csr")
            
            # Vérifier que les blobs ne sont pas vides
            if len(model_bytes) == 0 or len(metadata_bytes) == 0 or len(csr_bytes) == 0:
                raise ValueError("Un ou plusieurs blobs sont vides")
            
            logging.info(f"Taille des blobs - Modèle: {len(model_bytes)}, Metadata: {len(metadata_bytes)}, CSR: {len(csr_bytes)}")
            
            # Utiliser la méthode load_from_bytes si disponible
            if hasattr(_recommender, 'load_from_bytes'):
                _recommender.load_from_bytes(model_bytes, metadata_bytes, csr_bytes)
            else:
                # Fallback: charger manuellement
                logging.info("Chargement du modèle...")
                _recommender.als_model = pickle.load(io.BytesIO(model_bytes))
                logging.info("Chargement des metadata...")
                metadata = pickle.load(io.BytesIO(metadata_bytes))
                logging.info("Chargement de la matrice CSR...")
                _recommender.csr_train = pickle.load(io.BytesIO(csr_bytes))
                
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


def main(req, modelBlob=None, metadataBlob=None, csrBlob=None):
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
    logging.info('='*60)
    logging.info('Azure Function RecommendArticle déclenchée')
    
    # Les blobs peuvent être des InputStream, pas des bytes directement
    # On ne peut pas utiliser len() sur un InputStream
    def get_blob_info(blob, name):
        if blob is None:
            return f"{name}: None"
        blob_type = type(blob).__name__
        # Si c'est un InputStream, on ne peut pas obtenir la taille directement
        if hasattr(blob, 'read'):
            return f"{name}: {blob_type} (InputStream)"
        elif hasattr(blob, '__len__'):
            return f"{name}: {blob_type}, Taille: {len(blob)}"
        else:
            return f"{name}: {blob_type}"
    
    logging.info(get_blob_info(modelBlob, 'modelBlob'))
    logging.info(get_blob_info(metadataBlob, 'metadataBlob'))
    logging.info(get_blob_info(csrBlob, 'csrBlob'))
    
    try:
        # Charger le recommandeur (une seule fois, puis mis en cache)
        # Les blobs sont fournis automatiquement par Azure Functions via les input bindings
        logging.info('Début du chargement du recommandeur...')
        try:
            recommender = load_recommender(modelBlob, metadataBlob, csrBlob)
            logging.info('✅ Recommandeur chargé avec succès')
        except Exception as load_error:
            # Capturer spécifiquement les erreurs de chargement
            import traceback
            error_trace = traceback.format_exc()
            logging.error(f"❌ ERREUR CRITIQUE lors du chargement du modèle: {load_error}")
            logging.error(f"❌ Type d'erreur: {type(load_error).__name__}")
            logging.error(f"❌ Traceback complet:\n{error_trace}")
            
            # Retourner une erreur détaillée
            return func.HttpResponse(
                json.dumps({
                    'error': 'Erreur de chargement du modèle',
                    'message': str(load_error),
                    'type': type(load_error).__name__,
                    'details': 'Vérifiez les logs Application Insights pour plus de détails'
                }),
                status_code=500,
                mimetype='application/json'
            )
        
        # Récupérer le user_id depuis la requête
        try:
            req_body = req.get_json()
            logging.info(f'Body de la requête: {req_body}')
        except ValueError as e:
            logging.warning(f'Impossible de parser le body JSON: {e}')
            req_body = {}
        
        # Support pour GET (query params) et POST (body)
        user_id = req_body.get('user_id') if req_body else None
        if user_id is None:
            user_id = req.params.get('user_id')
            logging.info(f'user_id depuis query params: {user_id}')
        
        if user_id is None:
            logging.warning('user_id manquant dans la requête')
            return func.HttpResponse(
                json.dumps({
                    'error': 'user_id manquant',
                    'message': 'Veuillez fournir un user_id dans les paramètres de requête ou le body JSON'
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        # Convertir en int
        try:
            user_id = int(user_id)
            logging.info(f'user_id converti en int: {user_id}')
        except (ValueError, TypeError) as e:
            logging.error(f'Erreur de conversion user_id: {e}')
            return func.HttpResponse(
                json.dumps({
                    'error': 'user_id invalide',
                    'message': 'user_id doit être un entier'
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        # Obtenir les recommandations
        logging.info(f'Génération des recommandations pour user_id={user_id}...')
        recommendations = recommender.recommend(user_id, n_reco=5)
        logging.info(f'Recommandations générées: {recommendations}')
        
        # Convertir les recommandations en types Python standard (pour éviter les problèmes avec numpy int64)
        recommendations_list = [int(rec) for rec in recommendations]

        # Retourner le JSON
        response = {
            'user_id': user_id,
            'recommendations': recommendations_list,
            'count': len(recommendations_list)
        }
        
        logging.info(f"✅ Recommandations générées pour user_id={user_id}: {recommendations}")
        
        return func.HttpResponse(
            json.dumps(response, indent=2),
            status_code=200,
            mimetype='application/json'
        )
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"❌ Erreur: {str(e)}")
        logging.error(f"❌ Traceback complet:\n{error_details}")
        
        # Retourner une réponse avec plus de détails en mode développement
        error_response = {
            'error': 'Erreur interne',
            'message': str(e),
            'type': type(e).__name__
        }
        
        # Ne pas exposer le traceback complet en production pour des raisons de sécurité
        # Mais le logger pour le diagnostic
        return func.HttpResponse(
            json.dumps(error_response),
            status_code=500,
            mimetype='application/json'
        )

