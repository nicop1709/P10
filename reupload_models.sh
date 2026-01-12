#!/bin/bash
# Script pour ré-uploader les fichiers pickle en mode binaire

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Charger les variables
if [ ! -f .azure_deploy_vars ]; then
    print_error "Fichier .azure_deploy_vars non trouvé"
    exit 1
fi

STORAGE_ACCOUNT=$(sed -n '3p' .azure_deploy_vars)
RESOURCE_GROUP=$(sed -n '1p' .azure_deploy_vars)

if [ -z "$STORAGE_ACCOUNT" ] || [ -z "$RESOURCE_GROUP" ]; then
    print_error "Impossible de charger les variables de déploiement"
    exit 1
fi

print_header "RÉ-UPLOAD DES FICHIERS PICKLE EN MODE BINAIRE"

print_info "Storage Account: $STORAGE_ACCOUNT"
print_info "Resource Group: $RESOURCE_GROUP"
print_info "Conteneur: models"
echo

# Vérifier que les fichiers existent
FILES="als_model.pkl metadata.pkl csr_train.pkl"
MISSING_FILES=""

for file in $FILES; do
    if [ ! -f "$file" ]; then
        MISSING_FILES="$MISSING_FILES $file"
    fi
done

if [ -n "$MISSING_FILES" ]; then
    print_error "Fichiers manquants:"
    for file in $MISSING_FILES; do
        echo "  - $file"
    done
    exit 1
fi

# Récupérer la clé de stockage
print_info "Récupération de la clé de stockage..."
STORAGE_KEY=$(az storage account keys list \
    --account-name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --query '[0].value' \
    --output tsv)

if [ -z "$STORAGE_KEY" ]; then
    print_error "Impossible de récupérer la clé de stockage"
    exit 1
fi

print_success "Clé de stockage récupérée"
echo

# Uploader chaque fichier en mode binaire
for file in $FILES; do
    print_info "Upload de $file..."
    
    # Obtenir la taille du fichier
    FILE_SIZE=$(ls -lh "$file" | awk '{print $5}')
    print_info "Taille: $FILE_SIZE"
    
    if az storage blob upload \
        --container-name "models" \
        --name "$file" \
        --file "$file" \
        --account-name "$STORAGE_ACCOUNT" \
        --account-key "$STORAGE_KEY" \
        --content-type "application/octet-stream" \
        --overwrite 2>&1; then
        print_success "$file uploadé avec succès"
    else
        print_error "Erreur lors de l'upload de $file"
        exit 1
    fi
    echo
done

print_header "RÉ-UPLOAD TERMINÉ"
print_success "Tous les fichiers ont été ré-uploadés en mode binaire!"
echo
print_info "Prochaines étapes:"
echo "  1. Redémarrer la Function App:"
echo "     az functionapp restart --name func-recommender-1768155564 --resource-group $RESOURCE_GROUP"
echo
echo "  2. Tester la fonction:"
echo "     python3 test_and_analyze.py 0"
echo

