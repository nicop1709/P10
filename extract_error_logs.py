#!/usr/bin/env python3
"""
Script pour extraire et analyser les logs d'erreur depuis Application Insights
"""
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

def print_warning(text):
    print(f"⚠️  {text}")

def analyze_log_entry(log_entry):
    """Analyse une entrée de log et extrait les informations importantes"""
    print_header("ANALYSE DE L'ENTRÉE DE LOG")
    
    # Extraire les informations principales
    timestamp = log_entry.get('timestamp', 'Unknown')
    message = log_entry.get('message', '')
    severity = log_entry.get('severityLevel', 0)
    item_type = log_entry.get('itemType', '')
    custom_dims = log_entry.get('customDimensions', {})
    
    print_info(f"Timestamp: {timestamp}")
    print_info(f"Type: {item_type}")
    print_info(f"Niveau de sévérité: {severity}")
    print()
    
    if message:
        print_info("Message:")
        print(f"  {message}")
        print()
    
    # Analyser les dimensions personnalisées
    if custom_dims:
        print_info("Détails supplémentaires:")
        for key, value in custom_dims.items():
            if key not in ['prop__{OriginalFormat}', 'LogLevel', 'EventId', 'Category', 'EventName']:
                print(f"  {key}: {value}")
        print()
    
    # Vérifier si c'est une erreur
    if severity >= 3:
        print_error("⚠️  C'EST UNE ERREUR!")
        
        # Chercher des indices sur le type d'erreur
        message_lower = message.lower()
        custom_str = str(custom_dims).lower()
        
        if 'modulenotfound' in message_lower or 'modulenotfound' in custom_str:
            print()
            print_warning("DIAGNOSTIC: Module Python manquant")
            print_info("Solution: Vérifiez requirements.txt et redéployez")
        elif 'attributeerror' in message_lower or 'attributeerror' in custom_str:
            print()
            print_warning("DIAGNOSTIC: Erreur d'attribut dans le code")
            print_info("Solution: Vérifiez le code Python, ligne mentionnée dans le traceback")
        elif 'pickle' in message_lower or 'unpickling' in message_lower:
            print()
            print_warning("DIAGNOSTIC: Problème avec les fichiers pickle")
            print_info("Solution: Vérifiez que les fichiers sont bien uploadés et compatibles")
        elif 'memory' in message_lower or 'out of memory' in message_lower:
            print()
            print_warning("DIAGNOSTIC: Problème de mémoire")
            print_info("Solution: Envisagez un plan Premium")
        elif 'timeout' in message_lower:
            print()
            print_warning("DIAGNOSTIC: Timeout")
            print_info("Solution: Augmentez le timeout dans host.json")
        elif 'exception' in message_lower or 'error' in message_lower:
            print()
            print_warning("DIAGNOSTIC: Exception Python")
            print_info("Solution: Vérifiez le message d'erreur complet ci-dessus")

def main():
    print_header("EXTRACTION ET ANALYSE DES LOGS D'ERREUR")
    
    print_info("Ce script analyse les logs que vous copiez depuis Application Insights")
    print_info("Pour obtenir les logs:")
    print("  1. Allez sur https://portal.azure.com")
    print("  2. Application Insights -> func-recommender-1768155564 -> Logs")
    print("  3. Exécutez cette requête KQL:")
    print()
    print("     traces")
    print("     | where timestamp > ago(1h)")
    print("     | where severityLevel >= 3 or message contains 'Error' or message contains 'Exception'")
    print("     | order by timestamp desc")
    print("     | take 20")
    print()
    print("  4. Copiez les résultats JSON et collez-les ici (ou sauvegardez dans un fichier)")
    print()
    
    # Demander le fichier ou l'entrée
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        if os.path.exists(log_file):
            print_info(f"Lecture du fichier: {log_file}")
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            print_error(f"Fichier non trouvé: {log_file}")
            return 1
    else:
        print_info("Collez les logs JSON ici (appuyez sur Ctrl+D ou Ctrl+Z pour terminer):")
        print()
        content = sys.stdin.read()
    
    # Parser le JSON
    try:
        # Essayer de parser comme un tableau
        if content.strip().startswith('['):
            logs = json.loads(content)
        else:
            # Essayer de parser comme un objet unique
            logs = [json.loads(content)]
        
        print_success(f"{len(logs)} entrée(s) de log trouvée(s)")
        print()
        
        # Analyser chaque log
        error_count = 0
        for i, log in enumerate(logs, 1):
            severity = log.get('severityLevel', 0)
            if severity >= 3:
                error_count += 1
                print(f"\n{'='*60}")
                print(f"ERREUR #{error_count}")
                print(f"{'='*60}")
                analyze_log_entry(log)
        
        if error_count == 0:
            print_warning("Aucune erreur trouvée dans les logs fournis")
            print_info("Vérifiez que vous avez bien copié les logs avec severityLevel >= 3")
        else:
            print_header("RÉSUMÉ")
            print_error(f"Total: {error_count} erreur(s) trouvée(s)")
            print()
            print_info("Actions recommandées:")
            print("  1. Notez le type d'erreur identifié ci-dessus")
            print("  2. Suivez les solutions suggérées")
            print("  3. Redéployez si nécessaire")
            print("  4. Testez à nouveau")
        
    except json.JSONDecodeError as e:
        print_error(f"Erreur de parsing JSON: {e}")
        print_info("Assurez-vous que les logs sont au format JSON valide")
        return 1
    except Exception as e:
        print_error(f"Erreur: {e}")
        import traceback
        print(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

