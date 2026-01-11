#!/usr/bin/env python3
"""
Script de vérification et d'aide au déploiement Azure
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def check_file_exists(filepath):
    """Vérifie si un fichier existe"""
    path = Path(filepath)
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        print_success(f"{filepath} existe ({size_mb:.2f} MB)")
        return True
    else:
        print_error(f"{filepath} manquant")
        return False

def check_azure_cli():
    """Vérifie si Azure CLI est installé"""
    try:
        result = subprocess.run(['az', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print_success(f"Azure CLI installé: {version}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print_error("Azure CLI n'est pas installé")
    print_info("Installez-le avec: brew install azure-cli (macOS)")
    return False

def check_func_tools():
    """Vérifie si Azure Functions Core Tools est installé"""
    try:
        result = subprocess.run(['func', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Azure Functions Core Tools installé: {version}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print_error("Azure Functions Core Tools n'est pas installé")
    print_info("Installez-le avec: npm install -g azure-functions-core-tools@4 --unsafe-perm true")
    return False

def check_azure_login():
    """Vérifie si l'utilisateur est connecté à Azure"""
    try:
        # Vérifier d'abord si on peut lister les comptes
        list_result = subprocess.run(['az', 'account', 'list'], 
                                    capture_output=True, 
                                    text=True, 
                                    timeout=10)
        
        if list_result.returncode == 0:
            accounts = json.loads(list_result.stdout)
            if len(accounts) == 0:
                print_error("Aucun abonnement Azure trouvé")
                print_warning("Votre compte n'a pas d'abonnement Azure associé")
                print_info("Consultez SETUP_AZURE_ACCOUNT.md pour créer un compte Azure gratuit")
                print_info("Ou visitez: https://azure.microsoft.com/free/")
                return False
            
            # Vérifier l'abonnement actif
            result = subprocess.run(['az', 'account', 'show'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                account = json.loads(result.stdout)
                print_success(f"Connecté à Azure: {account.get('name', 'N/A')}")
                print_info(f"  Subscription ID: {account.get('id', 'N/A')}")
                print_info(f"  État: {account.get('state', 'N/A')}")
                return True
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        pass
    
    # Vérifier si c'est un problème de connexion ou d'abonnement
    try:
        login_check = subprocess.run(['az', 'account', 'show'], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=10)
        if "No subscriptions found" in login_check.stderr:
            print_error("Aucun abonnement Azure trouvé")
            print_warning("Votre compte n'a pas d'abonnement Azure associé")
            print_info("Consultez SETUP_AZURE_ACCOUNT.md pour créer un compte Azure gratuit")
            return False
    except:
        pass
    
    print_warning("Vous n'êtes pas connecté à Azure ou aucun abonnement trouvé")
    print_info("Connectez-vous avec: az login")
    print_info("Si vous n'avez pas d'abonnement, consultez SETUP_AZURE_ACCOUNT.md")
    return False

def check_artifacts():
    """Vérifie que les artefacts sont présents"""
    print_header("VÉRIFICATION DES ARTEFACTS")
    
    artifacts = ['als_model.pkl', 'metadata.pkl', 'csr_train.pkl']
    all_exist = True
    
    for artifact in artifacts:
        if not check_file_exists(artifact):
            all_exist = False
    
    if not all_exist:
        print_warning("Exécutez d'abord: python serialize_artifacts.py")
    
    return all_exist

def check_azure_function_structure():
    """Vérifie la structure du dossier azure_function"""
    print_header("VÉRIFICATION DE LA STRUCTURE AZURE FUNCTION")
    
    base_dir = Path(__file__).parent
    azure_function_dir = base_dir / "azure_function"
    
    if not azure_function_dir.exists():
        print_error("Le dossier azure_function n'existe pas")
        return False
    
    print_success("Dossier azure_function existe")
    
    # Vérifier les fichiers nécessaires
    required_files = {
        'host.json': azure_function_dir / 'host.json',
        'requirements.txt': azure_function_dir / 'requirements.txt',
        'RecommendArticle/__init__.py': azure_function_dir / 'RecommendArticle' / '__init__.py',
        'RecommendArticle/function.json': azure_function_dir / 'RecommendArticle' / 'function.json',
    }
    
    all_exist = True
    for name, path in required_files.items():
        if path.exists():
            print_success(f"{name} existe")
        else:
            print_error(f"{name} manquant")
            all_exist = False
    
    return all_exist

def load_deployment_vars():
    """Charge les variables de déploiement depuis .azure_deploy_vars"""
    vars_file = Path('.azure_deploy_vars')
    if vars_file.exists():
        with open(vars_file, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 4:
                return {
                    'resource_group': lines[0].strip(),
                    'location': lines[1].strip(),
                    'storage_account': lines[2].strip(),
                    'function_app': lines[3].strip(),
                }
    return None

def check_deployment_status():
    """Vérifie l'état du déploiement Azure"""
    print_header("VÉRIFICATION DU DÉPLOIEMENT AZURE")
    
    vars = load_deployment_vars()
    if not vars:
        print_warning("Aucune variable de déploiement trouvée")
        print_info("Exécutez d'abord le script deploy_azure.sh (étape 1)")
        return False
    
    print_info(f"Resource Group: {vars['resource_group']}")
    print_info(f"Function App: {vars['function_app']}")
    print_info(f"Storage Account: {vars['storage_account']}")
    
    # Vérifier si le Resource Group existe
    try:
        result = subprocess.run(
            ['az', 'group', 'show', '--name', vars['resource_group']],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print_success("Resource Group existe")
        else:
            print_error("Resource Group n'existe pas")
            return False
    except subprocess.TimeoutExpired:
        print_warning("Impossible de vérifier le Resource Group (timeout)")
    
    # Vérifier si la Function App existe
    try:
        result = subprocess.run(
            ['az', 'functionapp', 'show', 
             '--name', vars['function_app'],
             '--resource-group', vars['resource_group']],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            app_info = json.loads(result.stdout)
            state = app_info.get('state', 'Unknown')
            print_success(f"Function App existe (État: {state})")
        else:
            print_error("Function App n'existe pas")
            return False
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        print_warning("Impossible de vérifier la Function App")
    
    return True

def main():
    print_header("VÉRIFICATION DU DÉPLOIEMENT")
    
    # Vérifier les prérequis
    print_header("PRÉREQUIS")
    cli_ok = check_azure_cli()
    func_ok = check_func_tools()
    login_ok = check_azure_login() if cli_ok else False
    
    # Vérifier les artefacts
    artifacts_ok = check_artifacts()
    
    # Vérifier la structure
    structure_ok = check_azure_function_structure()
    
    # Vérifier le déploiement
    deployment_ok = check_deployment_status() if login_ok else False
    
    # Résumé
    print_header("RÉSUMÉ")
    
    print("\nPrérequis:")
    print(f"  Azure CLI: {'✅' if cli_ok else '❌'}")
    print(f"  Functions Tools: {'✅' if func_ok else '❌'}")
    print(f"  Connexion Azure: {'✅' if login_ok else '❌'}")
    
    print("\nFichiers:")
    print(f"  Artefacts: {'✅' if artifacts_ok else '❌'}")
    print(f"  Structure Azure Function: {'✅' if structure_ok else '❌'}")
    
    print("\nDéploiement:")
    print(f"  Ressources Azure: {'✅' if deployment_ok else '❌'}")
    
    # Recommandations
    print_header("PROCHAINES ÉTAPES")
    
    if not cli_ok or not func_ok:
        print("1. Installez les outils manquants")
    
    if not login_ok:
        print("2. Connectez-vous à Azure: az login")
    
    if not artifacts_ok:
        print("3. Générez les artefacts: python serialize_artifacts.py")
    
    if not structure_ok:
        print("4. Vérifiez la structure du dossier azure_function")
    
    if cli_ok and func_ok and login_ok and artifacts_ok and structure_ok:
        if not deployment_ok:
            print("5. Déployez avec: ./deploy_azure.sh")
        else:
            print("✅ Tout est prêt! Vous pouvez tester votre fonction.")
            print("\nPour tester:")
            vars = load_deployment_vars()
            if vars:
                print(f"  curl \"https://{vars['function_app']}.azurewebsites.net/api/RecommendArticle?code=<KEY>&user_id=0\"")

if __name__ == "__main__":
    main()

