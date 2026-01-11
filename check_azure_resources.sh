#!/bin/bash

# Script de diagnostic des ressources Azure

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Charger les variables de déploiement si elles existent
if [ -f .azure_deploy_vars ]; then
    RESOURCE_GROUP=$(sed -n '1p' .azure_deploy_vars)
    LOCATION=$(sed -n '2p' .azure_deploy_vars)
    STORAGE_ACCOUNT=$(sed -n '3p' .azure_deploy_vars)
    FUNCTION_APP=$(sed -n '4p' .azure_deploy_vars)
    
    print_header "RESSOURCES CONFIGURÉES"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Storage Account: $STORAGE_ACCOUNT"
    echo "Function App: $FUNCTION_APP"
    echo ""
else
    print_warning "Aucun fichier .azure_deploy_vars trouvé"
    read -p "Nom du Resource Group à vérifier (défaut: rg-recommender): " RESOURCE_GROUP
    RESOURCE_GROUP=${RESOURCE_GROUP:-rg-recommender}
fi

print_header "VÉRIFICATION DU RESOURCE GROUP"

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_success "Resource Group '$RESOURCE_GROUP' existe"
    az group show --name "$RESOURCE_GROUP" --query "{Name:name, Location:location, ProvisioningState:properties.provisioningState}" -o table
else
    print_error "Resource Group '$RESOURCE_GROUP' n'existe pas"
fi

print_header "VÉRIFICATION DES STORAGE ACCOUNTS"

STORAGE_ACCOUNTS=$(az storage account list --resource-group "$RESOURCE_GROUP" --query "[].{Name:name, Location:location, Status:provisioningState}" -o table 2>/dev/null)

if [ -n "$STORAGE_ACCOUNTS" ] && [ "$STORAGE_ACCOUNTS" != "Name" ]; then
    echo "$STORAGE_ACCOUNTS"
    
    if [ -n "$STORAGE_ACCOUNT" ]; then
        echo ""
        print_info "Vérification du Storage Account spécifique: $STORAGE_ACCOUNT"
        if az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
            print_success "Storage Account '$STORAGE_ACCOUNT' existe"
            
            # Vérifier les conteneurs
            print_info "Conteneurs dans le Storage Account:"
            STORAGE_KEY=$(az storage account keys list \
                --resource-group "$RESOURCE_GROUP" \
                --account-name "$STORAGE_ACCOUNT" \
                --query "[0].value" -o tsv 2>/dev/null)
            
            if [ -n "$STORAGE_KEY" ]; then
                CONTAINERS=$(az storage container list \
                    --account-name "$STORAGE_ACCOUNT" \
                    --account-key "$STORAGE_KEY" \
                    --query "[].name" -o tsv 2>/dev/null)
                
                if [ -n "$CONTAINERS" ]; then
                    echo "$CONTAINERS" | while read container; do
                        print_success "  - $container"
                    done
                else
                    print_warning "  Aucun conteneur trouvé"
                fi
            else
                print_error "  Impossible de récupérer la clé du Storage Account"
            fi
        else
            print_error "Storage Account '$STORAGE_ACCOUNT' n'existe pas"
        fi
    fi
else
    print_warning "Aucun Storage Account trouvé dans le Resource Group"
fi

print_header "VÉRIFICATION DES FUNCTION APPS"

FUNCTION_APPS=$(az functionapp list --resource-group "$RESOURCE_GROUP" --query "[].{Name:name, State:state, Location:location}" -o table 2>/dev/null)

if [ -n "$FUNCTION_APPS" ] && [ "$FUNCTION_APPS" != "Name" ]; then
    echo "$FUNCTION_APPS"
    
    if [ -n "$FUNCTION_APP" ]; then
        echo ""
        print_info "Vérification de la Function App spécifique: $FUNCTION_APP"
        if az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
            print_success "Function App '$FUNCTION_APP' existe"
            STATE=$(az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" --query "state" -o tsv)
            print_info "État: $STATE"
        else
            print_error "Function App '$FUNCTION_APP' n'existe pas"
        fi
    fi
else
    print_warning "Aucune Function App trouvée dans le Resource Group"
fi

print_header "RÉSUMÉ"

echo ""
print_info "Pour nettoyer et recommencer:"
echo "  az group delete --name $RESOURCE_GROUP --yes"
echo ""
print_info "Pour relancer le déploiement:"
echo "  ./deploy_azure.sh"
echo ""
print_info "Pour voir toutes les ressources Azure:"
echo "  az resource list --resource-group $RESOURCE_GROUP --output table"

