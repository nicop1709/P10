#!/bin/bash
#
# Script pour configurer l'authentification Azure via Service Principal
# Plus fiable que le Publish Profile pour CI/CD
#

set -e

echo ""
echo "============================================================"
echo "  CONFIGURATION AZURE SERVICE PRINCIPAL POUR CI/CD"
echo "============================================================"
echo ""

# Variables
FUNCTION_APP="func-recommender-1768155564"
RESOURCE_GROUP="rg-recommender"
GITHUB_REPO="" # À remplir: username/repo
SUBSCRIPTION_ID=""

# Vérifier que gh CLI est installé
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) n'est pas installé."
    echo "ℹ️  Installation: https://cli.github.com/"
    exit 1
fi

# Vérifier que az CLI est installé
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI (az) n'est pas installé."
    exit 1
fi

# Demander le nom du repository si non défini
if [ -z "$GITHUB_REPO" ]; then
    echo "ℹ️  Entrez le nom de votre repository GitHub (format: username/repo):"
    read -r GITHUB_REPO
fi

# Vérifier authentification GitHub
echo "🔐 Vérification de l'authentification GitHub..."
if ! gh auth status &> /dev/null; then
    echo "ℹ️  Vous devez vous connecter à GitHub:"
    gh auth login
fi
echo "✅ Authentification GitHub réussie"
echo ""

# Vérifier authentification Azure
echo "🔐 Vérification de l'authentification Azure..."
if ! az account show &> /dev/null; then
    echo "ℹ️  Vous devez vous connecter à Azure:"
    az login
fi
echo "✅ Authentification Azure réussie"
echo ""

# Récupérer l'ID de la subscription
SUBSCRIPTION_ID=$(az account show --query "id" -o tsv)
echo "📋 Subscription ID: $SUBSCRIPTION_ID"
echo ""

# Récupérer l'ID du Resource Group
RESOURCE_GROUP_ID=$(az group show --name "$RESOURCE_GROUP" --query "id" -o tsv)
echo "📋 Resource Group ID: $RESOURCE_GROUP_ID"
echo ""

# Créer un Service Principal avec les droits sur le Resource Group
echo "🔑 Création du Service Principal pour le déploiement..."
SP_NAME="sp-github-actions-$FUNCTION_APP"

# Supprimer l'ancien service principal s'il existe
az ad sp list --display-name "$SP_NAME" --query "[].appId" -o tsv | while read -r app_id; do
    echo "🗑️  Suppression de l'ancien Service Principal..."
    az ad sp delete --id "$app_id" || true
done

# Créer le nouveau service principal avec le rôle Contributor sur le Resource Group
CREDENTIALS=$(az ad sp create-for-rbac \
    --name "$SP_NAME" \
    --role Contributor \
    --scopes "$RESOURCE_GROUP_ID" \
    --sdk-auth 2>/dev/null)

if [ -z "$CREDENTIALS" ]; then
    echo "❌ Impossible de créer le Service Principal"
    exit 1
fi

echo "✅ Service Principal créé avec succès"
echo ""

# Ajouter le secret AZURE_CREDENTIALS dans GitHub
echo "🔑 Ajout du secret AZURE_CREDENTIALS dans GitHub..."
echo "$CREDENTIALS" | gh secret set AZURE_CREDENTIALS --repo "$GITHUB_REPO"

if [ $? -eq 0 ]; then
    echo "✅ Secret AZURE_CREDENTIALS ajouté avec succès"
else
    echo "❌ Erreur lors de l'ajout du secret"
    exit 1
fi
echo ""

# Récupérer et ajouter la Function Key (optionnel, pour tests)
echo "📥 Récupération de la Function Key (pour tests automatiques)..."
FUNCTION_KEY=$(az functionapp keys list \
    --name "$FUNCTION_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "functionKeys.default" -o tsv 2>/dev/null)

if [ -n "$FUNCTION_KEY" ]; then
    echo "🔑 Ajout du secret AZURE_FUNCTION_KEY dans GitHub..."
    echo "$FUNCTION_KEY" | gh secret set AZURE_FUNCTION_KEY --repo "$GITHUB_REPO"

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
echo "ℹ️  Service Principal créé:"
echo "   Nom: $SP_NAME"
echo "   Scope: $RESOURCE_GROUP"
echo "   Rôle: Contributor"
echo ""
echo "ℹ️  Prochaines étapes:"
echo "   1. Le workflow a été mis à jour pour utiliser Azure CLI"
echo "   2. Commitez et pushez les changements:"
echo "      git add .github/workflows/"
echo "      git commit -m 'Update CI/CD to use Service Principal auth'"
echo "      git push origin main"
echo ""
echo "   3. Le déploiement se fera automatiquement!"
echo ""
