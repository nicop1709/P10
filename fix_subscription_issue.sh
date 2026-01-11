#!/bin/bash

# Script de correction pour les problèmes d'abonnement Azure
# Résout l'erreur "SubscriptionNotFound"

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step "CORRECTION DU PROBLÈME D'ABONNEMENT AZURE"

# Vérifier la connexion
print_info "Vérification de la connexion Azure..."
if ! az account show &> /dev/null; then
    print_warning "Vous n'êtes pas connecté à Azure"
    print_info "Connexion à Azure..."
    az login
fi

# Afficher l'abonnement actuel
print_step "ABONNEMENT ACTUEL"
CURRENT_SUB=$(az account show --query "{Name:name, State:state, SubscriptionId:id}" -o table 2>/dev/null || echo "")
if [ -z "$CURRENT_SUB" ]; then
    print_error "Impossible de récupérer les informations de l'abonnement"
    exit 1
fi
echo "$CURRENT_SUB"

# Vérifier l'état
SUBSCRIPTION_STATE=$(az account show --query state -o tsv 2>/dev/null || echo "Unknown")
SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null || echo "")

if [ "$SUBSCRIPTION_STATE" != "Enabled" ]; then
    print_error "L'abonnement n'est pas dans l'état 'Enabled' (état: $SUBSCRIPTION_STATE)"
    echo ""
    print_info "Solutions:"
    echo "  1. Allez sur https://portal.azure.com"
    echo "  2. Vérifiez l'état de votre abonnement"
    echo "  3. Réactivez l'abonnement si nécessaire"
    echo "  4. Consultez RESOLUTION_RAPIDE.md pour plus de détails"
    exit 1
fi

print_success "Abonnement actif (état: $SUBSCRIPTION_STATE)"

# Lister tous les abonnements disponibles
print_step "ABONNEMENTS DISPONIBLES"
ALL_SUBS=$(az account list --output table 2>/dev/null || echo "")
if [ -z "$ALL_SUBS" ]; then
    print_error "Aucun abonnement trouvé"
    print_info "Vous devez créer un compte Azure gratuit: https://azure.microsoft.com/free/"
    exit 1
fi
echo "$ALL_SUBS"

# Vérifier si le Resource Group existe et dans quel abonnement
print_step "VÉRIFICATION DU RESOURCE GROUP"
RESOURCE_GROUP="rg-recommender"

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Resource Group '$RESOURCE_GROUP' existe déjà"
    
    # Récupérer l'ID de l'abonnement du Resource Group
    RG_SUB_ID=$(az group show --name "$RESOURCE_GROUP" --query id -o tsv 2>/dev/null | cut -d'/' -f3 || echo "")
    
    if [ -n "$RG_SUB_ID" ] && [ "$RG_SUB_ID" != "$SUBSCRIPTION_ID" ]; then
        print_warning "Le Resource Group a été créé avec un autre abonnement!"
        print_info "Resource Group Subscription: $RG_SUB_ID"
        print_info "Abonnement actuel: $SUBSCRIPTION_ID"
        echo ""
        print_info "Options:"
        echo "  1. Supprimer le Resource Group et recommencer"
        echo "  2. Changer d'abonnement pour correspondre au Resource Group"
        echo ""
        read -p "Voulez-vous supprimer le Resource Group et recommencer? (o/n): " delete_rg
        if [[ $delete_rg =~ ^[Oo]$ ]]; then
            print_info "Suppression du Resource Group..."
            az group delete --name "$RESOURCE_GROUP" --yes --no-wait
            print_success "Resource Group en cours de suppression"
            print_info "Attendez 30-60 secondes avant de relancer le déploiement"
        else
            print_info "Changement d'abonnement..."
            az account set --subscription "$RG_SUB_ID"
            print_success "Abonnement changé"
            print_info "Vérifiez l'état: az account show --query state -o tsv"
        fi
    else
        print_success "Le Resource Group est dans le bon abonnement"
    fi
else
    print_info "Resource Group '$RESOURCE_GROUP' n'existe pas (c'est normal si c'est un nouveau déploiement)"
fi

# Vérifier les permissions
print_step "VÉRIFICATION DES PERMISSIONS"
USER_NAME=$(az account show --query user.name -o tsv 2>/dev/null || echo "")
if [ -n "$USER_NAME" ]; then
    print_info "Utilisateur: $USER_NAME"
    ROLES=$(az role assignment list --assignee "$USER_NAME" --scope "/subscriptions/$SUBSCRIPTION_ID" --query "[].roleDefinitionName" -o tsv 2>/dev/null || echo "")
    if [ -z "$ROLES" ]; then
        print_warning "Aucun rôle trouvé pour cet utilisateur"
        print_info "Vous devez avoir au moins le rôle 'Contributor' ou 'Owner'"
    else
        print_success "Rôles trouvés:"
        echo "$ROLES" | while read role; do
            echo "  - $role"
        done
    fi
fi

# Test de création d'une ressource simple
print_step "TEST DE CRÉATION DE RESSOURCE"
print_info "Test de création d'un groupe de ressources de test..."
TEST_RG="rg-test-$(date +%s)"
if az group create --name "$TEST_RG" --location "westeurope" &> /dev/null; then
    print_success "Test réussi: création de ressource possible"
    print_info "Suppression du groupe de test..."
    az group delete --name "$TEST_RG" --yes --no-wait &> /dev/null
else
    print_error "Test échoué: impossible de créer une ressource"
    print_info "Vérifiez vos permissions et l'état de l'abonnement"
    exit 1
fi

# Résumé
print_step "RÉSUMÉ"
print_success "L'abonnement semble correctement configuré"
echo ""
print_info "Prochaines étapes:"
echo "  1. Relancez le déploiement: ./deploy_azure.sh"
echo "  2. Si le problème persiste, consultez TROUBLESHOOTING_AZURE.md"
echo ""

