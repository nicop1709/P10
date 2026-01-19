#!/bin/bash
set -euo pipefail

# Lancer l'app Streamlit depuis ce repertoire
SCRIPT_DIR="$(cd -- "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Charger les variables d'environnement depuis .env si present
if [ -f ".env" ]; then
  set -a
  source ./.env
  set +a
fi

# Verification de la cle API
if [ -z "${FUNCTION_KEY:-}" ]; then
  echo "ERREUR: variable FUNCTION_KEY absente."
  echo "  - Copiez .env.example en .env et renseignez FUNCTION_KEY"
  echo "  - ou exportez FUNCTION_KEY dans votre shell"
  exit 1
fi

# Verifier Streamlit
if ! command -v streamlit >/dev/null 2>&1; then
  echo "ERREUR: Streamlit n'est pas installe."
  echo "  Installez les dependances: pip install -r requirements.txt"
  exit 1
fi

# Demarrer l'app
exec streamlit run app.py
