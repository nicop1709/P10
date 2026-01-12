#!/usr/bin/env python3
"""
Script pour vérifier les logs et l'état de la fonction Azure
"""
import subprocess
import json
import sys
import os

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

def load_deployment_vars():
    """Charge les variables de déploiement depuis .azure_deploy_vars"""
    vars_file = ".azure_deploy_vars"
    if not os.path.exists(vars_file):
        return None
    
    try:
        with open(vars_file, 'r') as f:
            lines = f.readlines()
        
        vars = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                vars[line] = None  # Les valeurs sont sur des lignes séparées
        
        # Lire les valeurs
        with open(vars_file, 'r') as f:
            lines = f.readlines()
        
        vars['resource_group'] = lines[0].strip() if len(lines) > 0 else None
        vars['region'] = lines[1].strip() if len(lines) > 1 else None
        vars['storage_account'] = lines[2].strip() if len(lines) > 2 else None
        vars['function_app'] = lines[3].strip() if len(lines) > 3 else None
        
        return vars
    except Exception as e:
        print_error(f"Erreur lors du chargement des variables: {e}")
        return None

def check_blob_storage(vars):
    """Vérifie que les fichiers sont bien dans Blob Storage"""
    print_header("VÉRIFICATION DES FICHIERS DANS BLOB STORAGE")
    
    storage_account = vars['storage_account']
    resource_group = vars['resource_group']
    
    # Récupérer la clé de stockage
    try:
        result = subprocess.run(
            ['az', 'storage', 'account', 'keys', 'list',
             '--account-name', storage_account,
             '--resource-group', resource_group,
             '--query', '[0].value',
             '--output', 'tsv'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print_error(f"Impossible de récupérer la clé de stockage: {result.stderr}")
            return False
        
        storage_key = result.stdout.strip()
        
        # Lister les fichiers dans le conteneur models
        result = subprocess.run(
            ['az', 'storage', 'blob', 'list',
             '--container-name', 'models',
             '--account-name', storage_account,
             '--account-key', storage_key,
             '--output', 'table'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            print_success("Fichiers dans le conteneur 'models':")
            print(result.stdout)
            
            # Vérifier les fichiers requis
            required_files = ['als_model.pkl', 'metadata.pkl', 'csr_train.pkl']
            output = result.stdout.lower()
            for file in required_files:
                if file.lower() in output:
                    print_success(f"  ✓ {file} trouvé")
                else:
                    print_error(f"  ✗ {file} MANQUANT")
                    return False
            return True
        else:
            print_error(f"Impossible de lister les fichiers: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error("Timeout lors de la vérification du stockage")
        return False
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def check_function_app_settings(vars):
    """Vérifie les paramètres de la Function App"""
    print_header("VÉRIFICATION DES PARAMÈTRES DE LA FUNCTION APP")
    
    function_app = vars['function_app']
    resource_group = vars['resource_group']
    
    try:
        result = subprocess.run(
            ['az', 'functionapp', 'config', 'appsettings', 'list',
             '--name', function_app,
             '--resource-group', resource_group,
             '--query', '[?name==`AzureWebJobsStorage`].{name:name, value:value}',
             '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            settings = json.loads(result.stdout)
            if settings and len(settings) > 0:
                print_success("AzureWebJobsStorage est configuré")
                # Afficher seulement le début de la chaîne de connexion
                conn_str = settings[0].get('value', '')
                if conn_str:
                    print_info(f"Chaîne de connexion: {conn_str[:50]}...")
                return True
            else:
                print_error("AzureWebJobsStorage n'est PAS configuré")
                return False
        else:
            print_error(f"Impossible de vérifier les paramètres: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Erreur: {e}")
        return False

def get_recent_logs(vars):
    """Récupère les logs récents de la fonction"""
    print_header("LOGS RÉCENTS DE LA FONCTION")
    
    function_app = vars['function_app']
    resource_group = vars['resource_group']
    
    print_info("Pour voir les logs en temps réel, utilisez:")
    print(f"  func azure functionapp logstream {function_app}")
    print()
    print_info("Ou via Azure CLI:")
    print(f"  az webapp log tail --name {function_app} --resource-group {resource_group}")
    print()
    print_info("Pour voir les logs dans le portail Azure:")
    print(f"  https://portal.azure.com -> Function App -> {function_app} -> Log stream")

def main():
    print_header("DIAGNOSTIC DE LA FONCTION AZURE")
    
    vars = load_deployment_vars()
    if not vars:
        print_error("Variables de déploiement non trouvées")
        print_info("Assurez-vous que le fichier .azure_deploy_vars existe")
        sys.exit(1)
    
    print_info(f"Function App: {vars['function_app']}")
    print_info(f"Resource Group: {vars['resource_group']}")
    print_info(f"Storage Account: {vars['storage_account']}")
    
    # Vérifications
    checks = []
    
    checks.append(("Blob Storage", check_blob_storage(vars)))
    checks.append(("Function App Settings", check_function_app_settings(vars)))
    
    # Résumé
    print_header("RÉSUMÉ DES VÉRIFICATIONS")
    all_ok = True
    for name, result in checks:
        if result:
            print_success(f"{name}: OK")
        else:
            print_error(f"{name}: ÉCHEC")
            all_ok = False
    
    if not all_ok:
        print()
        print_warning("Certaines vérifications ont échoué.")
        print_info("Actions recommandées:")
        print("  1. Vérifiez que les fichiers sont bien uploadés dans Blob Storage")
        print("  2. Vérifiez que AzureWebJobsStorage est configuré")
        print("  3. Redémarrez la Function App: az functionapp restart --name <FUNCTION_APP> --resource-group <RESOURCE_GROUP>")
        print("  4. Consultez les logs pour plus de détails")
    
    get_recent_logs(vars)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())

