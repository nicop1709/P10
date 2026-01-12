#!/bin/bash
#
# Script pour configurer automatiquement les secrets GitHub
# pour le déploiement CI/CD
#

set -e

echo ""
echo "============================================================"
echo "  CONFIGURATION DES SECRETS GITHUB POUR CI/CD"
echo "============================================================"
echo ""

# Variables
FUNCTION_APP="func-recommender-1768155564"
RESOURCE_GROUP="rg-recommender"
GITHUB_REPO="" # À remplir: username/repo

# Vérifier que gh CLI est installé
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) n'est pas installé."
    echo "ℹ️  Installation: https://cli.github.com/"
    echo ""
    echo "   macOS:   brew install gh"
    echo "   Linux:   https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo "   Windows: https://github.com/cli/cli/releases"
    exit 1
fi

# Vérifier que az CLI est installé
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI (az) n'est pas installé."
    echo "ℹ️  Installation: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Demander le nom du repository si non défini
if [ -z "$GITHUB_REPO" ]; then
    echo "ℹ️  Entrez le nom de votre repository GitHub (format: username/repo):"
    read -r GITHUB_REPO
fi

# Vérifier que l'utilisateur est connecté à GitHub
echo "🔐 Vérification de l'authentification GitHub..."
if ! gh auth status &> /dev/null; then
    echo "ℹ️  Vous devez vous connecter à GitHub:"
    gh auth login
fi

echo "✅ Authentification GitHub réussie"
echo ""

# Vérifier que l'utilisateur est connecté à Azure
echo "🔐 Vérification de l'authentification Azure..."
if ! az account show &> /dev/null; then
    echo "ℹ️  Vous devez vous connecter à Azure:"
    az login
fi

echo "✅ Authentification Azure réussie"
echo ""

# Récupérer le Publish Profile
echo "📥 Récupération du Publish Profile depuis Azure..."
PUBLISH_PROFILE=$(az functionapp deployment list-publishing-profiles \
    --name "$FUNCTION_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --xml 2>/dev/null)

if [ -z "$PUBLISH_PROFILE" ]; then
    echo "❌ Impossible de récupérer le Publish Profile"
    exit 1
fi

echo "✅ Publish Profile récupéré"

# Ajouter le secret dans GitHub
echo "🔑 Ajout du secret AZURE_FUNCTIONAPP_PUBLISH_PROFILE dans GitHub..."
echo "$PUBLISH_PROFILE" | gh secret set AZURE_FUNCTIONAPP_PUBLISH_PROFILE \
    --repo "$GITHUB_REPO"

if [ $? -eq 0 ]; then
    echo "✅ Secret AZURE_FUNCTIONAPP_PUBLISH_PROFILE ajouté avec succès"
else
    echo "❌ Erreur lors de l'ajout du secret"
    exit 1
fi

# Récupérer et ajouter la Function Key (optionnel, pour tests)
echo ""
echo "📥 Récupération de la Function Key (pour tests automatiques)..."
FUNCTION_KEY=$(az functionapp keys list \
    --name "$FUNCTION_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "functionKeys.default" -o tsv 2>/dev/null)

if [ -n "$FUNCTION_KEY" ]; then
    echo "🔑 Ajout du secret AZURE_FUNCTION_KEY dans GitHub..."
    echo "$FUNCTION_KEY" | gh secret set AZURE_FUNCTION_KEY \
        --repo "$GITHUB_REPO"

    if [ $? -eq 0 ]; then
        echo "✅ Secret AZURE_FUNCTION_KEY ajouté avec succès"
    else
        echo "⚠️  Erreur lors de l'ajout du secret AZURE_FUNCTION_KEY (optionnel)"
    fi
else
    echo "⚠️  Impossible de récupérer la Function Key (optionnel)"
fi

echo ""
echo "============================================================"
echo "  CONFIGURATION TERMINÉE"
echo "============================================================"
echo ""
echo "✅ Les secrets GitHub ont été configurés avec succès!"
echo ""
echo "ℹ️  Prochaines étapes:"
echo "   1. Commitez et pushez le workflow:"
echo "      git add .github/workflows/azure-function-deploy.yml"
echo "      git commit -m 'Add CI/CD workflow for Azure Function'"
echo "      git push origin main"
echo ""
echo "   2. Vérifiez le déploiement dans GitHub Actions:"
echo "      https://github.com/$GITHUB_REPO/actions"
echo ""
echo "   3. Les prochains pushs déclencheront automatiquement le déploiement!"
echo ""
