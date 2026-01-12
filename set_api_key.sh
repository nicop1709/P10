#!/bin/bash
#
# Script pour configurer la clé d'API Azure Function
#

# Récupérer la clé depuis Azure
echo "🔑 Récupération de la clé d'API depuis Azure..."
FUNCTION_KEY=$(az functionapp keys list --name func-recommender-1768155564 --resource-group rg-recommender --query "functionKeys.default" -o tsv 2>/dev/null)

if [ -z "$FUNCTION_KEY" ]; then
    echo "❌ Impossible de récupérer la clé depuis Azure"
    echo "ℹ️  Veuillez définir manuellement la variable d'environnement:"
    echo "   export AZURE_FUNCTION_KEY='votre_cle_azure_function'"
    echo ""
    echo "💡 Pour obtenir la clé depuis Azure:"
    echo "   az functionapp keys list --name func-recommender-1768155564 --resource-group rg-recommender --query 'functionKeys.default' -o tsv"
    exit 1
fi

# Exporter la clé
export AZURE_FUNCTION_KEY="$FUNCTION_KEY"

echo "✅ Clé d'API configurée!"
echo "ℹ️  Variable d'environnement: AZURE_FUNCTION_KEY"
echo ""
echo "💡 Pour utiliser dans votre shell actuel, exécutez:"
echo "   source ./set_api_key.sh"
echo ""
echo "🧪 Pour tester:"
echo "   python3 test_function.py 0"
