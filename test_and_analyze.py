#!/usr/bin/env python3
"""
Script pour tester la fonction et analyser les erreurs en détail
"""
import urllib.request
import urllib.parse
import json
import ssl
import sys
import os
from datetime import datetime

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_info(text):
    print(f"ℹ️  {text}")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

def test_function_detailed(user_id=0, function_key=None):
    """Teste la fonction avec une analyse détaillée"""
    FUNCTION_URL = "https://func-recommender-1768155564.azurewebsites.net/api/recommendarticle"
    
    if not function_key:
        if 'AZURE_FUNCTION_KEY' in os.environ:
            function_key = os.environ['AZURE_FUNCTION_KEY']
    
    if not function_key:
        print_error("Aucune clé de fonction trouvée")
        print_info("Définissez AZURE_FUNCTION_KEY dans votre environnement:")
        print_info("  export AZURE_FUNCTION_KEY='votre_cle'")
        print_info("Ou passez-la en argument: test_and_analyze.py <user_id> <function_key>")
        return False, None
    
    # Construire l'URL
    params = {
        'code': function_key,
        'user_id': user_id
    }
    url = f"{FUNCTION_URL}?{urllib.parse.urlencode(params)}"
    
    print_header("TEST DÉTAILLÉ DE LA FONCTION AZURE")
    print_info(f"URL: {FUNCTION_URL}")
    print_info(f"User ID: {user_id}")
    print_info(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    try:
        # Créer un contexte SSL
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Faire la requête avec timeout
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Python-Test-Script/1.0')
        
        print_info("Envoi de la requête...")
        start_time = datetime.now()
        
        try:
            with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
                elapsed = (datetime.now() - start_time).total_seconds()
                status_code = response.getcode()
                headers = dict(response.headers)
                response_data = response.read().decode('utf-8')
                
                print_success(f"Statut HTTP: {status_code}")
                print_info(f"Temps de réponse: {elapsed:.2f}s")
                print_info(f"Headers de réponse:")
                for key, value in headers.items():
                    if key.lower() in ['content-type', 'content-length', 'date']:
                        print(f"  {key}: {value}")
                print()
                
                print_info("Corps de la réponse:")
                try:
                    json_data = json.loads(response_data)
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                    return True, json_data
                except json.JSONDecodeError:
                    print(response_data)
                    return True, response_data
                    
        except urllib.error.HTTPError as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            print_error(f"Erreur HTTP {e.code}: {e.reason}")
            print_info(f"Temps avant erreur: {elapsed:.2f}s")
            print()
            
            # Analyser les headers de l'erreur
            print_info("Headers de l'erreur:")
            for key, value in e.headers.items():
                print(f"  {key}: {value}")
            print()
            
            # Lire le corps de l'erreur
            print_info("Corps de l'erreur:")
            try:
                error_body = e.read().decode('utf-8')
                print(error_body)
                print()
                
                # Essayer de parser en JSON
                try:
                    error_json = json.loads(error_body)
                    print_info("Erreur formatée (JSON):")
                    print(json.dumps(error_json, indent=2, ensure_ascii=False))
                    
                    # Analyser le type d'erreur
                    if 'error' in error_json:
                        print()
                        print_header("ANALYSE DE L'ERREUR")
                        print_error(f"Type: {error_json.get('error', 'Unknown')}")
                        print_error(f"Message: {error_json.get('message', 'No message')}")
                        if 'type' in error_json:
                            print_error(f"Exception Type: {error_json.get('type')}")
                        
                        # Suggestions basées sur le type d'erreur
                        error_type = error_json.get('type', '')
                        message = error_json.get('message', '').lower()
                        
                        if 'modulenotfound' in error_type.lower() or 'modulenotfound' in message:
                            print()
                            print_warning("SUGGESTION: Dépendance Python manquante")
                            print_info("  - Vérifiez requirements.txt")
                            print_info("  - Redéployez la fonction")
                        elif 'attributeerror' in error_type.lower() or 'attributeerror' in message:
                            print()
                            print_warning("SUGGESTION: Erreur dans le code Python")
                            print_info("  - Vérifiez les logs Application Insights")
                            print_info("  - Vérifiez la ligne mentionnée dans le traceback")
                        elif 'pickle' in message or 'unpickling' in message:
                            print()
                            print_warning("SUGGESTION: Problème avec les fichiers pickle")
                            print_info("  - Vérifiez que les fichiers sont bien uploadés")
                            print_info("  - Vérifiez la compatibilité des versions Python")
                        elif 'memory' in message or 'out of memory' in message:
                            print()
                            print_warning("SUGGESTION: Problème de mémoire")
                            print_info("  - Les fichiers sont peut-être trop volumineux")
                            print_info("  - Envisagez un plan Premium")
                        elif 'timeout' in message:
                            print()
                            print_warning("SUGGESTION: Timeout")
                            print_info("  - Le chargement prend trop de temps")
                            print_info("  - Augmentez le timeout dans host.json")
                    
                except json.JSONDecodeError:
                    print_warning("L'erreur n'est pas au format JSON")
                    print_info("Cela peut indiquer un problème au niveau du serveur Azure")
                    
            except Exception as read_error:
                print_error(f"Impossible de lire le corps de l'erreur: {read_error}")
            
            return False, None
            
    except urllib.error.URLError as e:
        print_error(f"Erreur URL: {e.reason}")
        return False, None
        
    except Exception as e:
        print_error(f"Erreur inattendue: {type(e).__name__}: {str(e)}")
        import traceback
        print_error("Traceback:")
        print(traceback.format_exc())
        return False, None

def main():
    import sys
    
    # Récupérer user_id et function_key depuis les arguments
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    function_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    success, response = test_function_detailed(user_id, function_key)
    
    print()
    print_header("RÉSUMÉ")
    if success:
        print_success("Test réussi!")
        print_info("La fonction répond correctement")
    else:
        print_error("Test échoué!")
        print()
        print_info("Pour voir les logs détaillés:")
        print("  1. func azure functionapp logstream func-recommender-1768155564 --browser")
        print("  2. Portail Azure -> Function App -> Log stream")
        print("  3. Portail Azure -> Application Insights -> Logs")
        print()
        print_info("Requête KQL pour Application Insights:")
        print("  traces")
        print("  | where timestamp > ago(30m)")
        print("  | where severityLevel >= 3")
        print("  | order by timestamp desc")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

