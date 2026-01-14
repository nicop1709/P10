#!/bin/bash
#
# Script pour lancer l'application Streamlit
#

echo ""
echo "============================================================"
echo "  LANCEMENT DE L'APPLICATION STREAMLIT"
echo "============================================================"
echo ""

# Vérifier que streamlit est installé
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit n'est pas installé."
    echo "ℹ️  Installation avec: pip install streamlit requests"
    echo ""
    read -p "Voulez-vous installer les dépendances maintenant? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install streamlit requests
    else
        exit 1
    fi
fi

# Vérifier si la clé API est déjà définie
if [ -z "$AZURE_FUNCTION_KEY" ]; then
    echo "🔑 Clé API non trouvée, tentative de récupération..."
    
    # Essayer de récupérer la clé depuis Azure
    if command -v az &> /dev/null; then
        FUNCTION_KEY=$(az functionapp keys list --name func-recommender-1768155564 --resource-group rg-recommender --query "functionKeys.default" -o tsv 2>/dev/null)
        
        if [ -n "$FUNCTION_KEY" ]; then
            export AZURE_FUNCTION_KEY="$FUNCTION_KEY"
            echo "✅ Clé API récupérée depuis Azure"
        else
            echo "⚠️  Impossible de récupérer la clé depuis Azure"
            echo "ℹ️  Vous pouvez:"
            echo "   1. Exécuter: source ./set_api_key.sh"
            echo "   2. Ou définir manuellement: export AZURE_FUNCTION_KEY='votre_cle'"
            echo ""
            read -p "Continuer quand même? (y/n) " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        echo "⚠️  Azure CLI non installé, impossible de récupérer la clé automatiquement"
        echo "ℹ️  Définissez la clé manuellement:"
        echo "   export AZURE_FUNCTION_KEY='votre_cle'"
        echo "   ou exécutez: source ./set_api_key.sh"
        echo ""
        read -p "Continuer quand même? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "✅ Clé API déjà configurée"
fi

echo ""
echo "ℹ️  L'application va démarrer dans votre navigateur..."
echo "ℹ️  URL: http://localhost:8501"
echo ""
echo "💡 Pour arrêter l'application: Ctrl+C"
echo ""

# Lancer Streamlit
streamlit run app.py
