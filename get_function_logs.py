#!/usr/bin/env python3
"""
Script pour récupérer les logs de la fonction Azure depuis Application Insights
"""
import subprocess
import json
import sys
import os
from datetime import datetime, timedelta

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

def load_deployment_vars():
    """Charge les variables de déploiement depuis .azure_deploy_vars"""
    vars_file = ".azure_deploy_vars"
    if not os.path.exists(vars_file):
        return None
    
    try:
        with open(vars_file, 'r') as f:
            lines = f.readlines()
        
        vars = {}
        vars['resource_group'] = lines[0].strip() if len(lines) > 0 else None
        vars['region'] = lines[1].strip() if len(lines) > 1 else None
        vars['storage_account'] = lines[2].strip() if len(lines) > 2 else None
        vars['function_app'] = lines[3].strip() if len(lines) > 3 else None
        
        return vars
    except Exception as e:
        print_error(f"Erreur lors du chargement des variables: {e}")
        return None

def get_function_app_info(vars):
    """Récupère les informations de la Function App"""
    function_app = vars['function_app']
    resource_group = vars['resource_group']
    
    try:
        result = subprocess.run(
            ['az', 'functionapp', 'show',
             '--name', function_app,
             '--resource-group', resource_group,
             '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print_error(f"Impossible de récupérer les infos: {result.stderr}")
            return None
    except Exception as e:
        print_error(f"Erreur: {e}")
        return None

def get_recent_logs_az_cli(vars, minutes=30):
    """Récupère les logs récents via Azure CLI"""
    print_header(f"LOGS DES {minutes} DERNIÈRES MINUTES")
    
    function_app = vars['function_app']
    resource_group = vars['resource_group']
    
    # Calculer le temps de début
    start_time = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat() + 'Z'
    
    print_info("Récupération des logs via Azure CLI...")
    print_info("(Cela peut prendre quelques secondes...)\n")
    
    try:
        # Récupérer les logs d'exécution
        result = subprocess.run(
            ['az', 'monitor', 'app-insights', 'query',
             '--app', function_app,  # Cela nécessite Application Insights
             '--analytics-query',
             f"traces | where timestamp > ago({minutes}m) | order by timestamp desc | take 50",
             '--output', 'table'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print_warning("Application Insights non disponible ou non configuré")
            print_info("Tentative alternative...")
            
            # Alternative: logs via webapp
            result = subprocess.run(
                ['az', 'webapp', 'log', 'tail',
                 '--name', function_app,
                 '--resource-group', resource_group],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print_error("Impossible de récupérer les logs via Azure CLI")
                print_info("Utilisez le portail Azure pour voir les logs")
    except subprocess.TimeoutExpired:
        print_warning("Timeout lors de la récupération des logs")
    except Exception as e:
        print_error(f"Erreur: {e}")

def get_logs_via_portal(vars):
    """Affiche les instructions pour accéder aux logs via le portail"""
    print_header("ACCÈS AUX LOGS VIA LE PORTAL AZURE")
    
    function_app = vars['function_app']
    resource_group = vars['resource_group']
    
    print_info("Méthode 1: Log Stream (temps réel)")
    print(f"  https://portal.azure.com -> Function App -> {function_app} -> Log stream")
    print()
    
    print_info("Méthode 2: Application Insights (logs détaillés)")
    print(f"  https://portal.azure.com -> Function App -> {function_app} -> Application Insights")
    print()
    
    print_info("Méthode 3: Logs de la Function App")
    print(f"  https://portal.azure.com -> Function App -> {function_app} -> Monitoring -> Log stream")
    print()
    
    print_info("Méthode 4: Via Azure Functions Core Tools")
    print(f"  func azure functionapp logstream {function_app} --browser")
    print()

def get_recent_errors(vars):
    """Récupère les erreurs récentes"""
    print_header("RECHERCHE D'ERREURS RÉCENTES")
    
    function_app = vars['function_app']
    resource_group = vars['resource_group']
    
    print_info("Vérification des erreurs dans les logs...")
    print()
    print_info("Pour voir les erreurs en temps réel:")
    print(f"  1. Ouvrez le portail Azure: https://portal.azure.com")
    print(f"  2. Allez dans Function App -> {function_app}")
    print(f"  3. Cliquez sur 'Log stream' ou 'Application Insights'")
    print()
    print_info("Ou utilisez Azure CLI:")
    print(f"  az webapp log tail --name {function_app} --resource-group {resource_group}")
    print()

def get_function_execution_logs(vars):
    """Récupère les logs d'exécution de la fonction"""
    print_header("LOGS D'EXÉCUTION DE LA FONCTION")
    
    function_app = vars['function_app']
    
    print_info("Pour voir les logs d'exécution détaillés:")
    print()
    print("1. Via le portail Azure:")
    print(f"   https://portal.azure.com -> Function App -> {function_app} -> Functions -> RecommendArticle -> Monitor")
    print()
    print("2. Via Application Insights (si configuré):")
    print(f"   https://portal.azure.com -> Application Insights -> {function_app} -> Logs")
    print()
    print("3. Requête KQL pour Application Insights:")
    print("   traces")
    print("   | where timestamp > ago(1h)")
    print("   | where message contains 'Error' or message contains 'Exception'")
    print("   | order by timestamp desc")
    print()

def main():
    print_header("RÉCUPÉRATION DES LOGS DE LA FONCTION AZURE")
    
    vars = load_deployment_vars()
    if not vars:
        print_error("Variables de déploiement non trouvées")
        print_info("Assurez-vous que le fichier .azure_deploy_vars existe")
        sys.exit(1)
    
    print_info(f"Function App: {vars['function_app']}")
    print_info(f"Resource Group: {vars['resource_group']}")
    
    # Essayer de récupérer les logs
    get_recent_logs_az_cli(vars, minutes=30)
    
    # Afficher les instructions pour le portail
    get_logs_via_portal(vars)
    
    # Afficher les instructions pour les erreurs
    get_recent_errors(vars)
    
    # Afficher les instructions pour les logs d'exécution
    get_function_execution_logs(vars)
    
    print_header("RÉSUMÉ")
    print_success("Pour diagnostiquer l'erreur 500:")
    print("  1. Ouvrez Application Insights dans le portail Azure")
    print("  2. Cherchez les traces avec 'Error' ou 'Exception'")
    print("  3. Vérifiez les logs de la fonction RecommendArticle")
    print("  4. Regardez les détails de l'exception dans les logs")
    print()

if __name__ == "__main__":
    main()

