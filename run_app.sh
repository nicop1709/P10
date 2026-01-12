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

echo "ℹ️  L'application va démarrer dans votre navigateur..."
echo "ℹ️  URL: http://localhost:8501"
echo ""
echo "💡 Pour arrêter l'application: Ctrl+C"
echo ""

# Lancer Streamlit
streamlit run app.py
