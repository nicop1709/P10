#!/usr/bin/env python3
"""
Script de test pour la fonction Azure RecommendArticle
"""
import urllib.request
import urllib.parse
import json
import ssl

# Configuration
FUNCTION_URL = "https://func-recommender-1768155564.azurewebsites.net/api/recommendarticle"

def test_function(user_id=0, function_key=None):
    """Teste la fonction Azure avec un user_id donné"""
    if not function_key:
        raise ValueError("La clé de fonction est requise")
    
    # Construire l'URL avec les paramètres
    params = {
        'code': function_key,
        'user_id': user_id
    }
    url = f"{FUNCTION_URL}?{urllib.parse.urlencode(params)}"
    
    print(f"🔍 Test de la fonction Azure...")
    print(f"📍 URL: {FUNCTION_URL}")
    print(f"👤 User ID: {user_id}")
    print(f"🔗 Requête complète: {url[:80]}...")
    print()
    
    try:
        # Créer un contexte SSL qui ignore la vérification (pour les tests locaux)
        # En production, vous devriez utiliser un certificat valide
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Faire la requête
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            status_code = response.getcode()
            response_data = response.read().decode('utf-8')
            
            print(f"✅ Statut HTTP: {status_code}")
            print(f"📦 Réponse:")
            
            # Essayer de parser en JSON pour un affichage plus lisible
            try:
                json_data = json.loads(response_data)
                print(json.dumps(json_data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(response_data)
            
            return True, response_data
            
    except urllib.error.HTTPError as e:
        print(f"❌ Erreur HTTP {e.code}: {e.reason}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"📄 Détails de l'erreur:")
            print(error_body)
            
            # Essayer de parser en JSON pour un affichage plus lisible
            try:
                error_json = json.loads(error_body)
                print("\n📋 Erreur formatée:")
                print(json.dumps(error_json, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                pass
        except Exception as read_error:
            print(f"⚠️  Impossible de lire le corps de l'erreur: {read_error}")
        return False, None
        
    except urllib.error.URLError as e:
        print(f"❌ Erreur URL: {e.reason}")
        return False, None
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {type(e).__name__}: {str(e)}")
        return False, None

if __name__ == "__main__":
    import sys
    import os
    
    # Récupérer la clé depuis l'environnement ou les arguments
    function_key = None
    if 'AZURE_FUNCTION_KEY' in os.environ:
        function_key = os.environ['AZURE_FUNCTION_KEY']
    elif len(sys.argv) > 2:
        function_key = sys.argv[2]
    
    # Récupérer user_id depuis les arguments ou utiliser 0 par défaut
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    
    if not function_key:
        print("❌ Erreur: Aucune clé de fonction fournie!")
        print("   Utilisez: export AZURE_FUNCTION_KEY='votre_cle'")
        print("   ou: python test_function.py <user_id> <function_key>")
        sys.exit(1)
    
    success, response = test_function(user_id, function_key)
    
    if success:
        print("\n✅ Test réussi!")
        sys.exit(0)
    else:
        print("\n❌ Test échoué!")
        sys.exit(1)

