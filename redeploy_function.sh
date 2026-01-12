#!/bin/bash
# Script pour redéployer rapidement la fonction Azure après des modifications de code

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

# Vérifier que le fichier de variables existe
if [ ! -f .azure_deploy_vars ]; then
    print_error "Fichier .azure_deploy_vars non trouvé"
    print_info "Exécutez d'abord deploy_azure.sh (étape 1)"
    exit 1
fi

# Charger les variables
FUNCTION_APP=$(sed -n '4p' .azure_deploy_vars)
RESOURCE_GROUP=$(sed -n '1p' .azure_deploy_vars)

if [ -z "$FUNCTION_APP" ] || [ -z "$RESOURCE_GROUP" ]; then
    print_error "Impossible de charger les variables de déploiement"
    exit 1
fi

print_header "REDÉPLOIEMENT DE LA FONCTION AZURE"
print_info "Function App: $FUNCTION_APP"
print_info "Resource Group: $RESOURCE_GROUP"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "azure_function" ]; then
    print_error "Le dossier azure_function n'existe pas"
    exit 1
fi

# Vérifier que func est installé
if ! command -v func &> /dev/null; then
    print_error "Azure Functions Core Tools (func) n'est pas installé"
    print_info "Installez-le avec: npm install -g azure-functions-core-tools@4"
    exit 1
fi

print_info "Déploiement de la fonction..."
cd azure_function

# Déployer
if func azure functionapp publish "$FUNCTION_APP"; then
    print_success "Déploiement réussi!"
else
    print_error "Erreur lors du déploiement"
    cd ..
    exit 1
fi

cd ..

print_info "Attente de 10 secondes pour que le déploiement se stabilise..."
sleep 10

print_info "Redémarrage de la Function App pour s'assurer que le nouveau code est chargé..."
if az functionapp restart --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" 2>&1; then
    print_success "Function App redémarrée"
else
    print_warning "Impossible de redémarrer la Function App (peut-être déjà en cours)"
fi

print_header "REDÉPLOIEMENT TERMINÉ"
print_success "La fonction a été redéployée avec succès!"
print_info "Vous pouvez maintenant tester avec: python test_function.py 0"
print_info "Pour voir les logs: func azure functionapp logstream $FUNCTION_APP --browser"

