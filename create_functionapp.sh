#!/bin/bash

# Script rapide pour créer la Function App avec Python 3.11

set -e
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

# Charger les variables depuis .azure_deploy_vars si disponible
if [ -f .azure_deploy_vars ]; then
    RESOURCE_GROUP=$(sed -n '1p' .azure_deploy_vars)
    LOCATION=$(sed -n '2p' .azure_deploy_vars)
    STORAGE_ACCOUNT=$(sed -n '3p' .azure_deploy_vars)
    FUNCTION_APP=$(sed -n '4p' .azure_deploy_vars)
    
    print_info "Variables chargées depuis .azure_deploy_vars"
    print_info "Resource Group: $RESOURCE_GROUP"
    print_info "Location: $LOCATION"
    print_info "Storage Account: $STORAGE_ACCOUNT"
    print_info "Function App: $FUNCTION_APP"
else
    print_warning "Fichier .azure_deploy_vars non trouvé"
    read -p "Resource Group (défaut: rg-recommender): " RESOURCE_GROUP
    RESOURCE_GROUP=${RESOURCE_GROUP:-rg-recommender}
    
    read -p "Location (défaut: westeurope): " LOCATION
    LOCATION=${LOCATION:-westeurope}
    
    read -p "Storage Account: " STORAGE_ACCOUNT
    if [ -z "$STORAGE_ACCOUNT" ]; then
        print_error "Storage Account requis"
        exit 1
    fi
    
    TIMESTAMP=$(date +%s)
    FUNCTION_APP="func-recommender-${TIMESTAMP}"
    print_info "Function App généré: $FUNCTION_APP"
fi

# Vérifier si la Function App existe déjà
if az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Function App '$FUNCTION_APP' existe déjà"
    read -p "Voulez-vous la supprimer et la recréer? (o/n): " delete_existing
    if [[ $delete_existing =~ ^[Oo]$ ]]; then
        print_info "Suppression de la Function App existante..."
        az functionapp delete --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" --yes
        sleep 10
    else
        print_info "Utilisation de la Function App existante"
        exit 0
    fi
fi

# Essayer les versions Python supportées
PYTHON_VERSIONS=("3.11" "3.12" "3.10")
FUNCTION_CREATED=false

for PYTHON_VERSION in "${PYTHON_VERSIONS[@]}"; do
    print_info "Tentative de création avec Python $PYTHON_VERSION..."
    
    if az functionapp create \
        --resource-group "$RESOURCE_GROUP" \
        --consumption-plan-location "$LOCATION" \
        --runtime python \
        --runtime-version "$PYTHON_VERSION" \
        --functions-version 4 \
        --name "$FUNCTION_APP" \
        --storage-account "$STORAGE_ACCOUNT" \
        --os-type Linux 2>&1; then
        
        # Attendre un peu pour que la création soit propagée
        sleep 5
        
        # Vérifier que la Function App existe vraiment
        if az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
            print_success "Function App créée avec Python $PYTHON_VERSION"
            FUNCTION_CREATED=true
            break
        else
            print_warning "Function App créée mais pas encore disponible, attente..."
            sleep 10
            if az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
                print_success "Function App créée avec Python $PYTHON_VERSION"
                FUNCTION_CREATED=true
                break
            fi
        fi
    else
        print_warning "Échec avec Python $PYTHON_VERSION, essai avec une autre version..."
        continue
    fi
done

if [ "$FUNCTION_CREATED" = false ]; then
    print_error "Impossible de créer la Function App"
    print_info "Vérifiez les runtimes disponibles:"
    echo "  az functionapp list-runtimes --os-type Linux --query \"[?contains(name, 'python')]\" -o table"
    exit 1
fi

# Vérification finale
print_info "Vérification de la Function App..."
FUNC_INFO=$(az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" --query "{Name:name, State:state, PythonVersion:siteConfig.linuxFxVersion, OS:kind}" -o table)
echo "$FUNC_INFO"

# Mettre à jour .azure_deploy_vars si nécessaire
if [ -f .azure_deploy_vars ]; then
    # Mettre à jour la ligne 4 (Function App)
    sed -i '' "4s/.*/$FUNCTION_APP/" .azure_deploy_vars 2>/dev/null || sed -i "4s/.*/$FUNCTION_APP/" .azure_deploy_vars
    print_success "Fichier .azure_deploy_vars mis à jour"
fi

print_success "Function App prête!"
print_info "Vous pouvez maintenant continuer avec l'étape 3 (Configurer la connexion Storage)"

